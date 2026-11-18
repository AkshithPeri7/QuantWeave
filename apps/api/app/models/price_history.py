import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
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

if TYPE_CHECKING:
    from app.models.instrument import Instrument
    from app.models.data_source import DataSource


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="prices")
    data_source: Mapped["DataSource | None"] = relationship("DataSource")

    __table_args__ = (
        UniqueConstraint(
            "instrument_id", "trade_date", "provider_id",
            name="uq_price_history_instrument_date_provider"
        ),
        CheckConstraint(
            "high IS NULL OR low IS NULL OR high >= low",
            name="ck_price_history_high_ge_low"
        ),
        CheckConstraint(
            "volume IS NULL OR volume >= 0",
            name="ck_price_history_volume_non_negative"
        ),
        Index("ix_price_history_inst_date", "instrument_id", "trade_date"),
    )

    def __repr__(self) -> str:
        return f"<PriceHistory inst={self.instrument_id} date={self.trade_date} close={self.close}>"
