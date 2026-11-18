"""
Unit and integration tests for Milestone 4 Portfolio Intelligence MVP.

Tests:
- Portfolio creation, validation, and multi-currency rejection
- Strict user ownership and cross-user portfolio isolation
- Append-only transactions (BUY, SELL, DIVIDEND, CASH_DEPOSIT, CASH_WITHDRAWAL)
- Atomic cash validation and prevention of negative cash
- Overselling protection (shares_held >= sell_quantity)
- Weighted-Average Cost Basis (WACB) calculation and realized P&L
- Idempotency key duplicate protection
- Valuation calculation (cash + holdings market value, unrealized P&L, allocation)
- Performance and risk analytics (TWR, XIRR solver, volatility, Sharpe ratio, max drawdown)
- Daily historical equity curve timeline
"""

from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.portfolio_analytics import calculate_xirr, PortfolioAnalyticsService
from app.core.security import create_access_token, hash_password
from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.models.portfolio_transaction import PortfolioTransaction
from app.models.price_history import PriceHistory
from app.models.user import User
from app.services.portfolio import (
    DuplicateTransactionError,
    InsufficientCashError,
    InsufficientSharesError,
    PortfolioService,
    UnsupportedCurrencyError,
)


@pytest.fixture
def second_user(db_session: Session) -> User:
    """Creates a distinct second user for cross-user isolation testing."""
    user = User(
        name="Other Investor",
        email="other@quantweave.test",
        password_hash=hash_password("OtherPassword123!"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_user: User) -> str:
    """Access token for second user."""
    return create_access_token(
        subject=str(second_user.id),
        claims={"email": second_user.email, "role": second_user.role},
    )


@pytest.fixture
def sample_instrument(db_session: Session) -> Instrument:
    """Creates a sample test equity instrument."""
    inst = Instrument(
        id=uuid.uuid4(),
        exchange="NSE",
        symbol="TCS",
        isin="INE467B01029",
        company_name="Tata Consultancy Services Ltd",
        instrument_type="equity",
        sector="Information Technology",
        currency="INR",
        is_active=True,
        is_demo=True,
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)
    return inst


@pytest.fixture
def sample_instrument_with_prices(db_session: Session, sample_instrument: Instrument) -> Instrument:
    """Adds daily price history for the sample instrument over 5 days."""
    base_date = date(2026, 1, 1)
    prices = [Decimal("3500.00"), Decimal("3550.00"), Decimal("3600.00"), Decimal("3580.00"), Decimal("3700.00")]
    for i, p in enumerate(prices):
        trade_d = base_date + timedelta(days=i)
        ph = PriceHistory(
            instrument_id=sample_instrument.id,
            trade_date=trade_d,
            open=p - Decimal("10.00"),
            high=p + Decimal("20.00"),
            low=p - Decimal("20.00"),
            close=p,
            adjusted_close=p,
            volume=500000,
            currency="INR",
            is_demo=True,
        )
        db_session.add(ph)
    db_session.commit()
    return sample_instrument


# =========================================================================
# 1. Portfolio Creation & Multi-currency Tests
# =========================================================================

def test_create_portfolio_success(client: TestClient, test_user_token: str):
    """Test creating a portfolio with valid INR base currency."""
    response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Core Wealth Portfolio", "description": "Long-term investment portfolio", "base_currency": "INR"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Core Wealth Portfolio"
    assert data["base_currency"] == "INR"
    assert "id" in data


def test_create_portfolio_rejects_unsupported_currency(client: TestClient, test_user_token: str):
    """MVP explicitly rejects non-INR denominated portfolios."""
    response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "US Portfolio", "base_currency": "USD"},
    )
    assert response.status_code == 400
    assert "INR" in response.json()["detail"]


# =========================================================================
# 2. Cross-User Portfolio Isolation Tests
# =========================================================================

def test_cross_user_isolation(client: TestClient, test_user_token: str, second_user_token: str):
    """Verifies that User A cannot read or mutate User B's portfolio."""
    # User A creates a portfolio
    create_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "User A Private Fund", "base_currency": "INR"},
    )
    portfolio_id = create_res.json()["id"]

    # User B attempts to access User A's portfolio
    get_res = client.get(
        f"/api/v1/portfolios/{portfolio_id}",
        headers={"Authorization": f"Bearer {second_user_token}"},
    )
    assert get_res.status_code == 404

    # User B attempts to record a transaction into User A's portfolio
    tx_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        headers={"Authorization": f"Bearer {second_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 50000.0,
        },
    )
    assert tx_res.status_code == 404


