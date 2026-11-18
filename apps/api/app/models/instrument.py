import uuid
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.price_history import PriceHistory


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    instrument_type: Mapped[str] = mapped_column(String(30), nullable=False, default="equity")
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    prices: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="instrument",
        cascade="all, delete-orphan",
        order_by="PriceHistory.trade_date.desc()",
    )

    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_instruments_exchange_symbol"),
    )

    def __repr__(self) -> str:
        return f"<Instrument {self.exchange}:{self.symbol} - {self.company_name}>"
