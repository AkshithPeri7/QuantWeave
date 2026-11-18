import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PortfolioTransaction(Base):
    """
    Append-only audit ledger of portfolio events:
    - BUY: Stock purchase (deducts cash: quantity * price + fees, adds shares)
    - SELL: Stock sale (adds cash: quantity * price - fees, removes shares)
    - DIVIDEND: Cash dividend received (adds cash, share count unchanged)
    - CASH_DEPOSIT: External cash injection (adds cash)
    - CASH_WITHDRAWAL: External cash withdrawal (deducts cash)
    - REVERSAL: Explicit reversing audit entry referencing reversed_transaction_id
    
    All quantities and cash amounts are stored with strict Decimal / NUMERIC precision.
    Historical transactions are never overwritten or silently deleted.
    """
    __tablename__ = "portfolio_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # "BUY", "SELL", "DIVIDEND", "CASH_DEPOSIT", "CASH_WITHDRAWAL", "REVERSAL"
    
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    trade_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 8), nullable=False, default=Decimal("0.00000000")
    )
    price_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("0.000000")
    )
    fees: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("0.000000")
    )
    # Net cash impact (+ increases available cash in portfolio, - decreases cash)
    cash_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("0.000000")
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(120), unique=True, nullable=True, index=True
    )
    reversed_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("portfolio_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
    instrument: Mapped[Optional["Instrument"]] = relationship("Instrument")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="chk_portfolio_tx_quantity_non_negative"),
        CheckConstraint("price_per_unit >= 0", name="chk_portfolio_tx_price_non_negative"),
        CheckConstraint("fees >= 0", name="chk_portfolio_tx_fees_non_negative"),
    )

    def __repr__(self) -> str:
        return (
            f"<PortfolioTransaction id={self.id} type={self.transaction_type} "
            f"date={self.trade_date} qty={self.quantity} price={self.price_per_unit} "
            f"cash={self.cash_amount}>"
        )
