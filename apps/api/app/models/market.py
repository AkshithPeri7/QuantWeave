"""
SQLAlchemy models for MarketPulse: Financial News, Macroeconomics, Sentiment, and Watchlists.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.instrument import Instrument

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NewsSource(Base):
    __tablename__ = "news_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider_name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )
    provider_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DEMO",  # RSS, API, DEMO
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    last_successful_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    articles: Mapped[List["NewsArticle"]] = relationship(
        "NewsArticle",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    canonical_url: Mapped[str] = mapped_column(
        String(1000),
        unique=True,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MARKETS",
        index=True,  # MARKETS, EQUITY, ECONOMY, BANKING, POLICY, TECH
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    source: Mapped["NewsSource"] = relationship(
        "NewsSource",
        back_populates="articles",
    )
    instrument_links: Mapped[List["ArticleInstrumentLink"]] = relationship(
        "ArticleInstrumentLink",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    sentiment: Mapped[Optional["NewsSentiment"]] = relationship(
        "NewsSentiment",
        uselist=False,
        back_populates="article",
        cascade="all, delete-orphan",
    )


class ArticleInstrumentLink(Base):
    __tablename__ = "article_instrument_links"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="TICKER",  # TICKER, NAME, ALIAS, MANUAL
    )
    match_confidence: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("1.00"),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="AUTO_MATCHED",  # AUTO_MATCHED, VERIFIED, REJECTED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("article_id", "instrument_id", name="uq_article_instrument"),
    )

    article: Mapped["NewsArticle"] = relationship(
        "NewsArticle",
        back_populates="instrument_links",
    )
    instrument: Mapped["Instrument"] = relationship("Instrument")


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="quantweave-lexicon-v1",
    )
    positive_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0"),
    )
    negative_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0"),
    )
    neutral_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("1.0"),
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NEUTRAL",
        index=True,  # POSITIVE, NEGATIVE, NEUTRAL
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.5"),
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    article: Mapped["NewsArticle"] = relationship(
        "NewsArticle",
        back_populates="sentiment",
    )


class MacroEconomicSeries(Base):
    __tablename__ = "macro_economic_series"

    series_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,  # IN_REPO_RATE, IN_CPI_INFLATION, IN_10Y_BOND_YIELD, IN_GDP_GROWTH
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="%",
    )
    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Reserve Bank of India",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    frequency: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MONTHLY",
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    observations: Mapped[List["MacroEconomicObservation"]] = relationship(
        "MacroEconomicObservation",
        back_populates="series",
        cascade="all, delete-orphan",
        order_by="MacroEconomicObservation.observation_date.asc()",
    )


class MacroEconomicObservation(Base):
    __tablename__ = "macro_economic_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    series_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("macro_economic_series.series_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )
    release_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    __table_args__ = (
        UniqueConstraint("series_id", "observation_date", name="uq_series_observation_date"),
    )

    series: Mapped["MacroEconomicSeries"] = relationship(
        "MacroEconomicSeries",
        back_populates="observations",
    )


class Watchlist(Base):
    __tablename__ = "watchlists"

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
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_watchlist_name"),
    )

    items: Mapped[List["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        order_by="WatchlistItem.added_at.asc()",
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("watchlist_id", "instrument_id", name="uq_watchlist_instrument"),
    )

    watchlist: Mapped["Watchlist"] = relationship(
        "Watchlist",
        back_populates="items",
    )
    instrument: Mapped["Instrument"] = relationship("Instrument")


class UserAlert(Base):
    __tablename__ = "user_alerts"

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
    instrument_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NEWS",  # NEWS, SENTIMENT, MACRO
    )
    keyword: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    target_sentiment: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,  # POSITIVE, NEGATIVE
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AlertNotification(Base):
    __tablename__ = "alert_notifications"

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
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_alerts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news_articles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
