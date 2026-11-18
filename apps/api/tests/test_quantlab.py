"""
Integration and Unit Tests for QuantLab Strategy Research & Backtesting Engine.

Tests:
- Strategy parameter validation & bounds checks
- Chronological execution, next-bar Open pricing, fees, and slippage
- Strictly long-only equity accounting (no negative cash, no shorting)
- Quantitative risk metrics (CAGR, Sharpe, Sortino, Max Drawdown)
- Parameter grid search with train/test split and overfitting detection
- Authenticated REST API endpoints under /api/v1/quantlab
- User isolation across strategies and backtest runs
"""

from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.backtesting import (
    BacktestEngine,
    BuyAndHoldStrategy,
    EMACrossoverStrategy,
    RSIThresholdStrategy,
    SMACrossoverStrategy,
    run_parameter_grid_search,
)
from app.analytics.quant_metrics import calculate_backtest_metrics
from app.models.data_source import DataSource
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory
from app.models.user import User


# ==========================================
# Helpers & Fixtures
# ==========================================

@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def other_user(db_session: Session) -> User:
    from app.core.security import hash_password
    user = User(
        name="Other Analyst",
        email="other@quantweave.test",
        password_hash=hash_password("OtherPassword123!"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_instrument(db_session: Session) -> Instrument:
    ds = DataSource(provider_name="TestNSE", dataset="equities")
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    inst = Instrument(
        symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        exchange="NSE",
        instrument_type="equity",
        sector="Energy",
        currency="INR",
        is_active=True,
        is_demo=True,
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    # Insert 60 bars of synthetic prices with a clear upward trend followed by pullback
    base_date = date(2024, 1, 1)
    base_price = 2000.0

    for i in range(60):
        t_date = base_date + timedelta(days=i)
        # Upward wave then pullback
        drift = i * 15.0 if i < 40 else (40 * 15.0 - (i - 40) * 20.0)
        p_close = base_price + drift
        p_open = p_close - 5.0
        p_high = p_close + 10.0
        p_low = p_close - 10.0
        p_vol = 50000 + i * 100

        bar = PriceHistory(
            instrument_id=inst.id,
            provider_id=ds.id,
            trade_date=t_date,
            open=Decimal(str(round(p_open, 2))),
            high=Decimal(str(round(p_high, 2))),
            low=Decimal(str(round(p_low, 2))),
            close=Decimal(str(round(p_close, 2))),
            volume=p_vol,
        )
        db_session.add(bar)

    db_session.commit()
    return inst


# ==========================================
# 1. Parameter Validation Tests
# ==========================================

def test_sma_parameter_validation():
    # Valid
    p = SMACrossoverStrategy.validate_parameters({"fast_period": 20, "slow_period": 50})
    assert p["fast_period"] == 20
    assert p["slow_period"] == 50

    # Invalid: fast >= slow
    with pytest.raises(ValueError, match="strictly less than slow_period"):
        SMACrossoverStrategy.validate_parameters({"fast_period": 50, "slow_period": 20})

    # Invalid: fast < 2
    with pytest.raises(ValueError, match="between 2 and 500"):
        SMACrossoverStrategy.validate_parameters({"fast_period": 1, "slow_period": 20})


def test_rsi_parameter_validation():
    # Valid
    p = RSIThresholdStrategy.validate_parameters({
        "rsi_period": 14,
        "oversold_threshold": 30,
        "overbought_threshold": 70,
    })
    assert p["rsi_period"] == 14
    assert p["oversold_threshold"] == 30.0

    # Invalid: oversold >= overbought
    with pytest.raises(ValueError, match="must be less than overbought_threshold"):
        RSIThresholdStrategy.validate_parameters({
            "rsi_period": 14,
            "oversold_threshold": 75,
            "overbought_threshold": 70,
        })


def test_buy_and_hold_parameter_validation():
    # Buy & Hold takes any or empty dict
    p = BuyAndHoldStrategy.validate_parameters({})
    assert p == {}


# ==========================================
# 2. Backtest Engine Execution Tests
# ==========================================

def test_next_bar_open_execution_and_fees():
    """
    Verifies that a signal emitted at bar t close executes strictly on bar t+1 at Open price,
    with fees and slippage correctly deducted.
    """
    df = pd.DataFrame([
        {"trade_date": date(2024, 1, 1), "open": 100.0, "high": 105.0, "low": 99.0, "close": 101.0, "volume": 1000},
        {"trade_date": date(2024, 1, 2), "open": 102.0, "high": 108.0, "low": 101.0, "close": 107.0, "volume": 1000},
        {"trade_date": date(2024, 1, 3), "open": 108.0, "high": 112.0, "low": 106.0, "close": 110.0, "volume": 1000},
        {"trade_date": date(2024, 1, 4), "open": 111.0, "high": 115.0, "low": 109.0, "close": 114.0, "volume": 1000},
    ])

    result = BacktestEngine.run_backtest(
        df=df,
        strategy_cls=BuyAndHoldStrategy,
        parameters={},
        starting_capital=10000.0,
        fee_rate=0.001,  # 0.1%
        slippage_bps=10.0,  # 0.1% slippage
    )

    trades = result["trades"]
    # Buy & Hold generates BUY signal on bar 0 (2024-01-01), which must execute on bar 1 (2024-01-02) at Open
    assert len(trades) >= 1
    first_trade = trades[0]
    assert first_trade["side"] == "BUY"
    assert first_trade["signal_date"] == date(2024, 1, 1)
    assert first_trade["execution_date"] == date(2024, 1, 2)

    # Bar 1 open is 102.0. Slippage = 10 bps (0.1%), so execution_price = 102.0 * 1.001 = 102.102
    assert abs(first_trade["execution_price"] - 102.102) < 1e-3
    assert first_trade["fees"] > 0
    assert first_trade["slippage_cost"] > 0
    # Long only constraint: cash after must never be negative
    assert first_trade["cash_after"] >= 0


def test_long_only_and_cash_protection():
    """
    Verifies that the engine prevents negative cash and unauthorized shorting.
    """
    df = pd.DataFrame([
        {"trade_date": date(2024, 1, 1), "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000},
        {"trade_date": date(2024, 1, 2), "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000},
        {"trade_date": date(2024, 1, 3), "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000},
    ])

    result = BacktestEngine.run_backtest(
        df=df,
        strategy_cls=BuyAndHoldStrategy,
        parameters={},
        starting_capital=500.0,  # Small capital
        fee_rate=0.005,
        slippage_bps=5.0,
    )

    for pt in result["equity_curve"]:
        assert pt["cash"] >= 0
        assert pt["position_value"] >= 0
        assert pt["equity"] > 0


# ==========================================
# 3. Quantitative Risk Metrics Tests
# ==========================================

def test_flat_metrics_safely_handled():
    metrics = calculate_backtest_metrics([], [], starting_capital=100000.0)
    assert metrics["starting_capital"] == 100000.0
    assert metrics["ending_equity"] == 100000.0
    assert metrics["total_return_pct"] == 0.0
    assert metrics["cagr_pct"] is None
    assert metrics["sharpe_ratio"] is None
    assert metrics["total_trades"] == 0


def test_cagr_guard_under_365_days():
    # 30 days history
    equity_series = [
        {"point_date": date(2024, 1, 1), "equity": 100000.0, "drawdown_pct": 0.0, "benchmark_equity": 100000.0},
        {"point_date": date(2024, 1, 30), "equity": 110000.0, "drawdown_pct": 0.0, "benchmark_equity": 105000.0},
    ]
    metrics = calculate_backtest_metrics(equity_series, [], starting_capital=100000.0)
    # Under 365 days, CAGR must be None to prevent misleading annualized projection
    assert metrics["cagr_pct"] is None
    assert metrics["total_return_pct"] == 10.0


# ==========================================
# 4. Parameter Grid Search & Overfitting Tests
# ==========================================

def test_grid_search_max_combinations_limit():
    df = pd.DataFrame([
        {"trade_date": date(2024, 1, i + 1), "open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0, "volume": 1000}
        for i in range(30)
    ])

    # 6 * 5 = 30 combinations > 25 limit
    large_grid = {
        "fast_period": [5, 10, 15, 20, 25, 30],
        "slow_period": [40, 50, 60, 70, 80],
    }

    with pytest.raises(ValueError, match="exceeds maximum allowed limit of 25"):
        run_parameter_grid_search(
            df=df,
            strategy_cls=SMACrossoverStrategy,
            param_grid=large_grid,
        )


def test_grid_search_in_sample_out_of_sample_split():
    df = pd.DataFrame([
        {"trade_date": date(2024, 1, 1) + timedelta(days=i), "open": 100.0 + i, "high": 105.0 + i, "low": 95.0 + i, "close": 101.0 + i, "volume": 1000}
        for i in range(40)
    ])

    small_grid = {
        "fast_period": [3, 5],
        "slow_period": [10, 15],
    }

    result = run_parameter_grid_search(
        df=df,
        strategy_cls=SMACrossoverStrategy,
        param_grid=small_grid,
        starting_capital=100000.0,
        train_ratio=0.7,
    )

    assert result["combinations_tested"] == 4
    assert len(result["results"]) == 4
    for r in result["results"]:
        assert "in_sample_return_pct" in r
        assert "out_of_sample_return_pct" in r
        assert "overfitting_warning" in r


# ==========================================
# 5. REST API Integration Tests
# ==========================================

def test_strategy_crud_and_user_isolation(
    client: TestClient,
    auth_headers: dict,
    other_user: User,
    db_session: Session,
):
    # 1. Create Strategy
    payload = {
        "name": "Nifty Momentum SMA",
        "description": "50/200 crossover for educational purposes",
        "strategy_type": "SMA_CROSSOVER",
        "parameters": {"fast_period": 20, "slow_period": 50},
    }
    res = client.post("/api/v1/quantlab/strategies", json=payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    data = res.json()
    strategy_id = data["id"]
    assert data["name"] == "Nifty Momentum SMA"
    assert data["version"] == 1

    # 2. List Strategies
    res = client.get("/api/v1/quantlab/strategies", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 3. Get Strategy
    res = client.get(f"/api/v1/quantlab/strategies/{strategy_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == strategy_id

    # 4. Update Strategy (version bump)
    up_payload = {"name": "Updated Momentum SMA", "parameters": {"fast_period": 10, "slow_period": 30}}
    res = client.put(f"/api/v1/quantlab/strategies/{strategy_id}", json=up_payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Momentum SMA"
    assert res.json()["version"] == 2

    # 5. Cross-user isolation: other user cannot view or delete
    from app.core.security import create_access_token
    other_token = create_access_token(subject=str(other_user.id), claims={"email": other_user.email, "role": other_user.role})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    res = client.get(f"/api/v1/quantlab/strategies/{strategy_id}", headers=other_headers)
    assert res.status_code == 404

    # 6. Delete Strategy
    res = client.delete(f"/api/v1/quantlab/strategies/{strategy_id}", headers=auth_headers)
    assert res.status_code == 204


def test_instant_backtest_execution(
    client: TestClient,
    auth_headers: dict,
    sample_instrument: Instrument,
):
    payload = {
        "strategy_type": "BUY_AND_HOLD",
        "parameters": {},
        "instrument_id": str(sample_instrument.id),
        "start_date": "2024-01-01",
        "end_date": "2024-02-15",
        "starting_capital": 100000.0,
        "fee_rate": 0.001,
        "slippage_bps": 5.0,
    }
    res = client.post("/api/v1/quantlab/backtest/instant", json=payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    run = res.json()
    run_id = run["id"]
    assert run["status"] == "COMPLETED"
    assert run["metrics"] is not None
    assert "total_return_pct" in run["metrics"]

    # Check trades endpoint
    res = client.get(f"/api/v1/quantlab/runs/{run_id}/trades", headers=auth_headers)
    assert res.status_code == 200
    trades = res.json()
    assert len(trades) >= 1
    assert trades[0]["side"] == "BUY"

    # Check equity curve endpoint
    res = client.get(f"/api/v1/quantlab/runs/{run_id}/equity", headers=auth_headers)
    assert res.status_code == 200
    equity_pts = res.json()
    assert len(equity_pts) >= 2


def test_saved_strategy_backtest_and_comparison(
    client: TestClient,
    auth_headers: dict,
    sample_instrument: Instrument,
):
    # 1. Create Strategy
    strat_res = client.post(
        "/api/v1/quantlab/strategies",
        json={
            "name": "Reliance RSI Strategy",
            "strategy_type": "RSI_THRESHOLD",
            "parameters": {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70},
        },
        headers=auth_headers,
    )
    assert strat_res.status_code == 201
    strat_id = strat_res.json()["id"]

    # 2. Run Backtest on Saved Strategy
    bt_res1 = client.post(
        f"/api/v1/quantlab/strategies/{strat_id}/backtest",
        json={
            "instrument_id": str(sample_instrument.id),
            "start_date": "2024-01-01",
            "end_date": "2024-02-15",
            "starting_capital": 100000.0,
            "fee_rate": 0.001,
            "slippage_bps": 5.0,
        },
        headers=auth_headers,
    )
    assert bt_res1.status_code == 201
    run1_id = bt_res1.json()["id"]

    # 3. Run a second instant run for comparison
    bt_res2 = client.post(
        "/api/v1/quantlab/backtest/instant",
        json={
            "strategy_type": "BUY_AND_HOLD",
            "parameters": {},
            "instrument_id": str(sample_instrument.id),
            "start_date": "2024-01-01",
            "end_date": "2024-02-15",
            "starting_capital": 100000.0,
            "fee_rate": 0.001,
            "slippage_bps": 5.0,
        },
        headers=auth_headers,
    )
    assert bt_res2.status_code == 201
    run2_id = bt_res2.json()["id"]

    # 4. Compare runs
    comp_res = client.post(
        "/api/v1/quantlab/runs/compare",
        json={"run_ids": [run1_id, run2_id]},
        headers=auth_headers,
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["runs"]) == 2
    assert comp_data["runs"][0]["metrics"] is not None


def test_grid_search_api_endpoint(
    client: TestClient,
    auth_headers: dict,
    sample_instrument: Instrument,
):
    payload = {
        "strategy_type": "SMA_CROSSOVER",
        "param_grid": {
            "fast_period": [5, 10],
            "slow_period": [15, 20],
        },
        "instrument_id": str(sample_instrument.id),
        "start_date": "2024-01-01",
        "end_date": "2024-02-15",
        "starting_capital": 100000.0,
        "fee_rate": 0.001,
        "slippage_bps": 5.0,
        "train_ratio": 0.7,
    }

    res = client.post("/api/v1/quantlab/experiments/grid-search", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["combinations_tested"] == 4
    assert len(data["results"]) == 4
    assert data["strategy_type"] == "SMA_CROSSOVER"
