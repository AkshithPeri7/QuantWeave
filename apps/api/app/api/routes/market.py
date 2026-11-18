"""
MarketPulse API Routes: News, Sentiment, Macroeconomics, Watchlists, and Alerts.
"""

from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.analytics.sentiment_engine import FinancialSentimentEngine, SentimentResult
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.instrument import Instrument
from app.models.market import (
    AlertNotification,
    ArticleInstrumentLink,
    MacroEconomicObservation,
    MacroEconomicSeries,
    NewsArticle,
    NewsSentiment,
    NewsSource,
    UserAlert,
    Watchlist,
    WatchlistItem,
)
from app.models.user import User
from app.providers.news_provider import RSSNewsProvider
from app.schemas.market import (
    AlertNotificationResponse,
    LinkedInstrumentSummary,
    MacroObservationPoint,
    MacroSeriesResponse,
    NewsArticleResponse,
    NewsSentimentResponse,
    PaginatedNewsArticles,
    SentimentTrendSummary,
    UserAlertCreate,
    UserAlertResponse,
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistResponse,
    WatchlistUpdate,
)
from app.services.news_ingestion import NewsIngestionService

router = APIRouter(prefix="/api/v1/market", tags=["market"])


def _verify_admin_access(current_user: User) -> None:
    """Verifies that the user has admin role or environment is dev/testing."""
    if current_user.role == "admin":
        return
    if settings.environment in ["development", "testing"]:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only platform administrators can perform data ingestion or seeding operations.",
    )


def _build_article_response(article: NewsArticle) -> NewsArticleResponse:
    """Helper to convert NewsArticle DB model to Pydantic response."""
    linked_insts: List[LinkedInstrumentSummary] = []
    if article.instrument_links:
        for link in article.instrument_links:
            if link.instrument:
                linked_insts.append(
                    LinkedInstrumentSummary(
                        id=link.instrument.id,
                        symbol=link.instrument.symbol,
                        company_name=link.instrument.company_name,
                        match_method=link.match_method,
                        match_confidence=float(link.match_confidence),
                    )
                )

    sentiment_resp: Optional[NewsSentimentResponse] = None
    if article.sentiment:
        sentiment_resp = NewsSentimentResponse(
            id=article.sentiment.id,
            model_name=article.sentiment.model_name,
            positive_score=float(article.sentiment.positive_score),
            negative_score=float(article.sentiment.negative_score),
            neutral_score=float(article.sentiment.neutral_score),
            sentiment_label=article.sentiment.sentiment_label,
            confidence=float(article.sentiment.confidence),
            analyzed_at=article.sentiment.analyzed_at,
        )

    return NewsArticleResponse(
        id=article.id,
        source_id=article.source_id,
        source_name=article.source.provider_name if article.source else None,
        title=article.title,
        short_description=article.short_description,
        canonical_url=article.canonical_url,
        published_at=article.published_at,
        ingested_at=article.ingested_at,
        category=article.category,
        language=article.language,
        is_demo=article.is_demo,
        sentiment=sentiment_resp,
        linked_instruments=linked_insts,
    )


# ==========================================
# 1. Financial News Feed & Discovery
# ==========================================


