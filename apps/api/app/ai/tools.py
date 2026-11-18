"""
Server-side typed read-only financial tools for QuantWeave Copilot.

Enforces:
- Strict authorization: user-specific tools inject authenticated user_id server-side
- Zero mutations: strictly read-only computations and queries
- Structured metadata: value, unit, observation date, data freshness, synthetic/demo status
- Resilient error handling: returns structured diagnostic payloads rather than raising unhandled exceptions
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.comparison import compare_equities as analytics_compare_equities
from app.analytics.fund_analytics import FundAnalyticsService
from app.analytics.fund_comparison import compare_mutual_funds as analytics_compare_funds
from app.analytics.fundamentals import calculate_statement_ratios
from app.analytics.portfolio_analytics import PortfolioAnalyticsService
from app.analytics.technical import calculate_all_technicals
from app.models.instrument import Instrument
from app.models.market import (
    ArticleInstrumentLink,
    MacroEconomicObservation,
    MacroEconomicSeries,
    NewsArticle,
    NewsSentiment,
)
from app.models.mutual_fund import FundNAVHistory, MutualFund
from app.models.portfolio import Portfolio
from app.models.price_history import PriceHistory
from app.models.quantlab import BacktestRun, BacktestTrade, ResearchStrategy
from app.services.portfolio import PortfolioService


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_instrument(db: Session, identifier: str) -> Optional[Instrument]:
    """Helper to locate instrument by UUID or ticker symbol."""
    try:
        u = uuid.UUID(identifier)
        inst = db.query(Instrument).filter(Instrument.id == u).first()
        if inst:
            return inst
    except ValueError:
        pass
    clean_sym = identifier.strip().upper()
    return db.query(Instrument).filter(Instrument.symbol == clean_sym).first()


def _resolve_fund(db: Session, identifier: str) -> Optional[MutualFund]:
    """Helper to locate mutual fund by UUID or scheme code."""
    try:
        u = uuid.UUID(identifier)
        fund = db.query(MutualFund).filter(MutualFund.id == u).first()
        if fund:
            return fund
    except ValueError:
        pass
    clean_id = identifier.strip()
    return db.query(MutualFund).filter(
        or_(MutualFund.scheme_code == clean_id, MutualFund.scheme_name.ilike(f"%{clean_id}%"))
    ).first()


# ==========================================
# 1. Equity Intelligence Tools
# ==========================================

def tool_search_instruments(db: Session, context_user_id: uuid.UUID, query: str, limit: int = 10) -> Dict[str, Any]:
    """Searches NSE/BSE equity instruments by symbol or company name."""
    clean_q = query.strip()
    records = (
        db.query(Instrument)
        .filter(or_(Instrument.symbol.ilike(f"%{clean_q}%"), Instrument.company_name.ilike(f"%{clean_q}%")))
        .limit(min(limit, 25))
        .all()
    )
    return {
        "tool": "search_instruments",
        "status": "success",
        "query": clean_q,
        "count": len(records),
        "instruments": [
            {
                "id": str(i.id),
                "symbol": i.symbol,
                "company_name": i.company_name,
                "exchange": i.exchange,
                "sector": i.sector,
                "currency": i.currency,
                "is_demo": i.is_demo,
            }
            for i in records
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_instrument_profile(db: Session, context_user_id: uuid.UUID, symbol_or_id: str) -> Dict[str, Any]:
    """Retrieves full profile metadata and latest closing price for a stock."""
    inst = _resolve_instrument(db, symbol_or_id)
    if not inst:
        return {"tool": "get_instrument_profile", "status": "not_found", "message": f"Instrument '{symbol_or_id}' not found."}

    latest_bar = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.desc())
        .first()
    )

    return {
        "tool": "get_instrument_profile",
        "status": "success",
        "id": str(inst.id),
        "symbol": inst.symbol,
        "company_name": inst.company_name,
        "exchange": inst.exchange,
        "sector": inst.sector,
        "industry": inst.industry,
        "currency": inst.currency,
        "is_demo": inst.is_demo,
        "latest_price": float(latest_bar.close) if latest_bar else None,
        "latest_trade_date": str(latest_bar.trade_date) if latest_bar else None,
        "retrieved_at": _iso_now(),
    }


def tool_get_price_history(
    db: Session, context_user_id: uuid.UUID, symbol_or_id: str, limit: int = 30
) -> Dict[str, Any]:
    """Retrieves recent daily OHLCV trading bars for a stock."""
    inst = _resolve_instrument(db, symbol_or_id)
    if not inst:
        return {"tool": "get_price_history", "status": "not_found", "message": f"Instrument '{symbol_or_id}' not found."}

    bars = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.desc())
        .limit(min(limit, 100))
        .all()
    )
    bars = list(reversed(bars))  # chronological

    return {
        "tool": "get_price_history",
        "status": "success",
        "symbol": inst.symbol,
        "company_name": inst.company_name,
        "count": len(bars),
        "bars": [
            {
                "date": str(b.trade_date),
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": b.volume,
            }
            for b in bars
        ],
        "is_demo": inst.is_demo,
        "retrieved_at": _iso_now(),
    }


def tool_get_technical_indicators(db: Session, context_user_id: uuid.UUID, symbol_or_id: str) -> Dict[str, Any]:
    """Calculates SMA, EMA, RSI (Wilder's), MACD, and Bollinger Bands using deterministic analytics."""
    inst = _resolve_instrument(db, symbol_or_id)
    if not inst:
        return {"tool": "get_technical_indicators", "status": "not_found", "message": f"Instrument '{symbol_or_id}' not found."}

    price_records = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.asc())
        .all()
    )

    try:
        points, summary = calculate_all_technicals(price_records)
        latest_date = price_records[-1].trade_date.isoformat() if price_records else "N/A"
        latest_pt = points[-1] if points else None
    except Exception as e:
        return {"tool": "get_technical_indicators", "status": "error", "message": str(e)}

    return {
        "tool": "get_technical_indicators",
        "status": "success",
        "symbol": inst.symbol,
        "as_of": str(latest_date),
        "summary": {
            "sma_20": latest_pt.sma_20 if latest_pt else None,
            "sma_50": latest_pt.sma_50 if latest_pt else None,
            "sma_200": latest_pt.sma_200 if latest_pt else None,
            "ema_12": latest_pt.ema_12 if latest_pt else None,
            "ema_26": latest_pt.ema_26 if latest_pt else None,
            "rsi_14": summary.rsi_value,
            "macd": latest_pt.macd_line if latest_pt else None,
            "macd_signal": latest_pt.macd_signal if latest_pt else None,
            "macd_histogram": summary.macd_histogram,
            "bollinger_upper": latest_pt.bb_upper if latest_pt else None,
            "bollinger_middle": latest_pt.bb_middle if latest_pt else None,
            "bollinger_lower": latest_pt.bb_lower if latest_pt else None,
        },
        "is_demo": inst.is_demo,
        "is_synthetic": inst.is_demo,
        "retrieved_at": _iso_now(),
    }


