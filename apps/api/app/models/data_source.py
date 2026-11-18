import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    dataset: Mapped[str] = mapped_column(String(80), nullable=False)
    terms_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("provider_name", "dataset", name="uq_data_sources_provider_dataset"),
    )

    def __repr__(self) -> str:
        return f"<DataSource {self.provider_name}:{self.dataset}>"
