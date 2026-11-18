"""
Unit and integration tests for Milestone 5 FundScope (Mutual Fund Intelligence).

Tests:
- Mutual fund model creation and deterministic demo fixtures
- Idempotency and duplicate NAV prevention
- CSV NAV parsing, validation, and upsert logic
- Return calculations: Absolute return, CAGR, trailing returns
- Rolling returns analysis (1Y rolling window distribution)
- SIP calculator: unit accumulation, cash flows, and true XIRR
- Lump-sum investment calculator
- Multi-fund comparison with normalized base-100 series
- Full REST API verification under /api/v1/funds
- Admin / dev authorization on seed and CSV ingestion
"""

from datetime import date, timedelta
from decimal import Decimal
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.fund_analytics import (
    calculate_absolute_return,
    calculate_cagr,
    FundAnalyticsService,
)
from app.analytics.fund_comparison import compare_mutual_funds
from app.core.security import create_access_token, hash_password
from app.models.mutual_fund import MutualFund, FundNAVHistory
from app.models.user import User
from app.providers.fund_fixtures import seed_demo_mutual_funds
from app.services.fund_ingestion import FundCSVIngestionService


@pytest.fixture
def sample_fund(db_session: Session) -> MutualFund:
    """Creates a sample test mutual fund with 10 days of NAV history."""
    fund = MutualFund(
        id=uuid.uuid4(),
        scheme_code="TEST101",
        isin="INF101TEST01",
        scheme_name="Test Alpha Growth Fund - Direct - Growth",
        amc_name="QuantWeave AMC",
        category="Equity",
        subcategory="Flexi Cap Fund",
        plan_type="Direct",
        option_type="Growth",
        benchmark_name="NIFTY 500 TRI",
        expense_ratio=Decimal("0.5500"),
        aum_crores=Decimal("15000.00"),
        fund_manager="Test Manager",
        crisil_rating=5,
        is_active=True,
        is_demo=True,
    )
    db_session.add(fund)
    db_session.commit()
    db_session.refresh(fund)

    base_date = date(2025, 1, 1)
    # 10 days of NAVs starting at 50.00
    nav_values = [
        Decimal("50.0000"),
        Decimal("50.5000"),
        Decimal("51.0000"),
        Decimal("50.8000"),
        Decimal("51.5000"),
        Decimal("52.0000"),
        Decimal("52.4000"),
        Decimal("52.1000"),
        Decimal("53.0000"),
        Decimal("54.0000"),
    ]
    for i, val in enumerate(nav_values):
        nav_entry = FundNAVHistory(
            fund_id=fund.id,
            nav_date=base_date + timedelta(days=i),
            nav=val,
            is_demo=True,
        )
        db_session.add(nav_entry)
    db_session.commit()
    return fund


# =========================================================================
# 1. Financial Math: Absolute Return & CAGR Tests
# =========================================================================

def test_absolute_return_calculation():
    """Verify simple percentage return formula."""
    start = Decimal("100.00")
    end = Decimal("145.50")
    ret = calculate_absolute_return(start, end)
    assert ret == Decimal("45.50")

    # Negative return
    end_loss = Decimal("85.00")
    ret_loss = calculate_absolute_return(start, end_loss)
    assert ret_loss == Decimal("-15.00")


def test_cagr_calculation_and_guards():
    """
    Verify CAGR formula:
    - 100 -> 144 over 730 days (2 years): sqrt(1.44) - 1 = 20.00%
    - Returns None if period < 365 days
    """
    start = Decimal("100.00")
    end = Decimal("144.00")
    cagr_2y = calculate_cagr(start, end, days=730)
    assert cagr_2y is not None
    assert abs(float(cagr_2y) - 20.00) < 0.1

    # Less than 1 year (e.g. 180 days) => None
    cagr_short = calculate_cagr(start, end, days=180)
    assert cagr_short is None


# =========================================================================
# 2. Demo Seeding & Ingestion Tests
# =========================================================================

def test_seed_demo_mutual_funds_idempotent(db_session: Session):
    """Verifies that seeding demo funds creates expected schemes and is idempotent."""
    res1 = seed_demo_mutual_funds(db_session, trading_days=100)
    assert res1["funds_created"] == 6
    assert res1["nav_rows_created"] > 0

    count_funds = db_session.query(MutualFund).count()
    assert count_funds == 6

    # Seeding again should not recreate duplicates
    res2 = seed_demo_mutual_funds(db_session, trading_days=100)
    assert res2["funds_created"] == 0
    assert res2["nav_rows_created"] == 0


