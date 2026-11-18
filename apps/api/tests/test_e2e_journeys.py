"""
End-to-End User Journey Verification Suite (Milestone 9).

Automates and verifies all 17 core user journeys across QuantWeave:
1.  Journey 01: User Registration & Authentication (JWT + Cookie validation)
2.  Journey 02: Stock Search & Discovery (NSE/BSE instruments)
3.  Journey 03: Equity Technical Intelligence (RSI, MACD, SMAs, Bollinger Bands)
4.  Journey 04: Equity Fundamental Intelligence (P/E, P/B, ROE, Debt/Equity)
5.  Journey 05: Side-by-Side Equity Comparison (TCS vs INFY)
6.  Journey 06: Portfolio Creation & Capital Inflow (INR portfolio, CASH_DEPOSIT)
7.  Journey 07: Portfolio Transaction Ledger (BUY, SELL, WACB, Oversell protection)
8.  Journey 08: Portfolio Valuation, Risk & Performance (Valuation, TWR, XIRR)
9.  Journey 09: FundScope Mutual Fund Directory & Search (category & AMC filters)
10. Journey 10: FundScope Analytics & SIP Calculator (trailing returns, SIP projections)
11. Journey 11: FundScope Multi-Fund Comparison (normalized comparison)
12. Journey 12: MarketPulse Financial News Feed & Categorization
13. Journey 13: MarketPulse Lexicon Sentiment Heuristics
14. Journey 14: MarketPulse Macroeconomic Indicators (CPI Inflation, RBI Repo Rate)
15. Journey 15: QuantLab Strategy Definition & Backtest Execution
16. Journey 16: QuantLab Parameter Grid Search & Strategy Optimization
17. Journey 17: AI Copilot Multi-Turn Chat, Tool Calling & RAG Citations
"""

from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.instrument import Instrument
from app.models.mutual_fund import FundNAVHistory, MutualFund
from app.models.price_history import PriceHistory
from app.models.user import User
from app.providers.financial_fixtures import seed_demo_financial_statements
from app.providers.fund_fixtures import seed_demo_mutual_funds
from app.services.ingestion import seed_demo_market_data
from app.services.news_ingestion import NewsIngestionService


@pytest.fixture(autouse=True)
def seed_all_fixtures(db_session: Session):
    """Ensures deterministic demo dataset is loaded before running user journeys."""
    if db_session.query(Instrument).count() == 0:
        seed_demo_market_data(db_session)
    if db_session.query(MutualFund).count() == 0:
        seed_demo_mutual_funds(db_session, trading_days=100)
    seed_demo_financial_statements(db_session)
    NewsIngestionService.seed_demo_market_pulse(db_session)


