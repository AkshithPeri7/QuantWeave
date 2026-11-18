"""
SQLAlchemy models for Mutual Fund Intelligence (FundScope).

Implements:
- MutualFund: AMC, scheme details, plan type (Direct/Regular), option (Growth/IDCW), benchmark, expense ratio
- FundNAVHistory: Historical Net Asset Values with strict NUMERIC precision and unique date constraint
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MutualFund(Base):
    __tablename__ = "mutual_funds"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scheme_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="AMFI scheme code or unique identifier, e.g. '122639'",
    )
    isin: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    scheme_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Full scheme name, e.g. 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth'",
    )
    amc_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Asset Management Company / Fund House, e.g. 'PPFAS Mutual Fund'",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Broad asset category: Equity, Debt, Hybrid, Solution Oriented, Other",
    )
    subcategory: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="SEBI scheme subcategory: Flexi Cap, Large Cap, Mid Cap, Liquid, etc.",
    )
    plan_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Direct",
        doc="Direct or Regular plan",
    )
    option_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Growth",
        doc="Growth or IDCW (Income Distribution cum Capital Withdrawal)",
    )
    benchmark_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        doc="Benchmark index name, e.g. 'NIFTY 500 TRI'",
    )
    expense_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        doc="Total expense ratio percentage, e.g. 0.6500 for 0.65%",
    )
    aum_crores: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        doc="Assets Under Management in INR Crores",
    )
    fund_manager: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    crisil_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="1 to 5 star rating",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="True if synthetic/demo fixture, False if real market data",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    nav_history: Mapped[List["FundNAVHistory"]] = relationship(
        "FundNAVHistory",
        back_populates="fund",
        cascade="all, delete-orphan",
        order_by="FundNAVHistory.nav_date.desc()",
    )

    __table_args__ = (
        Index("ix_mutual_funds_cat_subcat", "category", "subcategory"),
        Index("ix_mutual_funds_amc", "amc_name"),
    )

    def __repr__(self) -> str:
        return f"<MutualFund code={self.scheme_code} name='{self.scheme_name}'>"


class FundNAVHistory(Base):
    __tablename__ = "fund_nav_history"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    fund_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mutual_funds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nav_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    nav: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        doc="Net Asset Value per unit in INR",
    )
    repurchase_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    fund: Mapped["MutualFund"] = relationship("MutualFund", back_populates="nav_history")

    __table_args__ = (
        UniqueConstraint("fund_id", "nav_date", name="uq_fund_nav_fund_date"),
        CheckConstraint("nav > 0", name="ck_fund_nav_positive"),
        Index("ix_fund_nav_fund_date", "fund_id", "nav_date"),
    )

    def __repr__(self) -> str:
        return f"<FundNAVHistory fund={self.fund_id} date={self.nav_date} nav={self.nav}>"