@router.get("/news", response_model=PaginatedNewsArticles)
async def list_news_articles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    instrument_id: Optional[uuid.UUID] = Query(None),
    q: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> PaginatedNewsArticles:
    """Retrieves paginated news articles with filtering by category, sentiment, and instrument."""
    query = (
        db.query(NewsArticle)
        .options(
            joinedload(NewsArticle.source),
            joinedload(NewsArticle.sentiment),
            joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
        )
    )

    if category and category != "All":
        query = query.filter(NewsArticle.category == category)

    if sentiment and sentiment != "All":
        query = query.join(NewsArticle.sentiment).filter(NewsSentiment.sentiment_label == sentiment.upper())

    if instrument_id:
        query = query.join(NewsArticle.instrument_links).filter(ArticleInstrumentLink.instrument_id == instrument_id)

    if start_date:
        query = query.filter(NewsArticle.published_at >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc))

    if end_date:
        query = query.filter(NewsArticle.published_at <= datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc))

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                NewsArticle.title.ilike(term),
                NewsArticle.short_description.ilike(term),
            )
        )

    total = query.count()
    pages = max(1, ceil(total / size)) if total > 0 else 1
    offset = (page - 1) * size

    articles = query.order_by(NewsArticle.published_at.desc()).offset(offset).limit(size).all()

    return PaginatedNewsArticles(
        items=[_build_article_response(a) for a in articles],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/news/search", response_model=List[NewsArticleResponse])
async def search_news_articles(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[NewsArticleResponse]:
    """Search news headlines and descriptions."""
    term = f"%{q.strip()}%"
    articles = (
        db.query(NewsArticle)
        .options(
            joinedload(NewsArticle.source),
            joinedload(NewsArticle.sentiment),
            joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
        )
        .filter(or_(NewsArticle.title.ilike(term), NewsArticle.short_description.ilike(term)))
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )
    return [_build_article_response(a) for a in articles]


@router.get("/news/categories")
async def get_news_categories(db: Session = Depends(get_db)) -> dict:
    """Returns available news categories."""
    categories = (
        db.query(NewsArticle.category)
        .distinct()
        .all()
    )
    cat_list = sorted([c[0] for c in categories if c[0]])
    if not cat_list:
        cat_list = ["MARKETS", "EQUITY", "ECONOMY", "BANKING"]
    return {"categories": cat_list}


@router.get("/news/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> NewsArticleResponse:
    """Retrieves full article details, source metadata, sentiment, and linked companies."""
    article = (
        db.query(NewsArticle)
        .options(
            joinedload(NewsArticle.source),
            joinedload(NewsArticle.sentiment),
            joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
        )
        .filter(NewsArticle.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return _build_article_response(article)


@router.get("/instruments/{instrument_id}/news", response_model=List[NewsArticleResponse])
async def get_company_news(
    instrument_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[NewsArticleResponse]:
    """Retrieves articles specifically linked to an instrument."""
    inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found.")

    links = (
        db.query(ArticleInstrumentLink)
        .filter(ArticleInstrumentLink.instrument_id == instrument_id)
        .order_by(ArticleInstrumentLink.created_at.desc())
        .limit(limit)
        .all()
    )

    article_ids = [l.article_id for l in links]
    if not article_ids:
        return []

    articles = (
        db.query(NewsArticle)
        .options(
            joinedload(NewsArticle.source),
            joinedload(NewsArticle.sentiment),
            joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
        )
        .filter(NewsArticle.id.in_(article_ids))
        .order_by(NewsArticle.published_at.desc())
        .all()
    )
    return [_build_article_response(a) for a in articles]


@router.get("/sectors/{sector}/news", response_model=List[NewsArticleResponse])
async def get_sector_news(
    sector: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[NewsArticleResponse]:
    """Retrieves articles linked to instruments in a given industry sector."""
    instruments = db.query(Instrument.id).filter(Instrument.sector.ilike(f"%{sector}%")).all()
    inst_ids = [i[0] for i in instruments]
    if not inst_ids:
        return []

    articles = (
        db.query(NewsArticle)
        .join(NewsArticle.instrument_links)
        .options(
            joinedload(NewsArticle.source),
            joinedload(NewsArticle.sentiment),
            joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
        )
        .filter(ArticleInstrumentLink.instrument_id.in_(inst_ids))
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )
    return [_build_article_response(a) for a in articles]


# ==========================================
# 2. Financial Sentiment Trends
# ==========================================


@router.get("/sentiment/summary", response_model=SentimentTrendSummary)
async def get_sentiment_summary(
    days: int = Query(30, ge=1, le=365),
    instrument_id: Optional[uuid.UUID] = Query(None),
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> SentimentTrendSummary:
    """Calculates aggregated sentiment breakdown and net sentiment score over a time window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        db.query(NewsSentiment)
        .join(NewsArticle, NewsSentiment.article_id == NewsArticle.id)
        .filter(NewsArticle.published_at >= cutoff)
    )

    if instrument_id:
        query = query.join(NewsArticle.instrument_links).filter(ArticleInstrumentLink.instrument_id == instrument_id)

    if sector:
        instruments = db.query(Instrument.id).filter(Instrument.sector.ilike(f"%{sector}%")).all()
        inst_ids = [i[0] for i in instruments]
        query = query.join(NewsArticle.instrument_links).filter(ArticleInstrumentLink.instrument_id.in_(inst_ids))

    sentiments = query.all()

    sentiment_results: List[SentimentResult] = [
        SentimentResult(
            label=s.sentiment_label,
            positive_score=float(s.positive_score),
            negative_score=float(s.negative_score),
            neutral_score=float(s.neutral_score),
            confidence=float(s.confidence),
            model_name=s.model_name,
        )
        for s in sentiments
    ]

    agg = FinancialSentimentEngine.aggregate_sentiments(sentiment_results)
    return SentimentTrendSummary(
        **agg,
        time_window_days=days,
        is_demo=True,
    )


# ==========================================
# 3. Macroeconomic Intelligence
# ==========================================


@router.get("/macro/series", response_model=List[MacroSeriesResponse])
async def list_macro_series(db: Session = Depends(get_db)) -> List[MacroSeriesResponse]:
    """Retrieves catalog of macroeconomic indicators with latest observation."""
    series_list = db.query(MacroEconomicSeries).all()
    results: List[MacroSeriesResponse] = []

    for s in series_list:
        latest = (
            db.query(MacroEconomicObservation)
            .filter(MacroEconomicObservation.series_id == s.series_id)
            .order_by(MacroEconomicObservation.observation_date.desc())
            .first()
        )
        latest_pt = (
            MacroObservationPoint(
                id=latest.id,
                observation_date=latest.observation_date,
                value=float(latest.value),
                release_timestamp=latest.release_timestamp,
                is_demo=latest.is_demo,
            )
            if latest
            else None
        )
        results.append(
            MacroSeriesResponse(
                series_id=s.series_id,
                name=s.name,
                unit=s.unit,
                source=s.source,
                description=s.description,
                frequency=s.frequency,
                is_demo=s.is_demo,
                latest_observation=latest_pt,
                observations=[],
            )
        )
    return results


@router.get("/macro/series/{series_id}", response_model=MacroSeriesResponse)
async def get_macro_series_history(
    series_id: str,
    db: Session = Depends(get_db),
) -> MacroSeriesResponse:
    """Retrieves chronological observations for a macroeconomic indicator."""
    series = db.query(MacroEconomicSeries).filter(MacroEconomicSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Series '{series_id}' not found.")

    obs = (
        db.query(MacroEconomicObservation)
        .filter(MacroEconomicObservation.series_id == series_id)
        .order_by(MacroEconomicObservation.observation_date.asc())
        .all()
    )

    obs_points = [
        MacroObservationPoint(
            id=o.id,
            observation_date=o.observation_date,
            value=float(o.value),
            release_timestamp=o.release_timestamp,
            is_demo=o.is_demo,
        )
        for o in obs
    ]

    return MacroSeriesResponse(
        series_id=series.series_id,
        name=series.name,
        unit=series.unit,
        source=series.source,
        description=series.description,
        frequency=series.frequency,
        is_demo=series.is_demo,
        latest_observation=obs_points[-1] if obs_points else None,
        observations=obs_points,
    )


# ==========================================
# 4. Watchlists & Alert Intelligence
# ==========================================


@router.get("/watchlists", response_model=List[WatchlistResponse])
async def list_user_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[WatchlistResponse]:
    """Retrieves all watchlists owned by the authenticated user."""
    watchlists = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )

    responses: List[WatchlistResponse] = []
    for wl in watchlists:
        items_resp: List[WatchlistItemResponse] = []
        inst_ids = []
        for itm in wl.items:
            if itm.instrument:
                inst_ids.append(itm.instrument_id)
                items_resp.append(
                    WatchlistItemResponse(
                        id=itm.id,
                        instrument_id=itm.instrument_id,
                        symbol=itm.instrument.symbol,
                        company_name=itm.instrument.company_name,
                        exchange=itm.instrument.exchange,
                        sector=itm.instrument.sector,
                        added_at=itm.added_at,
                        notes=itm.notes,
                    )
                )

        # Get latest 5 news articles for watched instruments
        latest_news: List[NewsArticleResponse] = []
        if inst_ids:
            news_items = (
                db.query(NewsArticle)
                .join(NewsArticle.instrument_links)
                .options(
                    joinedload(NewsArticle.source),
                    joinedload(NewsArticle.sentiment),
                    joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
                )
                .filter(ArticleInstrumentLink.instrument_id.in_(inst_ids))
                .order_by(NewsArticle.published_at.desc())
                .limit(5)
                .all()
            )
            latest_news = [_build_article_response(a) for a in news_items]

        responses.append(
            WatchlistResponse(
                id=wl.id,
                user_id=wl.user_id,
                name=wl.name,
                description=wl.description,
                created_at=wl.created_at,
                updated_at=wl.updated_at,
                items=items_resp,
                latest_news=latest_news,
            )
        )

    return responses


@router.post("/watchlists", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Creates a new watchlist for the current user."""
    existing = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.name == data.name.strip())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Watchlist with name '{data.name}' already exists.",
        )

    wl = Watchlist(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
    )
    db.add(wl)
    db.commit()
    db.refresh(wl)

    return WatchlistResponse(
        id=wl.id,
        user_id=wl.user_id,
        name=wl.name,
        description=wl.description,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
        items=[],
        latest_news=[],
    )


@router.get("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Retrieves a specific watchlist owned by current user."""
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")

    items_resp: List[WatchlistItemResponse] = []
    inst_ids = []
    for itm in wl.items:
        if itm.instrument:
            inst_ids.append(itm.instrument_id)
            items_resp.append(
                WatchlistItemResponse(
                    id=itm.id,
                    instrument_id=itm.instrument_id,
                    symbol=itm.instrument.symbol,
                    company_name=itm.instrument.company_name,
                    exchange=itm.instrument.exchange,
                    sector=itm.instrument.sector,
                    added_at=itm.added_at,
                    notes=itm.notes,
                )
            )

    latest_news: List[NewsArticleResponse] = []
    if inst_ids:
        news_items = (
            db.query(NewsArticle)
            .join(NewsArticle.instrument_links)
            .options(
                joinedload(NewsArticle.source),
                joinedload(NewsArticle.sentiment),
                joinedload(NewsArticle.instrument_links).joinedload(ArticleInstrumentLink.instrument),
            )
            .filter(ArticleInstrumentLink.instrument_id.in_(inst_ids))
            .order_by(NewsArticle.published_at.desc())
            .limit(10)
            .all()
        )
        latest_news = [_build_article_response(a) for a in news_items]

    return WatchlistResponse(
        id=wl.id,
        user_id=wl.user_id,
        name=wl.name,
        description=wl.description,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
        items=items_resp,
        latest_news=latest_news,
    )


@router.put("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: uuid.UUID,
    data: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Updates a watchlist name or description."""
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")

    if data.name:
        wl.name = data.name.strip()
    if data.description is not None:
        wl.description = data.description.strip() if data.description else None

    db.commit()
    db.refresh(wl)
    return await get_watchlist(watchlist_id, current_user, db)


@router.delete("/watchlists/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Deletes a watchlist."""
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")

    db.delete(wl)
    db.commit()


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_watchlist(
    watchlist_id: uuid.UUID,
    data: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemResponse:
    """Adds an instrument to a watchlist."""
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")

    inst = db.query(Instrument).filter(Instrument.id == data.instrument_id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found.")

    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.instrument_id == data.instrument_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{inst.symbol} is already in this watchlist.",
        )

    item = WatchlistItem(
        id=uuid.uuid4(),
        watchlist_id=watchlist_id,
        instrument_id=data.instrument_id,
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return WatchlistItemResponse(
        id=item.id,
        instrument_id=inst.id,
        symbol=inst.symbol,
        company_name=inst.company_name,
        exchange=inst.exchange,
        sector=inst.sector,
        added_at=item.added_at,
        notes=item.notes,
    )


@router.delete("/watchlists/{watchlist_id}/items/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_watchlist(
    watchlist_id: uuid.UUID,
    instrument_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Removes an instrument from a watchlist."""
    wl = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .first()
    )
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found.")

    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.instrument_id == instrument_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in watchlist.")

    db.delete(item)
    db.commit()


# ==========================================
# 5. User Alerts & Notifications
# ==========================================


@router.get("/alerts", response_model=List[UserAlertResponse])
async def list_user_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[UserAlertResponse]:
    """Retrieves all news and sentiment alerts for current user."""
    alerts = (
        db.query(UserAlert)
        .filter(UserAlert.user_id == current_user.id)
        .order_by(UserAlert.created_at.desc())
        .all()
    )
    return [UserAlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts", response_model=UserAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_user_alert(
    data: UserAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAlertResponse:
    """Creates a new news or sentiment alert."""
    alert = UserAlert(
        id=uuid.uuid4(),
        user_id=current_user.id,
        instrument_id=data.instrument_id,
        alert_type=data.alert_type,
        keyword=data.keyword.strip() if data.keyword else None,
        target_sentiment=data.target_sentiment.upper() if data.target_sentiment else None,
        is_active=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return UserAlertResponse.model_validate(alert)


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Deletes an alert."""
    alert = (
        db.query(UserAlert)
        .filter(UserAlert.id == alert_id, UserAlert.user_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    db.delete(alert)
    db.commit()


@router.get("/notifications", response_model=List[AlertNotificationResponse])
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AlertNotificationResponse]:
    """Retrieves in-app alert notifications for current user."""
    notifs = (
        db.query(AlertNotification)
        .filter(AlertNotification.user_id == current_user.id)
        .order_by(AlertNotification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [AlertNotificationResponse.model_validate(n) for n in notifs]


@router.put("/notifications/{notification_id}/read", response_model=AlertNotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertNotificationResponse:
    """Marks a notification as read."""
    notif = (
        db.query(AlertNotification)
        .filter(AlertNotification.id == notification_id, AlertNotification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return AlertNotificationResponse.model_validate(notif)


# ==========================================
# 6. Admin Seeding & Ingestion
# ==========================================


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_market_pulse_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Seeds synthetic demo news headlines, sentiment, entity links, and macroeconomic series (admin/dev)."""
    _verify_admin_access(current_user)
    stats = NewsIngestionService.seed_demo_market_pulse(db)
    return {
        "status": "success",
        "message": f"Successfully initialized MarketPulse: {stats['articles_ingested']} articles ingested, {stats['sentiment_computed']} sentiments analyzed, {stats['series_created']} macro series seeded.",
        **stats,
    }


@router.post("/ingest/rss", status_code=status.HTTP_201_CREATED)
async def ingest_rss_endpoint(
    provider_name: str = Query(..., min_length=1),
    xml_content: str = Query(..., min_length=10),
    category: str = Query("MARKETS"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Parses and ingests financial news from RSS XML content (admin/dev)."""
    _verify_admin_access(current_user)
    source = NewsIngestionService.get_or_create_source(
        db,
        provider_name=provider_name,
        source_type="RSS",
    )
    parser = RSSNewsProvider()
    articles = parser.parse_rss_string(xml_content, default_category=category)
    if not articles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid articles found in XML content.")

    stats = NewsIngestionService.ingest_articles(db, source_id=source.id, articles=articles)
    return {
        "status": "success",
        "message": f"Successfully ingested {stats['articles_ingested']} articles from RSS provider '{provider_name}'.",
        **stats,
    }