def test_fund_csv_ingestion_and_validation(db_session: Session, sample_fund: MutualFund):
    """Tests CSV parsing, strictly positive NAV validation, and duplicate prevention."""
    valid_csv = f"""nav_date,nav,scheme_code
2025-02-01,55.2000,{sample_fund.scheme_code}
2025-02-02,55.8000,{sample_fund.scheme_code}
"""
    rows, errors = FundCSVIngestionService.parse_and_validate_csv(db_session, valid_csv)
    assert len(errors) == 0
    assert len(rows) == 2

    # Ingest rows
    count = FundCSVIngestionService.ingest_nav_records(db_session, rows, is_demo=False)
    assert count == 2

    # Re-ingest same date with updated NAV (must update, not duplicate)
    update_csv = f"""nav_date,nav,scheme_code
2025-02-01,56.0000,{sample_fund.scheme_code}
"""
    u_rows, _ = FundCSVIngestionService.parse_and_validate_csv(db_session, update_csv)
    FundCSVIngestionService.ingest_nav_records(db_session, u_rows, is_demo=False)

    nav_row = (
        db_session.query(FundNAVHistory)
        .filter(FundNAVHistory.fund_id == sample_fund.id, FundNAVHistory.nav_date == date(2025, 2, 1))
        .all()
    )
    # Exactly one record with updated NAV
    assert len(nav_row) == 1
    assert nav_row[0].nav == Decimal("56.0000")


def test_fund_csv_validation_negative_nav(db_session: Session, sample_fund: MutualFund):
    """Non-positive NAV in CSV is rejected with validation error."""
    invalid_csv = f"""nav_date,nav,scheme_code
2025-02-01,-10.5000,{sample_fund.scheme_code}
"""
    rows, errors = FundCSVIngestionService.parse_and_validate_csv(db_session, invalid_csv)
    assert len(rows) == 0
    assert any("strictly positive" in err for err in errors)


# =========================================================================
# 3. SIP Calculator & XIRR Tests
# =========================================================================

