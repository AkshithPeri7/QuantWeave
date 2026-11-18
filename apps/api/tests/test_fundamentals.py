"""
Unit tests for fundamental analysis calculations (fundamentals.py) and
synthetic financial fixtures (financial_fixtures.py).
"""

from datetime import date
from decimal import Decimal
import uuid
import pytest
from sqlalchemy.orm import Session

from app.analytics.fundamentals import (
    calculate_statement_ratios,
    FundamentalRatios,
)
from app.models.financial_statement import FinancialStatement
from app.models.instrument import Instrument
from app.providers.demo import DemoMarketDataProvider
from app.providers.financial_fixtures import seed_demo_financial_statements
from app.services.ingestion import seed_demo_market_data


def test_fundamental_ratios_standard_calculation():
    stmt = FinancialStatement(
        instrument_id=uuid.uuid4(),
        statement_type="annual",
        period_type="annual",
        fiscal_year=2024,
        fiscal_quarter=None,
        period_end_date=date(2024, 3, 31),
        currency="INR",
        revenue=Decimal("100000.00"),
        cost_of_goods_sold=Decimal("60000.00"),
        gross_profit=Decimal("40000.00"),
        operating_income=Decimal("25000.00"),
        net_income=Decimal("20000.00"),
        eps=Decimal("50.00"),
        shareholder_equity=Decimal("80000.00"),
        total_debt=Decimal("20000.00"),
        total_current_assets=Decimal("50000.00"),
        total_current_liabilities=Decimal("25000.00"),
        book_value_per_share=Decimal("200.00"),
        operating_cash_flow=Decimal("22000.00"),
        free_cash_flow=Decimal("18000.00"),
    )

    ratios = calculate_statement_ratios(stmt, latest_price=1000.0)

    # Margins
    assert ratios.gross_margin_pct == 40.0  # (40000 / 100000) * 100
    assert ratios.operating_margin_pct == 25.0  # (25000 / 100000) * 100
    assert ratios.net_margin_pct == 20.0  # (20000 / 100000) * 100

    # ROE: (20000 / 80000) * 100 = 25.0%
    assert ratios.roe_pct == 25.0

    # D/E: 20000 / 80000 = 0.25
    assert ratios.debt_to_equity == 0.25

    # Current Ratio: 50000 / 25000 = 2.0
    assert ratios.current_ratio == 2.0

    # Valuation
    assert ratios.pe_ratio == 20.0  # 1000.0 / 50.0
    assert ratios.pb_ratio == 5.0   # 1000.0 / 200.0


def test_fundamental_ratios_zero_division_safeguards():
    # Test zero revenue, negative equity, negative EPS, zero current liabilities
    stmt = FinancialStatement(
        instrument_id=uuid.uuid4(),
        statement_type="annual",
        period_type="annual",
        fiscal_year=2024,
        period_end_date=date(2024, 3, 31),
        currency="INR",
        revenue=Decimal("0.00"),  # zero revenue
        gross_profit=Decimal("0.00"),
        operating_income=Decimal("-5000.00"),
        net_income=Decimal("-8000.00"),  # net loss
        eps=Decimal("-10.00"),  # negative EPS
        shareholder_equity=Decimal("-2000.00"),  # negative equity
        total_debt=Decimal("5000.00"),
        total_current_assets=Decimal("1000.00"),
        total_current_liabilities=Decimal("0.00"),  # zero current liabilities
        book_value_per_share=Decimal("-5.00"),
    )

    ratios = calculate_statement_ratios(stmt, latest_price=150.0)

    # All zero or negative denominators must return None rather than throwing errors
    assert ratios.gross_margin_pct is None
    assert ratios.operating_margin_pct is None
    assert ratios.net_margin_pct is None
    assert ratios.roe_pct is None
    assert ratios.debt_to_equity is None
    assert ratios.current_ratio is None
    assert ratios.pe_ratio is None  # negative EPS -> no P/E
    assert ratios.pb_ratio is None  # negative book value -> no P/B


def test_seed_demo_financial_statements(db_session: Session):
    # Seed market data first so instruments exist
    seed_demo_market_data(db_session)

    count = seed_demo_financial_statements(db_session)
    assert count > 0

    # Check TCS statements
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    stmts = (
        db_session.query(FinancialStatement)
        .filter(FinancialStatement.instrument_id == tcs.id)
        .order_by(FinancialStatement.fiscal_year.asc())
        .all()
    )
    assert len(stmts) >= 3
    # Check that is_synthetic is True for all demo fixtures
    assert all(s.is_synthetic is True for s in stmts)
    # Check that revenues and net income are positive
    fy24 = next(s for s in stmts if s.fiscal_year == 2024 and s.period_type == "annual")
    assert fy24.revenue > 0
    assert fy24.net_income > 0
    assert fy24.gross_profit > 0
