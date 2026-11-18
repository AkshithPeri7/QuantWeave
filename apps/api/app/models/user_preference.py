import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Boolean, Uuid, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="signal-loom",
        server_default="signal-loom",
    )
    avatar_preset: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="loom",
        server_default="loom",
    )
    color_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        server_default="system",
    )
    reduced_motion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
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

    # Relationship to user
    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreference user_id={self.user_id} theme={self.theme} avatar={self.avatar_preset}>"