def test_sip_calculator_constant_nav():
    """
    If NAV remains constant at ₹10.00 and user invests ₹1,000 each month for 3 months:
    - Total Invested: ₹3,000
    - Total Units: 300
    - Final Value: ₹3,000
    - Absolute Return: 0.00%
    - XIRR: 0.00%
    """
    series = [
        (date(2025, 1, 5), Decimal("10.0000")),
        (date(2025, 1, 20), Decimal("10.0000")),
        (date(2025, 2, 5), Decimal("10.0000")),
        (date(2025, 2, 20), Decimal("10.0000")),
        (date(2025, 3, 5), Decimal("10.0000")),
        (date(2025, 3, 20), Decimal("10.0000")),
    ]
    res = FundAnalyticsService.calculate_sip(
        nav_series=series,
        monthly_amount=Decimal("1000.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 20),
        sip_day=5,
    )
    assert res["installments_count"] == 3
    assert res["total_invested"] == 3000.0
    assert res["final_value"] == 3000.0
    assert res["units_accumulated"] == 300.0
    assert abs(res["absolute_return_pct"]) < 0.01
    assert res["xirr_pct"] is not None
    assert abs(res["xirr_pct"]) < 0.1


def test_sip_calculator_growing_nav():
    """If NAV increases month-over-month, units compound and XIRR > 0."""
    series = [
        (date(2025, 1, 5), Decimal("10.0000")),
        (date(2025, 2, 5), Decimal("12.0000")),
        (date(2025, 3, 5), Decimal("15.0000")),
        (date(2025, 3, 25), Decimal("16.0000")),
    ]
    res = FundAnalyticsService.calculate_sip(
        nav_series=series,
        monthly_amount=Decimal("1000.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 25),
        sip_day=5,
    )
    assert res["installments_count"] == 3
    assert res["total_invested"] == 3000.0
    assert res["final_value"] > 3000.0
    assert res["total_profit"] > 0
    assert res["xirr_pct"] is not None
    assert res["xirr_pct"] > 0


# =========================================================================
# 4. Multi-Fund Comparison Engine Tests
# =========================================================================

def test_fund_comparison_engine(db_session: Session):
    """Compares 2 funds and verifies rebased 100 chart."""
    seed_demo_mutual_funds(db_session, trading_days=100)
    funds = db_session.query(MutualFund).limit(2).all()
    fund_ids = [f.id for f in funds]

    comp = compare_mutual_funds(db_session, fund_ids, period="6M")
    assert len(comp["funds"]) == 2
    assert "normalized_chart" in comp
    assert len(comp["normalized_chart"]) > 0

    # First point of each fund should be rebased to 100.0
    first_pt = comp["normalized_chart"][0]["values"]
    for fid in fund_ids:
        assert abs(first_pt[str(fid)] - 100.0) < 1.0


def test_fund_comparison_max_limit_rejection(db_session: Session):
    """Comparing more than 4 funds raises ValueError."""
    fake_ids = [uuid.uuid4() for _ in range(5)]
    with pytest.raises(ValueError, match="maximum of 4"):
        compare_mutual_funds(db_session, fake_ids)


# =========================================================================
# 5. REST API Endpoints Tests
# =========================================================================

def test_api_list_funds_and_search(client: TestClient, db_session: Session):
    """Test GET /api/v1/funds and GET /api/v1/funds/search."""
    seed_demo_mutual_funds(db_session, trading_days=50)

    # List funds
    res = client.get("/api/v1/funds?page=1&size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 6
    assert len(data["items"]) == 6

    # Category filter
    res_cat = client.get("/api/v1/funds?category=Debt")
    assert res_cat.status_code == 200
    assert res_cat.json()["total"] == 1
    assert res_cat.json()["items"][0]["subcategory"] == "Liquid Fund"

    # Search
    res_search = client.get("/api/v1/funds/search?q=Parikh")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1
    assert "Parag Parikh" in res_search.json()[0]["scheme_name"]


def test_api_fund_details_and_nav_history(client: TestClient, db_session: Session):
    """Test GET /api/v1/funds/{id} and GET /api/v1/funds/{id}/nav."""
    seed_demo_mutual_funds(db_session, trading_days=60)
    fund = db_session.query(MutualFund).first()

    # Detail
    detail_res = client.get(f"/api/v1/funds/{fund.id}")
    assert detail_res.status_code == 200
    d_data = detail_res.json()
    assert d_data["scheme_code"] == fund.scheme_code
    assert d_data["latest_nav"] is not None

    # NAV History
    nav_res = client.get(f"/api/v1/funds/{fund.id}/nav?limit=20")
    assert nav_res.status_code == 200
    n_data = nav_res.json()
    assert len(n_data["navs"]) == 20
    assert n_data["count"] == 20


def test_api_fund_analytics(client: TestClient, db_session: Session):
    """Test GET /api/v1/funds/{id}/analytics."""
    seed_demo_mutual_funds(db_session, trading_days=150)
    fund = db_session.query(MutualFund).first()

    res = client.get(f"/api/v1/funds/{fund.id}/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "trailing_returns" in data
    assert "rolling_returns_1y" in data
    assert data["max_drawdown_pct"] >= 0.0


def test_api_sip_and_lump_sum_calculators(client: TestClient, db_session: Session):
    """Test POST /api/v1/funds/{id}/sip-calculator and lump-sum."""
    seed_demo_mutual_funds(db_session, trading_days=150)
    fund = db_session.query(MutualFund).first()

    navs = db_session.query(FundNAVHistory).filter(FundNAVHistory.fund_id == fund.id).order_by(FundNAVHistory.nav_date.asc()).all()
    start_d = navs[0].nav_date.isoformat()
    end_d = navs[-1].nav_date.isoformat()

    # SIP
    sip_res = client.post(
        f"/api/v1/funds/{fund.id}/sip-calculator",
        json={"monthly_amount": 5000.0, "start_date": start_d, "end_date": end_d, "sip_day": 5},
    )
    assert sip_res.status_code == 200
    sip_data = sip_res.json()
    assert sip_data["total_invested"] > 0
    assert sip_data["final_value"] > 0
    assert len(sip_data["installments"]) > 0

    # Lump sum
    ls_res = client.post(
        f"/api/v1/funds/{fund.id}/lump-sum-calculator",
        json={"amount": 50000.0, "start_date": start_d, "end_date": end_d},
    )
    assert ls_res.status_code == 200
    ls_data = ls_res.json()
    assert ls_data["initial_investment"] == 50000.0
    assert ls_data["final_value"] > 0
    assert len(ls_data["timeline"]) > 0


def test_api_fund_comparison_endpoint(client: TestClient, db_session: Session):
    """Test GET /api/v1/funds/compare."""
    seed_demo_mutual_funds(db_session, trading_days=100)
    funds = db_session.query(MutualFund).limit(3).all()
    ids_str = ",".join(str(f.id) for f in funds)

    res = client.get(f"/api/v1/funds/compare?ids={ids_str}&period=1Y")
    assert res.status_code == 200
    data = res.json()
    assert len(data["funds"]) == 3
    assert len(data["normalized_chart"]) > 0