def tool_get_fundamental_ratios(db: Session, context_user_id: uuid.UUID, symbol_or_id: str) -> Dict[str, Any]:
    """Retrieves validated fundamental valuation and profitability ratios (P/E, P/B, ROE, Debt/Equity)."""
    inst = _resolve_instrument(db, symbol_or_id)
    if not inst:
        return {"tool": "get_fundamental_ratios", "status": "not_found", "message": f"Instrument '{symbol_or_id}' not found."}

    try:
        ratios_resp = calculate_statement_ratios(db=db, instrument_id=inst.id)
    except Exception as e:
        return {"tool": "get_fundamental_ratios", "status": "error", "message": str(e)}

    r = ratios_resp.ratios
    return {
        "tool": "get_fundamental_ratios",
        "status": "success",
        "symbol": inst.symbol,
        "as_of": str(ratios_resp.as_of),
        "ratios": {
            "pe_ratio": r.pe_ratio,
            "pb_ratio": r.pb_ratio,
            "roe_pct": r.roe_pct,
            "debt_to_equity": r.debt_to_equity,
            "net_margin_pct": r.net_margin_pct,
            "earnings_per_share": r.earnings_per_share,
            "book_value_per_share": r.book_value_per_share,
        },
        "is_demo": inst.is_demo,
        "retrieved_at": _iso_now(),
    }


def tool_compare_equities(
    db: Session, context_user_id: uuid.UUID, symbols_or_ids: List[str], period: str = "1Y"
) -> Dict[str, Any]:
    """Compares 2 to 4 equity instruments on return, annualized volatility, drawdown, and indicators."""
    resolved_ids = []
    for item in symbols_or_ids[:4]:
        inst = _resolve_instrument(db, item)
        if inst:
            resolved_ids.append(inst.id)

    if len(resolved_ids) < 1:
        return {"tool": "compare_equities", "status": "error", "message": "At least one valid instrument required."}

    try:
        comp_res = analytics_compare_equities(db=db, instrument_ids=resolved_ids, period=period)
    except Exception as e:
        return {"tool": "compare_equities", "status": "error", "message": str(e)}

    return {
        "tool": "compare_equities",
        "status": "success",
        "period": comp_res.period,
        "start_date": str(comp_res.start_date),
        "end_date": str(comp_res.end_date),
        "instruments": [
            {
                "symbol": m.symbol,
                "company_name": m.company_name,
                "latest_price": m.latest_price,
                "period_return_pct": m.period_return_pct,
                "annualized_volatility_pct": m.annualized_volatility_pct,
                "max_drawdown_pct": m.max_drawdown_pct,
                "rsi_14": m.rsi_14,
                "pe_ratio": m.pe_ratio,
            }
            for m in comp_res.instruments
        ],
        "retrieved_at": _iso_now(),
    }