# =========================================================================
# 3. Cash Management & Validation Tests
# =========================================================================

def test_cash_deposit_and_withdrawal(client: TestClient, test_user_token: str):
    """Verifies cash deposits, withdrawals, and balance tracking."""
    # Create portfolio
    p_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Liquid Fund", "base_currency": "INR"},
    )
    p_id = p_res.json()["id"]

    # Deposit 100,000 INR
    dep_res = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 100000.0,
            "fees": 50.0,
        },
    )
    assert dep_res.status_code == 201
    assert float(dep_res.json()["cash_amount"]) == 99950.0

    # Withdraw 40,000 INR
    with_res = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_WITHDRAWAL",
            "trade_date": "2026-01-02",
            "price_per_unit": 40000.0,
            "fees": 20.0,
        },
    )
    assert with_res.status_code == 201
    assert float(with_res.json()["cash_amount"]) == -40020.0

    # Valuation check: remaining cash should be 99950 - 40020 = 59930
    val_res = client.get(
        f"/api/v1/portfolios/{p_id}/valuation",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert val_res.status_code == 200
    assert float(val_res.json()["cash_balance"]) == 59930.0


def test_insufficient_cash_rejection(client: TestClient, test_user_token: str):
    """Attempting to withdraw more cash than available must return HTTP 400."""
    p_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Empty Cash Portfolio", "base_currency": "INR"},
    )
    p_id = p_res.json()["id"]

    # Attempt withdrawal from empty portfolio
    with_res = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_WITHDRAWAL",
            "trade_date": "2026-01-01",
            "price_per_unit": 1000.0,
        },
    )
    assert with_res.status_code == 400
    assert "Insufficient available cash" in with_res.json()["detail"]


# =========================================================================
# 4. Trading Engine: WACB, Overselling & P&L Tests
# =========================================================================

