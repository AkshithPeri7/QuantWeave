import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Portfolio(Base):
    """
    Portfolio entity owned by an authenticated user.
    Tracks cash balance, asset holdings, and performance in base_currency (default INR).
    """
    __tablename__ = "portfolios"

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
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

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
    transactions: Mapped[List["PortfolioTransaction"]] = relationship(
        "PortfolioTransaction",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="PortfolioTransaction.trade_date.asc(), PortfolioTransaction.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} user_id={self.user_id} name={self.name} currency={self.base_currency}>"