# ==========================================
# 2. Portfolio Intelligence Tools (Authenticated)
# ==========================================

def tool_list_user_portfolios(db: Session, context_user_id: uuid.UUID) -> Dict[str, Any]:
    """Lists portfolios owned strictly by the authenticated user."""
    ports = PortfolioService.get_user_portfolios(db, context_user_id)
    return {
        "tool": "list_user_portfolios",
        "status": "success",
        "count": len(ports),
        "portfolios": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "base_currency": p.base_currency,
                "created_at": p.created_at.isoformat(),
            }
            for p in ports
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_portfolio_valuation(db: Session, context_user_id: uuid.UUID, portfolio_id: str) -> Dict[str, Any]:
    """Retrieves current market valuation, cash balance, invested capital, and total P&L for user's portfolio."""
    try:
        pid = uuid.UUID(portfolio_id)
    except ValueError:
        return {"tool": "get_portfolio_valuation", "status": "error", "message": f"Invalid UUID: '{portfolio_id}'"}

    port = PortfolioService.get_portfolio_for_user(db, pid, context_user_id)
    if not port:
        return {"tool": "get_portfolio_valuation", "status": "not_found", "message": "Portfolio not found or access denied."}

    val = PortfolioAnalyticsService.get_portfolio_valuation(db, port)
    return {
        "tool": "get_portfolio_valuation",
        "status": "success",
        "portfolio_id": str(port.id),
        "portfolio_name": port.name,
        "as_of": str(val.get("as_of_date")),
        "total_value": float(val.get("total_value", 0)),
        "cash_balance": float(val.get("cash_balance", 0)),
        "invested_capital": float(val.get("cost_basis", 0)),
        "total_unrealized_pnl": float(val.get("unrealized_pnl", 0)),
        "total_unrealized_pnl_pct": float(val.get("unrealized_pnl_percent", 0)),
        "holdings_count": len(val.get("holdings", [])),
        "retrieved_at": _iso_now(),
    }