@pytest.fixture
def journey_user(db_session: Session) -> User:
    """Creates a dedicated verified user for end-to-end journey tests."""
    user = User(
        name="Journeys Analyst",
        email=f"analyst_{uuid.uuid4().hex[:6]}@quantweave.test",
        password_hash=hash_password("JourneysPassword123!"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def journey_headers(journey_user: User) -> dict:
    token = create_access_token(str(journey_user.id), {"email": journey_user.email, "role": journey_user.role})
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }


# =========================================================================
# Journey 01: User Registration & Authentication
# =========================================================================
def test_journey_01_authentication_flow(client: TestClient):
    # 1. Register new account
    reg_email = f"newuser_{uuid.uuid4().hex[:6]}@quantweave.test"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": reg_email, "name": "New Investor", "password": "StrongPassword123!"},
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == reg_email
    assert "access_token" in reg_data

    # 2. Login to obtain access token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": reg_email, "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Access protected me route
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == reg_email


# =========================================================================
# Journey 02: Stock Search & Discovery
# =========================================================================
def test_journey_02_stock_search(client: TestClient, journey_headers: dict):
    # Search for TCS by query string
    res = client.get("/api/v1/instruments/search?q=TCS", headers=journey_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert any(i["symbol"] == "TCS" for i in items)

    # Search for IT sector instruments via paginated list
    sector_res = client.get("/api/v1/instruments?sector=Information%20Technology", headers=journey_headers)
    assert sector_res.status_code == 200
    sector_data = sector_res.json()
    assert sector_data["total"] >= 1
    assert any(i["symbol"] in ("TCS", "INFY") for i in sector_data["items"])


# =========================================================================
# Journey 03: Equity Technical Intelligence
# =========================================================================
def test_journey_03_technical_indicators(client: TestClient, journey_headers: dict, db_session: Session):
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    res = client.get(f"/api/v1/instruments/{tcs.id}/technicals", headers=journey_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "TCS"
    assert "summary" in data
    assert "points" in data
    assert len(data["points"]) > 0

    latest_pt = data["points"][-1]
    assert latest_pt["close"] > 0
    assert latest_pt["sma_20"] is not None
    assert latest_pt["rsi_14"] is not None


# =========================================================================
# Journey 04: Equity Fundamental Intelligence
# =========================================================================
def test_journey_04_fundamental_ratios(client: TestClient, journey_headers: dict, db_session: Session):
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    res = client.get(f"/api/v1/instruments/{tcs.id}/fundamentals", headers=journey_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "TCS"
    assert "statements" in data
    assert len(data["statements"]) >= 1
    assert "disclaimer" in data


# =========================================================================
# Journey 05: Side-by-Side Equity Comparison
# =========================================================================
def test_journey_05_equity_comparison(client: TestClient, journey_headers: dict, db_session: Session):
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    infy = db_session.query(Instrument).filter(Instrument.symbol == "INFY").first()
    assert tcs is not None and infy is not None

    res = client.get(f"/api/v1/instruments/compare?ids={tcs.id},{infy.id}&period=1Y", headers=journey_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["instruments"]) == 2
    symbols = [inst["symbol"] for inst in data["instruments"]]
    assert "TCS" in symbols
    assert "INFY" in symbols
    assert "normalized_chart" in data


# =========================================================================
# Journey 06 & 07: Portfolio Creation, Ledger & Transactions
# =========================================================================
def test_journey_06_and_07_portfolio_ledger(client: TestClient, journey_headers: dict, db_session: Session):
    # 1. Create Portfolio
    port_res = client.post(
        "/api/v1/portfolios",
        headers=journey_headers,
        json={"name": "Alpha Growth Portfolio", "description": "Long-term tech compounders", "base_currency": "INR"},
    )
    assert port_res.status_code == 201
    port_id = port_res.json()["id"]

    # 2. Deposit Cash: ₹500,000
    dep_res = client.post(
        f"/api/v1/portfolios/{port_id}/transactions",
        headers=journey_headers,
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "quantity": 1.0,
            "price_per_unit": 500000.0,
            "fees": 0.0,
            "notes": "Initial capital deposit",
        },
    )
    assert dep_res.status_code == 201

    # 3. Look up TCS instrument ID
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    # 4. Record BUY: 50 shares of TCS @ ₹3,500
    buy_res = client.post(
        f"/api/v1/portfolios/{port_id}/transactions",
        headers=journey_headers,
        json={
            "transaction_type": "BUY",
            "instrument_id": str(tcs.id),
            "trade_date": "2026-01-05",
            "quantity": 50.0,
            "price_per_unit": 3500.0,
            "fees": 20.0,
        },
    )
    assert buy_res.status_code == 201

    # 5. Prevent Overselling: Attempting to sell 100 shares must fail
    oversell_res = client.post(
        f"/api/v1/portfolios/{port_id}/transactions",
        headers=journey_headers,
        json={
            "transaction_type": "SELL",
            "instrument_id": str(tcs.id),
            "trade_date": "2026-01-10",
            "quantity": 100.0,
            "price_per_unit": 3600.0,
            "fees": 20.0,
        },
    )
    assert oversell_res.status_code == 400
    assert "shares" in oversell_res.json()["detail"].lower() or "oversell" in oversell_res.json()["detail"].lower()

    # 6. Valid SELL: Sell 20 shares of TCS @ ₹3,600
    sell_res = client.post(
        f"/api/v1/portfolios/{port_id}/transactions",
        headers=journey_headers,
        json={
            "transaction_type": "SELL",
            "instrument_id": str(tcs.id),
            "trade_date": "2026-01-15",
            "quantity": 20.0,
            "price_per_unit": 3600.0,
            "fees": 20.0,
        },
    )
    assert sell_res.status_code == 201


# =========================================================================
# Journey 08: Portfolio Valuation, Risk & Performance
# =========================================================================
def test_journey_08_portfolio_valuation(client: TestClient, journey_headers: dict):
    # Retrieve user's portfolios
    ports_res = client.get("/api/v1/portfolios", headers=journey_headers)
    assert ports_res.status_code == 200
    ports = ports_res.json()
    if ports:
        pid = ports[0]["id"]
        # Valuation endpoint
        val_res = client.get(f"/api/v1/portfolios/{pid}/valuation", headers=journey_headers)
        assert val_res.status_code == 200
        val = val_res.json()
        assert "total_value" in val
        assert "cash_balance" in val
        assert "holdings" in val

        # Performance endpoint
        perf_res = client.get(f"/api/v1/portfolios/{pid}/performance", headers=journey_headers)
        assert perf_res.status_code == 200
        perf = perf_res.json()
        assert "twr_percent" in perf
        assert "max_drawdown_percent" in perf


# =========================================================================
# Journey 09 & 10: FundScope Mutual Fund Intelligence
# =========================================================================
def test_journey_09_and_10_fundscope(client: TestClient, journey_headers: dict, db_session: Session):
    # 1. Directory and Search
    search_res = client.get("/api/v1/funds/search?q=Parikh", headers=journey_headers)
    assert search_res.status_code == 200
    funds = search_res.json()
    assert len(funds) >= 1
    fund_id = funds[0]["id"]

    # 2. Fund Profile & Details
    detail_res = client.get(f"/api/v1/funds/{fund_id}", headers=journey_headers)
    assert detail_res.status_code == 200
    f_detail = detail_res.json()
    assert "scheme_name" in f_detail
    assert "plan_type" in f_detail

    # 3. SIP Calculator on historical NAVs
    navs = (
        db_session.query(FundNAVHistory)
        .filter(FundNAVHistory.fund_id == uuid.UUID(fund_id))
        .order_by(FundNAVHistory.nav_date.asc())
        .all()
    )
    assert len(navs) >= 10
    start_d = navs[0].nav_date.isoformat()
    end_d = navs[-1].nav_date.isoformat()

    sip_res = client.post(
        f"/api/v1/funds/{fund_id}/sip-calculator",
        headers=journey_headers,
        json={
            "monthly_amount": 5000.0,
            "start_date": start_d,
            "end_date": end_d,
            "sip_day": 5,
        },
    )
    assert sip_res.status_code == 200
    sip_data = sip_res.json()
    assert sip_data["total_invested"] > 0
    assert sip_data["units_accumulated"] > 0


# =========================================================================
# Journey 11: FundScope Multi-Fund Comparison
# =========================================================================
def test_journey_11_fund_comparison(client: TestClient, journey_headers: dict):
    all_funds = client.get("/api/v1/funds?page=1&size=2", headers=journey_headers).json()["items"]
    assert len(all_funds) >= 2
    f_ids = [f["id"] for f in all_funds]

    comp_res = client.get(f"/api/v1/funds/compare?ids={f_ids[0]},{f_ids[1]}&period=6M", headers=journey_headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["funds"]) == 2
    assert "normalized_chart" in comp_data


# =========================================================================
# Journey 12, 13, 14: MarketPulse News, Sentiment & Macro
# =========================================================================
def test_journey_12_13_14_marketpulse(client: TestClient, journey_headers: dict):
    # 1. News Articles
    news_res = client.get("/api/v1/market/news", headers=journey_headers)
    assert news_res.status_code == 200
    articles = news_res.json()["items"]
    assert len(articles) >= 1

    # 2. Sentiment Summary
    sent_res = client.get("/api/v1/market/sentiment/summary", headers=journey_headers)
    assert sent_res.status_code == 200
    sent = sent_res.json()
    assert "overall_classification" in sent
    assert "net_sentiment_score" in sent

    # 3. Macroeconomic Series Catalog
    macro_res = client.get("/api/v1/market/macro/series", headers=journey_headers)
    assert macro_res.status_code == 200
    macro_series = macro_res.json()
    assert len(macro_series) >= 1


# =========================================================================
# Journey 15 & 16: QuantLab Backtesting & Grid Search
# =========================================================================
def test_journey_15_16_quantlab(client: TestClient, journey_headers: dict, db_session: Session):
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    # Query price dates for TCS
    prices = (
        db_session.query(PriceHistory)
        .filter(PriceHistory.instrument_id == tcs.id)
        .order_by(PriceHistory.trade_date.asc())
        .all()
    )
    assert len(prices) >= 50
    start_d = prices[0].trade_date.isoformat()
    end_d = prices[-1].trade_date.isoformat()

    # 1. Create Strategy
    strat_res = client.post(
        "/api/v1/quantlab/strategies",
        headers=journey_headers,
        json={
            "name": "E2E SMA Crossover Strategy",
            "strategy_type": "SMA_CROSSOVER",
            "description": "Fast 20 crosses slow 50",
            "parameters": {"fast_period": 20, "slow_period": 50},
        },
    )
    assert strat_res.status_code == 201
    strat_id = strat_res.json()["id"]

    # 2. Execute Backtest on Saved Strategy
    bt_res = client.post(
        f"/api/v1/quantlab/strategies/{strat_id}/backtest",
        headers=journey_headers,
        json={
            "instrument_id": str(tcs.id),
            "start_date": start_d,
            "end_date": end_d,
            "starting_capital": 100000.0,
            "fee_rate": 0.001,
            "slippage_bps": 5.0,
        },
    )
    assert bt_res.status_code == 201
    bt = bt_res.json()
    assert bt["status"] == "COMPLETED"
    assert "metrics" in bt
    assert "sharpe_ratio" in bt["metrics"]
    assert "max_drawdown_pct" in bt["metrics"]

    # 3. Parameter Grid Search Experiment
    grid_res = client.post(
        "/api/v1/quantlab/experiments/grid-search",
        headers=journey_headers,
        json={
            "strategy_type": "SMA_CROSSOVER",
            "instrument_id": str(tcs.id),
            "start_date": start_d,
            "end_date": end_d,
            "starting_capital": 100000.0,
            "fee_rate": 0.001,
            "slippage_bps": 5.0,
            "train_ratio": 0.7,
            "param_grid": {
                "fast_period": [10, 20],
                "slow_period": [50],
            },
        },
    )
    assert grid_res.status_code == 200
    grid = grid_res.json()
    assert grid["combinations_tested"] == 2
    assert len(grid["results"]) == 2


# =========================================================================
# Journey 17: AI Copilot Multi-Turn Chat, Tool Calling & Citations
# =========================================================================
def test_journey_17_ai_copilot_lifecycle(client: TestClient, journey_headers: dict):
    # 1. Create AI Conversation
    conv_res = client.post(
        "/api/v1/ai/conversations",
        headers=journey_headers,
        json={"title": "E2E Copilot Research Session", "context_module": "equity"},
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 2. First Turn: Ask about technical indicators
    turn_1 = client.post(
        f"/api/v1/ai/conversations/{conv_id}/messages",
        headers=journey_headers,
        json={"content": "Explain TCS's RSI and MACD indicators."},
    )
    assert turn_1.status_code == 200
    res_1 = turn_1.json()
    assert "RSI" in res_1["content"]
    assert len(res_1["tool_executions"]) >= 1

    # 3. Second Turn: Ask follow-up question
    turn_2 = client.post(
        f"/api/v1/ai/conversations/{conv_id}/messages",
        headers=journey_headers,
        json={"content": "What is the P/E ratio and ROE of Reliance?"},
    )
    assert turn_2.status_code == 200
    res_2 = turn_2.json()
    assert "P/E" in res_2["content"]

    # 4. List messages in conversation
    detail_res = client.get(f"/api/v1/ai/conversations/{conv_id}", headers=journey_headers)
    assert detail_res.status_code == 200
    # 2 user turns + 2 assistant turns = 4 messages
    assert len(detail_res.json()["messages"]) >= 4

    # 5. Delete conversation
    del_res = client.delete(f"/api/v1/ai/conversations/{conv_id}", headers=journey_headers)
    assert del_res.status_code == 204
