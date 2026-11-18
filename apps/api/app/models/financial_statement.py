import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class FinancialStatement(Base):
    """
    Financial statements (Income Statement, Balance Sheet, Cash Flow) for equity instruments.
    Supports both annual and quarterly filings with data provenance and synthetic demo labeling.
    """
    __tablename__ = "financial_statements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Reporting period
    statement_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="annual_consolidated"
    )  # "annual", "quarterly", "income_statement", "balance_sheet", "cash_flow"
    period_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="annual"
    )  # "annual" or "quarterly"
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fiscal_quarter: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0 for annual, 1..4 for quarters
    period_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    filing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Income statement (in currency base unit, e.g. Crores or raw Currency)
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    cost_of_goods_sold: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    operating_expenses: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    operating_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)  # EBIT
    interest_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    tax_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    diluted_shares: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)

    # Balance sheet
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_non_current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_long_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    shareholder_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    book_value_per_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)

    # Cash flow
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    capital_expenditures: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    investing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    financing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)
    net_change_in_cash: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 4), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "period_type",
            "fiscal_year",
            "fiscal_quarter",
            name="uq_financial_statement_period",
        ),
    )

    def __init__(self, **kwargs):
        if "fiscal_quarter" in kwargs and kwargs["fiscal_quarter"] is None:
            kwargs["fiscal_quarter"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<FinancialStatement instrument_id={self.instrument_id} "
            f"period={self.period_type} FY{self.fiscal_year} "
            f"quarter={self.fiscal_quarter} net_income={self.net_income}>"
        )
