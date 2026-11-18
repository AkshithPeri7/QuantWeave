"""
SQLAlchemy models for QuantLab: Strategy Research, Simulation & Backtesting Engine.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.instrument import Instrument
    from app.models.user import User


class ResearchStrategy(Base):
    """
    User-defined or preset quantitative research strategy with validated parameter configuration.
    """
    __tablename__ = "research_strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

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

    # Relationships
    user: Mapped["User"] = relationship("User")
    backtest_runs: Mapped[List["BacktestRun"]] = relationship(
        "BacktestRun",
        back_populates="strategy",
        cascade="all, delete-orphan",
    )


class BacktestRun(Base):
    """
    Historical backtest simulation execution record with parameters, dataset fingerprint, and metrics.
    """
    __tablename__ = "backtest_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_strategies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    starting_capital: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("100000.00"),
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    fee_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.001)
    slippage_bps: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETED", index=True)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    dataset_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    strategy: Mapped[Optional["ResearchStrategy"]] = relationship(
        "ResearchStrategy",
        back_populates="backtest_runs",
    )
    user: Mapped["User"] = relationship("User")
    instrument: Mapped["Instrument"] = relationship("Instrument")
    trades: Mapped[List["BacktestTrade"]] = relationship(
        "BacktestTrade",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="BacktestTrade.execution_date.asc()",
    )
    equity_points: Mapped[List["BacktestEquityPoint"]] = relationship(
        "BacktestEquityPoint",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="BacktestEquityPoint.point_date.asc()",
    )


class BacktestTrade(Base):
    """
    Individual trade simulated during a backtest execution.
    Executes at the next bar's Open price following a signal.
    """
    __tablename__ = "backtest_trades"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("backtest_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY / SELL
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    execution_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    execution_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0.0000"))
    slippage_cost: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0.0000"))
    cash_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    position_after: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    pnl_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # Relationships
    run: Mapped["BacktestRun"] = relationship("BacktestRun", back_populates="trades")


class BacktestEquityPoint(Base):
    """
    Daily portfolio valuation point during the backtest period.
    Enables interactive equity curves, drawdown charts, and benchmark comparison.
    """
    __tablename__ = "backtest_equity_points"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("backtest_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    point_date: Mapped[date] = mapped_column(Date, nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    position_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    drawdown_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    benchmark_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "point_date", name="uq_backtest_equity_point"),
        Index("ix_backtest_equity_run_date", "run_id", "point_date"),
    )

    # Relationships
    run: Mapped["BacktestRun"] = relationship("BacktestRun", back_populates="equity_points")
