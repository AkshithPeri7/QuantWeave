"""
Multi-Instrument Equity Comparison Engine for QuantWeave.

Compares 2 to 4 equity instruments over supported periods (1M, 3M, 6M, 1Y, ALL):
- Normalized price series rebased to 100.0 at the period start date
- Total period return (%)
- Annualized daily return volatility (%) using sqrt(252) annualization factor
- Maximum drawdown (%) over the evaluation window
- Aligned technical indicators (SMA 20/50/200, RSI 14, MACD, Golden/Death cross)
- Fundamental valuation and profitability ratios (P/E, P/B, ROE, Margins, D/E)

Missing Data & Non-Overlapping Dates Methodology:
- Constructs the union of all trading dates within the window.
- For days where one exchange or stock has a holiday or suspension, price is
  forward-filled from the last verified closing price.
- Instruments with insufficient history return None for metrics requiring more
  observations than available.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.fundamentals import calculate_statement_ratios
from app.analytics.technical import calculate_all_technicals
from app.models.financial_statement import FinancialStatement
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory


@dataclass
class NormalizedDataPoint:
    trade_date: str
    prices: Dict[str, Optional[float]]  # symbol -> normalized price (base 100.0)


@dataclass
class InstrumentComparisonMetrics:
    instrument_id: str
    symbol: str
    company_name: str
    exchange: str
    sector: Optional[str]
    currency: str
    # Performance & Risk
    latest_price: Optional[float]
    period_return_pct: Optional[float]
    annualized_volatility_pct: Optional[float]
    max_drawdown_pct: Optional[float]
    # Technical Indicators
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    rsi_14: Optional[float]
    macd_signal_state: str  # "Bullish", "Bearish", "Neutral"
    ma_cross_state: Optional[str]  # "Golden Cross" (50 > 200), "Death Cross" (50 < 200), or None
    # Fundamental Ratios
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    roe_pct: Optional[float]
    net_margin_pct: Optional[float]
    operating_margin_pct: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    has_fundamentals: bool


@dataclass
class ComparisonResult:
    period: str
    start_date: Optional[str]
    end_date: Optional[str]
    instruments: List[InstrumentComparisonMetrics]
    normalized_chart: List[NormalizedDataPoint]


def get_period_cutoff(period: str, max_date: date) -> Optional[date]:
    """Calculates start date cutoff based on standard time horizons."""
    period_upper = period.upper().strip()
    if period_upper == "1M":
        return max_date - timedelta(days=30)
    elif period_upper == "3M":
        return max_date - timedelta(days=90)
    elif period_upper == "6M":
        return max_date - timedelta(days=180)
    elif period_upper == "1Y":
        return max_date - timedelta(days=365)
    elif period_upper == "ALL":
        return None
    else:
        # Default fallback to 1Y
        return max_date - timedelta(days=365)


def compare_equities(
    db: Session,
    instrument_ids: List[Any],
    period: str = "1Y",
) -> ComparisonResult:
    """
    Executes multi-instrument comparative analytics for 2 to 4 instruments.
    """
    if len(instrument_ids) < 1:
        raise ValueError("At least 1 instrument must be specified for comparison.")
    if len(instrument_ids) > 4:
        raise ValueError("A maximum of 4 instruments can be compared simultaneously.")

    # 1. Fetch Instruments
    instruments: List[Instrument] = (
        db.query(Instrument).filter(Instrument.id.in_(instrument_ids)).all()
    )
    if not instruments:
        raise ValueError("None of the specified instruments were found.")

    # 2. Fetch Price History for all selected instruments
    inst_prices: Dict[str, List[PriceHistory]] = {}
    all_dates_set = set()
    latest_global_date: Optional[date] = None

    for inst in instruments:
        bars = (
            db.query(PriceHistory)
            .filter(PriceHistory.instrument_id == inst.id)
            .order_by(PriceHistory.trade_date.asc())
            .all()
        )
        inst_prices[str(inst.id)] = bars
        for b in bars:
            all_dates_set.add(b.trade_date)
            if latest_global_date is None or b.trade_date > latest_global_date:
                latest_global_date = b.trade_date

    if not latest_global_date or not all_dates_set:
        return ComparisonResult(
            period=period,
            start_date=None,
            end_date=None,
            instruments=[],
            normalized_chart=[],
        )

    # 3. Apply Period Filter
    cutoff_date = get_period_cutoff(period, latest_global_date)
    filtered_dates = sorted(
        [d for d in all_dates_set if cutoff_date is None or d >= cutoff_date]
    )

    if not filtered_dates:
        filtered_dates = sorted(list(all_dates_set))

    start_date_str = str(filtered_dates[0])
    end_date_str = str(filtered_dates[-1])

    # 4. Build Aligned Time Series DataFrame with Forward-Fill
    price_series_dict: Dict[str, pd.Series] = {}
    for inst in instruments:
        bars = inst_prices.get(str(inst.id), [])
        if not bars:
            continue
        bar_dates = [b.trade_date for b in bars]
        bar_closes = [float(b.close) for b in bars]
        s = pd.Series(bar_closes, index=pd.to_datetime(bar_dates))
        # Reindex to all filtered dates and forward fill for holidays/gaps
        idx = pd.to_datetime(filtered_dates)
        s_aligned = s.reindex(idx).ffill().bfill()
        price_series_dict[inst.symbol] = s_aligned

    # 5. Compute Normalized Chart Points (Base = 100.0)
    normalized_chart: List[NormalizedDataPoint] = []
    for d in filtered_dates:
        d_ts = pd.to_datetime(d)
        norm_map: Dict[str, Optional[float]] = {}
        for inst in instruments:
            series = price_series_dict.get(inst.symbol)
            if series is not None and not series.empty:
                base_price = float(series.iloc[0])
                curr_price = float(series.loc[d_ts]) if d_ts in series.index else None
                if base_price > 0 and curr_price is not None:
                    norm_map[inst.symbol] = round((curr_price / base_price) * 100.0, 2)
                else:
                    norm_map[inst.symbol] = None
            else:
                norm_map[inst.symbol] = None
        normalized_chart.append(
            NormalizedDataPoint(
                trade_date=str(d),
                prices=norm_map,
            )
        )

    # 6. Compute Individual Comparative Metrics
    metrics_list: List[InstrumentComparisonMetrics] = []

    for inst in instruments:
        bars_all = inst_prices.get(str(inst.id), [])
        series = price_series_dict.get(inst.symbol)

        # Performance & Risk
        latest_price = None
        period_return_pct = None
        volatility_pct = None
        max_dd_pct = None

        if series is not None and len(series) > 0:
            first_val = float(series.iloc[0])
            last_val = float(series.iloc[-1])
            latest_price = round(last_val, 2)

            if first_val > 0:
                period_return_pct = round(((last_val - first_val) / first_val) * 100.0, 2)

            # Volatility (annualized std of daily returns)
            daily_returns = series.pct_change().dropna()
            if len(daily_returns) >= 2:
                daily_std = float(daily_returns.std(ddof=1))
                volatility_pct = round(daily_std * np.sqrt(252.0) * 100.0, 2)
            else:
                volatility_pct = 0.0

            # Max Drawdown
            rolling_peak = series.cummax()
            drawdowns = (rolling_peak - series) / rolling_peak * 100.0
            max_dd_pct = round(float(drawdowns.max()), 2)

        # Technical Indicators on full available history
        tech_points, tech_summary = calculate_all_technicals(bars_all)
        last_tech = tech_points[-1] if tech_points else None

        sma_20 = last_tech.sma_20 if last_tech else None
        sma_50 = last_tech.sma_50 if last_tech else None
        sma_200 = last_tech.sma_200 if last_tech else None
        rsi_14 = last_tech.rsi_14 if last_tech else None

        macd_state = "Neutral"
        if last_tech and last_tech.macd_line is not None and last_tech.macd_signal is not None:
            if last_tech.macd_line > last_tech.macd_signal:
                macd_state = "Bullish"
            else:
                macd_state = "Bearish"

        ma_cross = None
        if sma_50 is not None and sma_200 is not None:
            ma_cross = "Golden Cross" if sma_50 > sma_200 else "Death Cross"

        # Fundamentals
        stmt = (
            db.query(FinancialStatement)
            .filter(
                FinancialStatement.instrument_id == inst.id,
                FinancialStatement.period_type == "annual",
            )
            .order_by(FinancialStatement.fiscal_year.desc())
            .first()
        )

        pe = None
        pb = None
        roe = None
        net_margin = None
        op_margin = None
        de = None
        cr = None
        has_fund = False

        if stmt:
            has_fund = True
            ratios = calculate_statement_ratios(stmt, latest_price=latest_price)
            pe = ratios.pe_ratio
            pb = ratios.pb_ratio
            roe = ratios.roe_pct
            net_margin = ratios.net_margin_pct
            op_margin = ratios.operating_margin_pct
            de = ratios.debt_to_equity
            cr = ratios.current_ratio

        metrics_list.append(
            InstrumentComparisonMetrics(
                instrument_id=str(inst.id),
                symbol=inst.symbol,
                company_name=inst.company_name,
                exchange=inst.exchange,
                sector=inst.sector,
                currency=inst.currency,
                latest_price=latest_price,
                period_return_pct=period_return_pct,
                annualized_volatility_pct=volatility_pct,
                max_drawdown_pct=max_dd_pct,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                rsi_14=rsi_14,
                macd_signal_state=macd_state,
                ma_cross_state=ma_cross,
                pe_ratio=pe,
                pb_ratio=pb,
                roe_pct=roe,
                net_margin_pct=net_margin,
                operating_margin_pct=op_margin,
                debt_to_equity=de,
                current_ratio=cr,
                has_fundamentals=has_fund,
            )
        )

    return ComparisonResult(
        period=period,
        start_date=start_date_str,
        end_date=end_date_str,
        instruments=metrics_list,
        normalized_chart=normalized_chart,
    )