def tool_get_portfolio_holdings(db: Session, context_user_id: uuid.UUID, portfolio_id: str) -> Dict[str, Any]:
    """Retrieves asset breakdown, weighted-average cost basis (WACB), and unrealized gains for user's portfolio."""
    try:
        pid = uuid.UUID(portfolio_id)
    except ValueError:
        return {"tool": "get_portfolio_holdings", "status": "error", "message": f"Invalid UUID: '{portfolio_id}'"}

    port = PortfolioService.get_portfolio_for_user(db, pid, context_user_id)
    if not port:
        return {"tool": "get_portfolio_holdings", "status": "not_found", "message": "Portfolio not found or access denied."}

    val = PortfolioAnalyticsService.get_portfolio_valuation(db, port)
    return {
        "tool": "get_portfolio_holdings",
        "status": "success",
        "portfolio_id": str(port.id),
        "portfolio_name": port.name,
        "holdings": [
            {
                "symbol": h["symbol"],
                "company_name": h["company_name"],
                "quantity": float(h["quantity"]),
                "wacb_cost": float(h["average_buy_price"]),
                "current_price": float(h["current_price"]) if h.get("current_price") else None,
                "current_value": float(h["market_value"]),
                "unrealized_pnl": float(h["unrealized_pnl"]),
                "unrealized_pnl_pct": float(h["unrealized_pnl_percent"]),
                "weight_pct": float(h.get("allocation_percent", 0)),
            }
            for h in val.get("holdings", [])
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_portfolio_performance(db: Session, context_user_id: uuid.UUID, portfolio_id: str) -> Dict[str, Any]:
    """Retrieves Time-Weighted Return (TWR), Money-Weighted XIRR, volatility, and Sharpe ratio for user's portfolio."""
    try:
        pid = uuid.UUID(portfolio_id)
    except ValueError:
        return {"tool": "get_portfolio_performance", "status": "error", "message": f"Invalid UUID: '{portfolio_id}'"}

    port = PortfolioService.get_portfolio_for_user(db, pid, context_user_id)
    if not port:
        return {"tool": "get_portfolio_performance", "status": "not_found", "message": "Portfolio not found or access denied."}

    perf = PortfolioAnalyticsService.calculate_performance_and_risk(db, port)
    return {
        "tool": "get_portfolio_performance",
        "status": "success",
        "portfolio_id": str(port.id),
        "portfolio_name": port.name,
        "twr_pct": perf.get("twr_percent"),
        "xirr_pct": perf.get("xirr_percent"),
        "annualized_volatility_pct": perf.get("annualized_volatility_percent"),
        "sharpe_ratio": perf.get("sharpe_ratio"),
        "max_drawdown_pct": perf.get("max_drawdown_percent"),
        "retrieved_at": _iso_now(),
    }


def tool_get_portfolio_risk(db: Session, context_user_id: uuid.UUID, portfolio_id: str) -> Dict[str, Any]:
    """Retrieves sector and asset allocation breakdown to evaluate portfolio diversification and risk."""
    try:
        pid = uuid.UUID(portfolio_id)
    except ValueError:
        return {"tool": "get_portfolio_risk", "status": "error", "message": f"Invalid UUID: '{portfolio_id}'"}

    port = PortfolioService.get_portfolio_for_user(db, pid, context_user_id)
    if not port:
        return {"tool": "get_portfolio_risk", "status": "not_found", "message": "Portfolio not found or access denied."}

    val = PortfolioAnalyticsService.get_portfolio_valuation(db, port)
    return {
        "tool": "get_portfolio_risk",
        "status": "success",
        "portfolio_id": str(port.id),
        "portfolio_name": port.name,
        "asset_allocation": [
            {"asset_type": a.get("type", "asset"), "value": float(a["value"]), "percentage": float(a["percentage"])}
            for a in val.get("asset_allocations", [])
        ],
        "sector_allocation": [
            {"sector": s["sector"], "value": float(s["value"]), "percentage": float(s["percentage"])}
            for s in val.get("sector_allocations", [])
        ],
        "retrieved_at": _iso_now(),
    }


# ==========================================
# 3. Mutual Fund (FundScope) Tools
# ==========================================

def tool_search_mutual_funds(db: Session, context_user_id: uuid.UUID, query: str, limit: int = 10) -> Dict[str, Any]:
    """Searches Indian mutual fund schemes by scheme name, AMC, or category."""
    clean_q = query.strip()
    funds = (
        db.query(MutualFund)
        .filter(
            or_(
                MutualFund.scheme_name.ilike(f"%{clean_q}%"),
                MutualFund.amc_name.ilike(f"%{clean_q}%"),
                MutualFund.category.ilike(f"%{clean_q}%"),
            )
        )
        .limit(min(limit, 25))
        .all()
    )
    return {
        "tool": "search_mutual_funds",
        "status": "success",
        "query": clean_q,
        "count": len(funds),
        "funds": [
            {
                "id": str(f.id),
                "scheme_code": f.scheme_code,
                "scheme_name": f.scheme_name,
                "amc_name": f.amc_name,
                "category": f.category,
                "plan_type": f.plan_type,
                "is_demo": f.is_demo,
            }
            for f in funds
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_fund_details(db: Session, context_user_id: uuid.UUID, fund_id_or_code: str) -> Dict[str, Any]:
    """Retrieves mutual fund metadata, latest NAV, expense ratio, and risk tier."""
    fund = _resolve_fund(db, fund_id_or_code)
    if not fund:
        return {"tool": "get_fund_details", "status": "not_found", "message": f"Fund '{fund_id_or_code}' not found."}

    latest_nav_rec = (
        db.query(FundNAVHistory)
        .filter(FundNAVHistory.fund_id == fund.id)
        .order_by(FundNAVHistory.nav_date.desc())
        .first()
    )

    return {
        "tool": "get_fund_details",
        "status": "success",
        "id": str(fund.id),
        "scheme_code": fund.scheme_code,
        "scheme_name": fund.scheme_name,
        "amc_name": fund.amc_name,
        "category": fund.category,
        "subcategory": fund.subcategory,
        "plan_type": fund.plan_type,
        "option": fund.option,
        "expense_ratio": float(fund.expense_ratio) if fund.expense_ratio is not None else None,
        "aum_crores": float(fund.aum_crores) if fund.aum_crores is not None else None,
        "risk_rating": fund.risk_rating,
        "latest_nav": float(latest_nav_rec.nav) if latest_nav_rec else None,
        "latest_nav_date": str(latest_nav_rec.nav_date) if latest_nav_rec else None,
        "is_demo": fund.is_demo,
        "retrieved_at": _iso_now(),
    }


def tool_get_fund_performance(db: Session, context_user_id: uuid.UUID, fund_id_or_code: str) -> Dict[str, Any]:
    """Retrieves trailing returns (1M, 3M, 6M, 1Y, 3Y, 5Y) and CAGR metrics for a mutual fund."""
    fund = _resolve_fund(db, fund_id_or_code)
    if not fund:
        return {"tool": "get_fund_performance", "status": "not_found", "message": f"Fund '{fund_id_or_code}' not found."}

    try:
        trailing = FundAnalyticsService.calculate_trailing_returns(db, fund.id)
    except Exception as e:
        return {"tool": "get_fund_performance", "status": "error", "message": str(e)}

    return {
        "tool": "get_fund_performance",
        "status": "success",
        "scheme_name": fund.scheme_name,
        "as_of": str(trailing.get("as_of_date")),
        "trailing_returns": {
            "return_1m_pct": trailing.get("return_1m_pct"),
            "return_3m_pct": trailing.get("return_3m_pct"),
            "return_6m_pct": trailing.get("return_6m_pct"),
            "return_1y_pct": trailing.get("return_1y_pct"),
            "cagr_3y_pct": trailing.get("cagr_3y_pct"),
            "cagr_5y_pct": trailing.get("cagr_5y_pct"),
        },
        "is_demo": fund.is_demo,
        "retrieved_at": _iso_now(),
    }


def tool_compare_mutual_funds(
    db: Session, context_user_id: uuid.UUID, fund_ids_or_codes: List[str]
) -> Dict[str, Any]:
    """Compares 2 to 4 mutual funds across trailing returns, expense ratios, and AUM."""
    resolved_ids = []
    for item in fund_ids_or_codes[:4]:
        fund = _resolve_fund(db, item)
        if fund:
            resolved_ids.append(fund.id)

    if len(resolved_ids) < 1:
        return {"tool": "compare_mutual_funds", "status": "error", "message": "At least one valid fund required."}

    try:
        comp_res = analytics_compare_funds(db=db, fund_ids=resolved_ids)
    except Exception as e:
        return {"tool": "compare_mutual_funds", "status": "error", "message": str(e)}

    return {
        "tool": "compare_mutual_funds",
        "status": "success",
        "funds": [
            {
                "scheme_name": f.scheme_name,
                "category": f.category,
                "latest_nav": f.latest_nav,
                "expense_ratio": f.expense_ratio,
                "aum_crores": f.aum_crores,
                "return_1y_pct": f.return_1y_pct,
                "cagr_3y_pct": f.cagr_3y_pct,
            }
            for f in comp_res.funds
        ],
        "retrieved_at": _iso_now(),
    }


# ==========================================
# 4. MarketPulse Tools
# ==========================================

def tool_search_market_news(db: Session, context_user_id: uuid.UUID, query: str, limit: int = 5) -> Dict[str, Any]:
    """Searches MarketPulse financial news articles and headlines."""
    clean_q = query.strip()
    articles = (
        db.query(NewsArticle)
        .filter(or_(NewsArticle.title.ilike(f"%{clean_q}%"), NewsArticle.summary.ilike(f"%{clean_q}%")))
        .order_by(NewsArticle.published_at.desc())
        .limit(min(limit, 10))
        .all()
    )
    return {
        "tool": "search_market_news",
        "status": "success",
        "query": clean_q,
        "count": len(articles),
        "articles": [
            {
                "id": str(a.id),
                "title": a.title,
                "summary": a.summary,
                "published_at": a.published_at.isoformat(),
                "category": a.category,
                "source_name": a.source.provider_name if a.source else "Financial Feed",
                "is_demo": a.is_demo,
            }
            for a in articles
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_company_news(db: Session, context_user_id: uuid.UUID, symbol_or_id: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieves news articles specifically linked to an equity ticker symbol."""
    inst = _resolve_instrument(db, symbol_or_id)
    if not inst:
        return {"tool": "get_company_news", "status": "not_found", "message": f"Instrument '{symbol_or_id}' not found."}

    links = (
        db.query(ArticleInstrumentLink)
        .filter(ArticleInstrumentLink.instrument_id == inst.id)
        .limit(min(limit, 10))
        .all()
    )
    articles = [link.article for link in links if link.article]

    return {
        "tool": "get_company_news",
        "status": "success",
        "symbol": inst.symbol,
        "count": len(articles),
        "articles": [
            {
                "id": str(a.id),
                "title": a.title,
                "summary": a.summary,
                "published_at": a.published_at.isoformat(),
                "source_name": a.source.provider_name if a.source else "Financial Feed",
                "is_demo": a.is_demo,
            }
            for a in articles
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_news_sentiment(
    db: Session, context_user_id: uuid.UUID, symbol_or_id: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieves lexicon-derived financial sentiment distributions and trend signals."""
    query = db.query(NewsSentiment)
    if symbol_or_id:
        inst = _resolve_instrument(db, symbol_or_id)
        if inst:
            query = query.join(NewsArticle).join(ArticleInstrumentLink).filter(ArticleInstrumentLink.instrument_id == inst.id)

    sentiments = query.limit(50).all()
    if not sentiments:
        return {"tool": "get_news_sentiment", "status": "no_data", "message": "No sentiment data recorded yet."}

    pos = sum(1 for s in sentiments if s.sentiment_label == "POSITIVE")
    neg = sum(1 for s in sentiments if s.sentiment_label == "NEGATIVE")
    neu = sum(1 for s in sentiments if s.sentiment_label == "NEUTRAL")
    avg_score = sum(s.sentiment_score for s in sentiments) / len(sentiments)

    return {
        "tool": "get_news_sentiment",
        "status": "success",
        "total_analyzed": len(sentiments),
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "average_score": round(avg_score, 3),
        "sentiment_disclaimer": "Lexicon-derived rule-based heuristic for educational observation, not a predictive signal.",
        "retrieved_at": _iso_now(),
    }


def tool_get_macro_indicators(db: Session, context_user_id: uuid.UUID) -> Dict[str, Any]:
    """Retrieves macroeconomic series and latest observations (e.g. CPI Inflation, RBI Repo Rate, GDP Growth)."""
    series_list = db.query(MacroEconomicSeries).all()
    results = []
    for s in series_list:
        latest_obs = (
            db.query(MacroEconomicObservation)
            .filter(MacroEconomicObservation.series_id == s.id)
            .order_by(MacroEconomicObservation.observation_date.desc())
            .first()
        )
        results.append({
            "series_name": s.series_name,
            "category": s.category,
            "frequency": s.frequency,
            "unit": s.unit,
            "latest_value": float(latest_obs.value) if latest_obs else None,
            "observation_date": str(latest_obs.observation_date) if latest_obs else None,
            "is_demo": s.is_demo,
        })

    return {
        "tool": "get_macro_indicators",
        "status": "success",
        "indicators": results,
        "retrieved_at": _iso_now(),
    }


# ==========================================
# 5. QuantLab Strategy & Backtesting Tools (Authenticated)
# ==========================================

def tool_get_saved_strategies(db: Session, context_user_id: uuid.UUID) -> Dict[str, Any]:
    """Retrieves quantitative research strategies owned strictly by the authenticated user."""
    strategies = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.user_id == context_user_id)
        .order_by(ResearchStrategy.created_at.desc())
        .all()
    )
    return {
        "tool": "get_saved_strategies",
        "status": "success",
        "count": len(strategies),
        "strategies": [
            {
                "id": str(s.id),
                "name": s.name,
                "strategy_type": s.strategy_type,
                "version": s.version,
                "parameters": s.parameters,
                "created_at": s.created_at.isoformat(),
            }
            for s in strategies
        ],
        "retrieved_at": _iso_now(),
    }


def tool_get_backtest_results(db: Session, context_user_id: uuid.UUID, run_id: str) -> Dict[str, Any]:
    """Retrieves quantitative performance metrics (CAGR, Sharpe, Drawdown, Win Rate) for user's backtest run."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        return {"tool": "get_backtest_results", "status": "error", "message": f"Invalid UUID: '{run_id}'"}

    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == rid, BacktestRun.user_id == context_user_id)
        .first()
    )
    if not run:
        return {"tool": "get_backtest_results", "status": "not_found", "message": "Backtest run not found or access denied."}

    return {
        "tool": "get_backtest_results",
        "status": "success",
        "run_id": str(run.id),
        "ticker": run.instrument.symbol if run.instrument else None,
        "start_date": str(run.start_date),
        "end_date": str(run.end_date),
        "starting_capital": float(run.starting_capital),
        "fee_rate": run.fee_rate,
        "slippage_bps": run.slippage_bps,
        "metrics": run.metrics,
        "simulation_disclaimer": "Simulated paper trading backtest with modeled fees and slippage; past returns do not guarantee future live performance.",
        "retrieved_at": _iso_now(),
    }


def tool_get_backtest_trades(
    db: Session, context_user_id: uuid.UUID, run_id: str, limit: int = 20
) -> Dict[str, Any]:
    """Retrieves chronological executed trades for user's backtest run."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        return {"tool": "get_backtest_trades", "status": "error", "message": f"Invalid UUID: '{run_id}'"}

    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == rid, BacktestRun.user_id == context_user_id)
        .first()
    )
    if not run:
        return {"tool": "get_backtest_trades", "status": "not_found", "message": "Backtest run not found or access denied."}

    trades = (
        db.query(BacktestTrade)
        .filter(BacktestTrade.run_id == run.id)
        .order_by(BacktestTrade.execution_date.asc())
        .limit(min(limit, 50))
        .all()
    )

    return {
        "tool": "get_backtest_trades",
        "status": "success",
        "run_id": str(run.id),
        "count": len(trades),
        "trades": [
            {
                "side": t.side,
                "signal_date": str(t.signal_date),
                "execution_date": str(t.execution_date),
                "quantity": float(t.quantity),
                "execution_price": float(t.execution_price),
                "fees": float(t.fees),
                "realized_pnl": float(t.realized_pnl) if t.realized_pnl is not None else None,
            }
            for t in trades
        ],
        "retrieved_at": _iso_now(),
    }


def tool_compare_backtest_runs(
    db: Session, context_user_id: uuid.UUID, run_ids: List[str]
) -> Dict[str, Any]:
    """Compares metrics across 2 to 5 backtest runs owned strictly by the authenticated user."""
    runs = []
    for raw_id in run_ids[:5]:
        try:
            rid = uuid.UUID(raw_id)
            r = db.query(BacktestRun).filter(BacktestRun.id == rid, BacktestRun.user_id == context_user_id).first()
            if r:
                runs.append(r)
        except ValueError:
            continue

    if len(runs) < 1:
        return {"tool": "compare_backtest_runs", "status": "error", "message": "At least one valid owned run required."}

    return {
        "tool": "compare_backtest_runs",
        "status": "success",
        "runs": [
            {
                "run_id": str(r.id),
                "ticker": r.instrument.symbol if r.instrument else None,
                "strategy_type": r.strategy.strategy_type if r.strategy else "CUSTOM",
                "total_return_pct": r.metrics.get("total_return_pct") if r.metrics else None,
                "sharpe_ratio": r.metrics.get("sharpe_ratio") if r.metrics else None,
                "max_drawdown_pct": r.metrics.get("max_drawdown_pct") if r.metrics else None,
                "win_rate_pct": r.metrics.get("win_rate_pct") if r.metrics else None,
            }
            for r in runs
        ],
        "retrieved_at": _iso_now(),
    }


# ==========================================
# Tool Registry Map & Schemas
# ==========================================

AVAILABLE_TOOLS: Dict[str, Dict[str, Any]] = {
    "search_instruments": {
        "function": tool_search_instruments,
        "description": "Search Indian equity instruments by ticker symbol or company name.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query like 'RELIANCE', 'TCS', 'Tata'"},
                "limit": {"type": "integer", "description": "Maximum results to return, default 10"},
            },
            "required": ["query"],
        },
    },
    "get_instrument_profile": {
        "function": tool_get_instrument_profile,
        "description": "Get company profile, exchange, sector, industry, and latest closing price for a stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Stock ticker (e.g. 'TCS') or instrument UUID"},
            },
            "required": ["symbol_or_id"],
        },
    },
    "get_price_history": {
        "function": tool_get_price_history,
        "description": "Get historical daily OHLCV trading bars for an equity.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Stock ticker or instrument UUID"},
                "limit": {"type": "integer", "description": "Number of bars (default 30)"},
            },
            "required": ["symbol_or_id"],
        },
    },
    "get_technical_indicators": {
        "function": tool_get_technical_indicators,
        "description": "Calculate SMA (20, 50, 200), EMA (12, 26), RSI 14, MACD, and Bollinger Bands for a stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Stock ticker or UUID"},
            },
            "required": ["symbol_or_id"],
        },
    },
    "get_fundamental_ratios": {
        "function": tool_get_fundamental_ratios,
        "description": "Calculate financial ratios (P/E, P/B, ROE, Debt/Equity, Net Margin) from audited financial statements.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Stock ticker or UUID"},
            },
            "required": ["symbol_or_id"],
        },
    },
    "compare_equities": {
        "function": tool_compare_equities,
        "description": "Compare 2 to 4 stocks side-by-side on period returns, volatility, drawdown, and indicators.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols_or_ids": {"type": "array", "items": {"type": "string"}, "description": "List of 2-4 stock tickers"},
                "period": {"type": "string", "description": "Comparison timeframe: '1M', '3M', '6M', '1Y', '3Y'"},
            },
            "required": ["symbols_or_ids"],
        },
    },
    "list_user_portfolios": {
        "function": tool_list_user_portfolios,
        "description": "List all investment portfolios owned by the authenticated user.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    "get_portfolio_valuation": {
        "function": tool_get_portfolio_valuation,
        "description": "Get current total market value, cash balance, invested capital, and unrealized P&L for a portfolio.",
        "parameters": {
            "type": "object",
            "properties": {
                "portfolio_id": {"type": "string", "description": "Portfolio UUID"},
            },
            "required": ["portfolio_id"],
        },
    },
    "get_portfolio_holdings": {
        "function": tool_get_portfolio_holdings,
        "description": "Get breakdown of individual holdings, shares, weighted-average cost basis (WACB), and unrealized gains.",
        "parameters": {
            "type": "object",
            "properties": {
                "portfolio_id": {"type": "string", "description": "Portfolio UUID"},
            },
            "required": ["portfolio_id"],
        },
    },
    "get_portfolio_performance": {
        "function": tool_get_portfolio_performance,
        "description": "Get performance metrics: Time-Weighted Return (TWR), Money-Weighted Return (XIRR), volatility, and Sharpe ratio.",
        "parameters": {
            "type": "object",
            "properties": {
                "portfolio_id": {"type": "string", "description": "Portfolio UUID"},
            },
            "required": ["portfolio_id"],
        },
    },
    "get_portfolio_risk": {
        "function": tool_get_portfolio_risk,
        "description": "Get asset allocation and sector diversification breakdown for portfolio risk evaluation.",
        "parameters": {
            "type": "object",
            "properties": {
                "portfolio_id": {"type": "string", "description": "Portfolio UUID"},
            },
            "required": ["portfolio_id"],
        },
    },
    "search_mutual_funds": {
        "function": tool_search_mutual_funds,
        "description": "Search mutual fund schemes by scheme name, AMC, or category.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term like 'HDFC', 'Small Cap', 'Index'"},
                "limit": {"type": "integer", "description": "Max funds to return"},
            },
            "required": ["query"],
        },
    },
    "get_fund_details": {
        "function": tool_get_fund_details,
        "description": "Get mutual fund profile, latest NAV, AMC, expense ratio, AUM, and risk rating.",
        "parameters": {
            "type": "object",
            "properties": {
                "fund_id_or_code": {"type": "string", "description": "Fund scheme code or UUID"},
            },
            "required": ["fund_id_or_code"],
        },
    },
    "get_fund_performance": {
        "function": tool_get_fund_performance,
        "description": "Get mutual fund trailing returns (1M to 5Y) and CAGR metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "fund_id_or_code": {"type": "string", "description": "Fund scheme code or UUID"},
            },
            "required": ["fund_id_or_code"],
        },
    },
    "compare_mutual_funds": {
        "function": tool_compare_mutual_funds,
        "description": "Compare 2 to 4 mutual funds across trailing returns, expense ratios, and AUM.",
        "parameters": {
            "type": "object",
            "properties": {
                "fund_ids_or_codes": {"type": "array", "items": {"type": "string"}, "description": "List of fund codes or UUIDs"},
            },
            "required": ["fund_ids_or_codes"],
        },
    },
    "search_market_news": {
        "function": tool_search_market_news,
        "description": "Search financial news headlines and articles by topic or keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword like 'RBI', 'inflation', 'earnings'"},
                "limit": {"type": "integer", "description": "Max articles"},
            },
            "required": ["query"],
        },
    },
    "get_company_news": {
        "function": tool_get_company_news,
        "description": "Get news headlines specifically referencing an equity ticker.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Stock ticker like 'RELIANCE' or 'TCS'"},
                "limit": {"type": "integer", "description": "Max articles"},
            },
            "required": ["symbol_or_id"],
        },
    },
    "get_news_sentiment": {
        "function": tool_get_news_sentiment,
        "description": "Get sentiment analysis score and positive/negative distribution for general market or a specific stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol_or_id": {"type": "string", "description": "Optional stock ticker"},
            },
        },
    },
    "get_macro_indicators": {
        "function": tool_get_macro_indicators,
        "description": "Get key Indian macroeconomic indicators like CPI Inflation, RBI Repo Rate, and GDP Growth.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    "get_saved_strategies": {
        "function": tool_get_saved_strategies,
        "description": "Get saved QuantLab research strategies owned by the authenticated user.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    "get_backtest_results": {
        "function": tool_get_backtest_results,
        "description": "Get performance metrics (CAGR, Sharpe, Max Drawdown, Win Rate) for a historical backtest run.",
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Backtest run UUID"},
            },
            "required": ["run_id"],
        },
    },
    "get_backtest_trades": {
        "function": tool_get_backtest_trades,
        "description": "Get chronological simulated trade executions for a backtest run.",
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Backtest run UUID"},
                "limit": {"type": "integer", "description": "Max trades"},
            },
            "required": ["run_id"],
        },
    },
    "compare_backtest_runs": {
        "function": tool_compare_backtest_runs,
        "description": "Compare metrics across 2 to 5 saved backtest runs side-by-side.",
        "parameters": {
            "type": "object",
            "properties": {
                "run_ids": {"type": "array", "items": {"type": "string"}, "description": "List of 2 to 5 run UUIDs"},
            },
            "required": ["run_ids"],
        },
    },
}


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: Session,
    context_user_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Safely dispatches a read-only tool execution.
    Enforces user_id injection, execution bounds, and captures any internal exceptions.
    """
    if tool_name not in AVAILABLE_TOOLS:
        return {
            "tool": tool_name,
            "status": "denied",
            "error": f"Tool '{tool_name}' is not in the permitted allowlist.",
        }

    tool_def = AVAILABLE_TOOLS[tool_name]
    func = tool_def["function"]

    # Filter arguments against schema properties to prevent arbitrary kwargs injection
    permitted_props = set(tool_def["parameters"].get("properties", {}).keys())

    # Map common convenience argument aliases
    normalized_args = dict(arguments)
    if "symbol" in normalized_args and "symbol_or_id" in permitted_props and "symbol_or_id" not in normalized_args:
        normalized_args["symbol_or_id"] = normalized_args["symbol"]
    if "symbols" in normalized_args and "symbols_or_ids" in permitted_props and "symbols_or_ids" not in normalized_args:
        normalized_args["symbols_or_ids"] = normalized_args["symbols"]

    sanitized_args = {k: v for k, v in normalized_args.items() if k in permitted_props}

    start_time = datetime.now(timezone.utc)
    try:
        result = func(db=db, context_user_id=context_user_id, **sanitized_args)
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        return {
            "tool": tool_name,
            "status": "success",
            "execution_time_ms": duration_ms,
            "result": result,
        }
    except Exception as e:
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        return {
            "tool": tool_name,
            "status": "error",
            "execution_time_ms": duration_ms,
            "error": str(e),
        }
