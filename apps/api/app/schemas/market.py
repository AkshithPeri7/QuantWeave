"""
Pydantic Schemas for MarketPulse: Financial News, Sentiment, Macroeconomics, and Watchlists.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class NewsSentimentResponse(BaseModel):
    id: uuid.UUID
    model_name: str
    positive_score: float
    negative_score: float
    neutral_score: float
    sentiment_label: str
    confidence: float
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsSourceResponse(BaseModel):
    id: uuid.UUID
    provider_name: str
    provider_url: Optional[str] = None
    source_type: str
    is_active: bool
    last_successful_sync: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LinkedInstrumentSummary(BaseModel):
    id: uuid.UUID
    symbol: str
    company_name: str
    match_method: str
    match_confidence: float

    model_config = ConfigDict(from_attributes=True)


class NewsArticleResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_name: Optional[str] = None
    title: str
    short_description: Optional[str] = None
    canonical_url: str
    published_at: datetime
    ingested_at: datetime
    category: str
    language: str
    is_demo: bool
    sentiment: Optional[NewsSentimentResponse] = None
    linked_instruments: List[LinkedInstrumentSummary] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedNewsArticles(BaseModel):
    items: List[NewsArticleResponse]
    total: int
    page: int
    size: int
    pages: int


class SentimentTrendSummary(BaseModel):
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    net_sentiment_score: float
    overall_classification: str
    average_confidence: float
    time_window_days: int
    is_demo: bool = True
    disclaimer: str = "Sentiment classifications are machine-generated statistical approximations and do not constitute financial advice or price predictions."


class MacroObservationPoint(BaseModel):
    id: uuid.UUID
    observation_date: date
    value: float
    release_timestamp: Optional[datetime] = None
    is_demo: bool = True

    model_config = ConfigDict(from_attributes=True)


class MacroSeriesResponse(BaseModel):
    series_id: str
    name: str
    unit: str
    source: str
    description: Optional[str] = None
    frequency: str
    is_demo: bool = True
    latest_observation: Optional[MacroObservationPoint] = None
    observations: List[MacroObservationPoint] = []

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    instrument_id: uuid.UUID
    symbol: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    added_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[WatchlistItemResponse] = []
    latest_news: List[NewsArticleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class WatchlistItemCreate(BaseModel):
    instrument_id: uuid.UUID
    notes: Optional[str] = Field(default=None, max_length=255)


class UserAlertCreate(BaseModel):
    instrument_id: Optional[uuid.UUID] = None
    alert_type: str = Field(default="NEWS", max_length=50)  # NEWS, SENTIMENT
    keyword: Optional[str] = Field(default=None, max_length=100)
    target_sentiment: Optional[str] = Field(default=None, max_length=20)  # POSITIVE, NEGATIVE


class UserAlertResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    instrument_id: Optional[uuid.UUID] = None
    alert_type: str
    keyword: Optional[str] = None
    target_sentiment: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertNotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    alert_id: Optional[uuid.UUID] = None
    article_id: Optional[uuid.UUID] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