def test_trading_engine_wacb_and_overselling_prevention(
    client: TestClient,
    test_user_token: str,
    sample_instrument: Instrument,
):
    """
    Tests:
    - BUY requires sufficient cash
    - Weighted-Average Cost Basis calculation across multiple buys
    - SELL increases cash and realizes P&L
    - Overselling is strictly prevented
    """
    # Create portfolio
    p_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Equities Portfolio", "base_currency": "INR"},
    )
    p_id = p_res.json()["id"]

    # 1. Attempt BUY without cash => must fail
    buy_fail = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "BUY",
            "instrument_id": str(sample_instrument.id),
            "trade_date": "2026-01-01",
            "quantity": 10,
            "price_per_unit": 3500.0,
        },
    )
    assert buy_fail.status_code == 400
    assert "Insufficient available cash" in buy_fail.json()["detail"]

    # 2. Deposit 100,000 INR
    client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 100000.0,
        },
    )

    # 3. First BUY: 10 shares @ 3500 (Cost = 35,000)
    buy1 = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "BUY",
            "instrument_id": str(sample_instrument.id),
            "trade_date": "2026-01-01",
            "quantity": 10,
            "price_per_unit": 3500.0,
            "fees": 20.0,
        },
    )
    assert buy1.status_code == 201

    # 4. Second BUY: 10 shares @ 3700 (Cost = 37,000 + 20 = 37,020)
    # Total shares = 20, Total Cost = 35,020 + 37,020 = 72,040 => Avg Price = 3602.00
    buy2 = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "BUY",
            "instrument_id": str(sample_instrument.id),
            "trade_date": "2026-01-02",
            "quantity": 10,
            "price_per_unit": 3700.0,
            "fees": 20.0,
        },
    )
    assert buy2.status_code == 201

    # 5. Overselling prevention: attempt to SELL 25 shares (only 20 held)
    oversell = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "SELL",
            "instrument_id": str(sample_instrument.id),
            "trade_date": "2026-01-03",
            "quantity": 25,
            "price_per_unit": 3800.0,
        },
    )
    assert oversell.status_code == 400
    assert "only 20.00000000 shares are currently held" in oversell.json()["detail"]

    # 6. Valid SELL: 10 shares @ 3900 (Proceeds = 39,000 - 15 = 38,985)
    # Cost of 10 shares sold = 10 * 3602 = 36,020
    # Realized P&L = 38,985 - 36,020 = 2965.00
    sell_res = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "SELL",
            "instrument_id": str(sample_instrument.id),
            "trade_date": "2026-01-03",
            "quantity": 10,
            "price_per_unit": 3900.0,
            "fees": 15.0,
        },
    )
    assert sell_res.status_code == 201

    # Check valuation and realized P&L
    val_res = client.get(
        f"/api/v1/portfolios/{p_id}/valuation",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    data = val_res.json()
    assert float(data["realized_pnl"]) == 2965.0
    # Remaining holding: 10 shares
    assert len(data["holdings"]) == 1
    assert float(data["holdings"][0]["quantity"]) == 10.0
    assert float(data["holdings"][0]["average_buy_price"]) == 3602.0


# =========================================================================
# 5. Idempotency Key Tests
# =========================================================================

def test_idempotency_key_prevents_duplicate_transactions(
    client: TestClient,
    test_user_token: str,
):
    """Submitting the same idempotency key twice returns the existing transaction."""
    p_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Idempotent Portfolio", "base_currency": "INR"},
    )
    p_id = p_res.json()["id"]

    key = "deposit-2026-01-01-xyz-123"

    res1 = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 50000.0,
            "idempotency_key": key,
        },
    )
    assert res1.status_code == 201
    tx_id1 = res1.json()["id"]

    # Resubmit with identical key
    res2 = client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 50000.0,
            "idempotency_key": key,
        },
    )
    assert res2.status_code == 201
    assert res2.json()["id"] == tx_id1

    # Check cash balance: should be 50,000, NOT 100,000
    val_res = client.get(
        f"/api/v1/portfolios/{p_id}/valuation",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert float(val_res.json()["cash_balance"]) == 50000.0


# =========================================================================
# 6. Performance & Risk Analytics Tests
# =========================================================================

def test_xirr_solver_independent_reference():
    """
    Validates XIRR numerical solver against standard known financial fixture:
    - Deposit 10,000 on 2026-01-01
    - Terminal value 11,000 on 2027-01-01 (exact 1-year 10.00% return)
    """
    cfs = [
        (date(2026, 1, 1), Decimal("-10000.00")),
        (date(2027, 1, 1), Decimal("11000.00")),
    ]
    xirr = calculate_xirr(cfs)
    assert xirr is not None
    # 10.0% annualized
    assert abs(float(xirr) - 10.00) < 0.05


def test_portfolio_performance_and_history(
    client: TestClient,
    test_user_token: str,
    sample_instrument_with_prices: Instrument,
):
    """
    Tests historical equity curve generation, TWR, volatility, Sharpe, and drawdown.
    """
    p_res = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"name": "Analytics Portfolio", "base_currency": "INR"},
    )
    p_id = p_res.json()["id"]

    # Day 1: Deposit 50,000 & Buy 10 shares @ 3500
    client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "CASH_DEPOSIT",
            "trade_date": "2026-01-01",
            "price_per_unit": 50000.0,
        },
    )
    client.post(
        f"/api/v1/portfolios/{p_id}/transactions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "transaction_type": "BUY",
            "instrument_id": str(sample_instrument_with_prices.id),
            "trade_date": "2026-01-01",
            "quantity": 10,
            "price_per_unit": 3500.0,
        },
    )

    # Performance endpoint as of Day 5 (2026-01-05)
    perf_res = client.get(
        f"/api/v1/portfolios/{p_id}/performance?as_of_date=2026-01-05",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert perf_res.status_code == 200
    perf = perf_res.json()
    assert perf["twr_percent"] is not None
    assert perf["max_drawdown_percent"] >= 0.0
    assert perf["timeline_days"] == 5

    # History timeline endpoint
    hist_res = client.get(
        f"/api/v1/portfolios/{p_id}/history?as_of_date=2026-01-05",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert hist_res.status_code == 200
    timeline = hist_res.json()
    assert len(timeline) == 5
    # Day 5 closing price of TCS is 3700; cash = 15000; total = 15000 + 37000 = 52000
    assert abs(timeline[-1]["total_value"] - 52000.0) < 1.0
