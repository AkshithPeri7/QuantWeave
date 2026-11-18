"""
Tests for MarketPulse: Financial News Ingestion, Entity Linking,
Financial Sentiment Engine, Macroeconomic Intelligence, Watchlists, and Alerts.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.orm import Session

from app.analytics.sentiment_engine import FinancialSentimentEngine, SentimentResult
from app.core.security import create_access_token, hash_password
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
from app.providers.macro_fixtures import seed_demo_macroeconomic_data
from app.providers.news_provider import DemoNewsProvider, RawArticleData, RSSNewsProvider
from app.services.news_ingestion import NewsIngestionService
from app.services.news_linking import NewsLinkingService


@pytest.fixture
def normal_user(db_session: Session) -> User:
    user = User(
        name="Market Analyst",
        email=f"analyst_{uuid.uuid4().hex[:6]}@quantweave.test",
        password_hash=hash_password("Password123!"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    admin = User(
        name="Platform Admin",
        email=f"admin_{uuid.uuid4().hex[:6]}@quantweave.test",
        password_hash=hash_password("Password123!"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def normal_user_token_headers(normal_user: User) -> dict:
    token = create_access_token(subject=str(normal_user.id), claims={"email": normal_user.email, "role": normal_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token_headers(admin_user: User) -> dict:
    token = create_access_token(subject=str(admin_user.id), claims={"email": admin_user.email, "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


def test_sentiment_engine_positive_negative_neutral():
    """Verifies sentiment analysis on positive, negative, and neutral financial texts."""
    # Positive text
    pos_res = FinancialSentimentEngine.analyze_text(
        "TCS Reports 6.8% YoY Net Profit Growth in Q3, Driven by Strong Cloud Deal Wins"
    )
    assert pos_res.label == "POSITIVE"
    assert pos_res.positive_score > pos_res.negative_score
    assert pos_res.confidence >= 0.50

    # Negative text
    neg_res = FinancialSentimentEngine.analyze_text(
        "Company warns of steep losses, margin contraction, and severe regulatory penalty"
    )
    assert neg_res.label == "NEGATIVE"
    assert neg_res.negative_score > pos_res.negative_score
    assert neg_res.confidence >= 0.50

    # Neutral text
    neu_res = FinancialSentimentEngine.analyze_text(
        "National Statistical Office releases quarterly financial statements calendar"
    )
    assert neu_res.label == "NEUTRAL"
    assert neu_res.neutral_score >= 0.60

    # Negation handling: "failed to grow"
    negated_res = FinancialSentimentEngine.analyze_text("Company failed to achieve revenue growth this quarter")
    assert negated_res.label in ["NEGATIVE", "NEUTRAL"]
    assert negated_res.negative_score > 0.3


def test_sentiment_aggregation_time_window():
    """Verifies calculation of aggregated net sentiment score and distribution."""
    results = [
        SentimentResult("POSITIVE", 0.7, 0.1, 0.2, 0.7),
        SentimentResult("POSITIVE", 0.8, 0.1, 0.1, 0.8),
        SentimentResult("NEGATIVE", 0.1, 0.7, 0.2, 0.7),
        SentimentResult("NEUTRAL", 0.2, 0.2, 0.6, 0.6),
    ]

    agg = FinancialSentimentEngine.aggregate_sentiments(results)
    assert agg["total_articles"] == 4
    assert agg["positive_count"] == 2
    assert agg["negative_count"] == 1
    assert agg["neutral_count"] == 1
    assert agg["positive_pct"] == 50.0
    assert agg["overall_classification"] == "BULLISH"
    assert agg["net_sentiment_score"] > 0


def test_news_linking_exact_ticker_and_company_name(db_session: Session):
    """Verifies accurate linking of news articles to equities by ticker and company name."""
    # Create test instrument
    inst = Instrument(
        id=uuid.uuid4(),
        exchange="NSE",
        symbol="TCS",
        company_name="Tata Consultancy Services Limited",
        instrument_type="EQUITY",
        currency="INR",
        is_active=True,
    )
    db_session.add(inst)
    db_session.commit()

    source = NewsSource(
        id=uuid.uuid4(),
        provider_name="Test Wire TCS",
        source_type="DEMO",
    )
    db_session.add(source)
    db_session.commit()

    article = NewsArticle(
        id=uuid.uuid4(),
        source_id=source.id,
        title="TCS Signs Major Cloud Deal With European Bank",
        short_description="Tata Consultancy Services announced a multi-million-pound agreement.",
        canonical_url="https://test.com/tcs-cloud-deal",
        published_at=datetime.now(timezone.utc),
        category="EQUITY",
        language="en",
        content_hash="hash_tcs_1",
    )
    db_session.add(article)
    db_session.commit()

    links = NewsLinkingService.link_article_to_instruments(db_session, article, [inst])
    assert len(links) == 1
    assert links[0].instrument_id == inst.id
    assert links[0].match_method == "NAME_AND_TICKER"
    assert links[0].match_confidence >= Decimal("0.90")


def test_news_linking_ambiguous_tickers_prevented(db_session: Session):
    """Verifies short common words (e.g. IT, ON, AI) are not falsely linked as bare tickers."""
    inst_it = Instrument(
        id=uuid.uuid4(),
        exchange="NSE",
        symbol="IT",
        company_name="Information Technology Corp Limited",
        instrument_type="EQUITY",
        currency="INR",
        is_active=True,
    )
    db_session.add(inst_it)
    db_session.commit()

    source = NewsSource(id=uuid.uuid4(), provider_name="Test Wire IT", source_type="DEMO")
    db_session.add(source)
    db_session.commit()

    # Article using 'it' as a common English pronoun, NOT the company name
    article = NewsArticle(
        id=uuid.uuid4(),
        source_id=source.id,
        title="Market opens higher and it continues to gain in afternoon trade",
        short_description="Traders noted that it is a positive session for domestic equities.",
        canonical_url="https://test.com/market-it-gain",
        published_at=datetime.now(timezone.utc),
        category="MARKETS",
        language="en",
        content_hash="hash_it_test",
    )
    db_session.add(article)
    db_session.commit()

    links = NewsLinkingService.link_article_to_instruments(db_session, article, [inst_it])
    assert len(links) == 0, "Common pronoun 'it' must not match as a ticker without company context"


def test_news_ingestion_deduplication_and_timestamps(db_session: Session):
    """Tests that duplicate articles and far-future publication timestamps are safely rejected."""
    source = NewsIngestionService.get_or_create_source(db_session, "Dedup Source", source_type="DEMO")

    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=2)  # Far future timestamp

    articles = [
        RawArticleData(
            title="Valid Article 1",
            canonical_url="https://test.com/art1",
            published_at=now,
        ),
        RawArticleData(
            title="Valid Article 1 (Duplicate URL)",
            canonical_url="https://test.com/art1",
            published_at=now,
        ),
        RawArticleData(
            title="Future Article (Invalid)",
            canonical_url="https://test.com/future-art",
            published_at=future_date,
        ),
    ]

    res = NewsIngestionService.ingest_articles(db_session, source.id, articles)
    assert res["articles_ingested"] == 1, "Only 1 valid, non-duplicate, non-future article should be ingested"


def test_rss_news_parser_safe_xml():
    """Verifies that RSSNewsProvider safely parses valid RSS and rejects malformed content."""
    valid_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Sample Finance Feed</title>
        <item>
          <title><![CDATA[Nifty Crosses 25,000 Milestone]]></title>
          <link>https://example.com/nifty-25000</link>
          <description>Benchmark index gains &lt;b&gt;150 points&lt;/b&gt; on foreign inflows.</description>
          <pubDate>Mon, 10 Feb 2025 10:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """
    parser = RSSNewsProvider()
    articles = parser.parse_rss_string(valid_rss)
    assert len(articles) == 1
    assert articles[0].title == "Nifty Crosses 25,000 Milestone"
    assert articles[0].canonical_url == "https://example.com/nifty-25000"
    assert "<b>" not in (articles[0].short_description or "")

    # Malformed XML should fail gracefully
    bad_articles = parser.parse_rss_string("<broken xml")
    assert bad_articles == []


def test_seed_demo_market_pulse(db_session: Session):
    """Verifies seeding of demo news headlines, sentiment, and macroeconomic series."""
    stats = NewsIngestionService.seed_demo_market_pulse(db_session)
    assert stats["articles_ingested"] >= 10
    assert stats["sentiment_computed"] >= 10
    assert stats["series_created"] >= 3
    assert stats["observations_created"] >= 20

    # Re-seeding must be idempotent
    re_stats = NewsIngestionService.seed_demo_market_pulse(db_session)
    assert re_stats["articles_ingested"] == 0
    assert re_stats["series_created"] == 0


def test_macro_series_and_observations(db_session: Session):
    """Verifies macroeconomic series creation, observation uniqueness, and retrieval."""
    seed_demo_macroeconomic_data(db_session)

    repo_rate = db_session.query(MacroEconomicSeries).filter(MacroEconomicSeries.series_id == "IN_REPO_RATE").first()
    assert repo_rate is not None
    assert repo_rate.unit == "%"
    assert len(repo_rate.observations) >= 10
    assert repo_rate.observations[-1].value == Decimal("6.50")


def test_api_list_news_filtering_and_pagination(client, admin_token_headers):
    """Verifies GET /api/v1/market/news filtering, query search, and pagination."""
    # Seed data
    client.post("/api/v1/market/seed", headers=admin_token_headers)

    # 1. Fetch default paginated news
    resp = client.get("/api/v1/market/news?size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["size"] == 5
    assert len(data["items"]) <= 5
    assert data["total"] >= 10

    # 2. Filter by category
    cat_resp = client.get("/api/v1/market/news?category=ECONOMY")
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()
    for itm in cat_data["items"]:
        assert itm["category"] == "ECONOMY"

    # 3. Filter by sentiment
    sent_resp = client.get("/api/v1/market/news?sentiment=POSITIVE")
    assert sent_resp.status_code == 200
    for itm in sent_resp.json()["items"]:
        assert itm["sentiment"]["sentiment_label"] == "POSITIVE"


def test_api_company_specific_news(client, admin_token_headers, db_session: Session):
    """Verifies retrieving news filtered for a specific company."""
    client.post("/api/v1/market/seed", headers=admin_token_headers)

    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    if not tcs:
        tcs = Instrument(
            id=uuid.uuid4(),
            exchange="NSE",
            symbol="TCS",
            company_name="Tata Consultancy Services Limited",
            instrument_type="EQUITY",
            currency="INR",
        )
        db_session.add(tcs)
        db_session.commit()

    resp = client.get(f"/api/v1/market/instruments/{tcs.id}/news")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_sentiment_summary_endpoint(client, admin_token_headers):
    """Verifies GET /api/v1/market/sentiment/summary."""
    client.post("/api/v1/market/seed", headers=admin_token_headers)

    resp = client.get("/api/v1/market/sentiment/summary?days=90")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_articles" in data
    assert "overall_classification" in data
    assert "net_sentiment_score" in data
    assert "disclaimer" in data


def test_api_macro_endpoints(client, admin_token_headers):
    """Verifies macro series catalog and observation history endpoints."""
    client.post("/api/v1/market/seed", headers=admin_token_headers)

    # Catalog
    cat_resp = client.get("/api/v1/market/macro/series")
    assert cat_resp.status_code == 200
    series_list = cat_resp.json()
    assert len(series_list) >= 3
    series_ids = [s["series_id"] for s in series_list]
    assert "IN_REPO_RATE" in series_ids

    # History
    hist_resp = client.get("/api/v1/market/macro/series/IN_REPO_RATE")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["series_id"] == "IN_REPO_RATE"
    assert len(hist_data["observations"]) >= 10


def test_watchlist_crud_and_user_isolation(client, normal_user_token_headers, admin_token_headers, db_session: Session):
    """Verifies user watchlists, adding/removing items, and user isolation."""
    inst = db_session.query(Instrument).first()
    if not inst:
        inst = Instrument(
            id=uuid.uuid4(),
            exchange="NSE",
            symbol="INFY",
            company_name="Infosys Limited",
            instrument_type="EQUITY",
            currency="INR",
        )
        db_session.add(inst)
        db_session.commit()

    # User 1 creates watchlist
    create_resp = client.post(
        "/api/v1/market/watchlists",
        json={"name": "Tech Titans", "description": "High growth IT companies"},
        headers=normal_user_token_headers,
    )
    assert create_resp.status_code == 201
    wl_id = create_resp.json()["id"]

    # User 1 adds instrument
    add_resp = client.post(
        f"/api/v1/market/watchlists/{wl_id}/items",
        json={"instrument_id": str(inst.id), "notes": "Core holding"},
        headers=normal_user_token_headers,
    )
    assert add_resp.status_code == 201

    # User 1 retrieves watchlist
    get_resp = client.get(f"/api/v1/market/watchlists/{wl_id}", headers=normal_user_token_headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()["items"]) == 1

    # User 2 (admin) CANNOT access User 1's watchlist
    unauth_resp = client.get(f"/api/v1/market/watchlists/{wl_id}", headers=admin_token_headers)
    assert unauth_resp.status_code == 404, "User 2 must not access User 1's private watchlist"

    # User 1 deletes item
    del_itm_resp = client.delete(
        f"/api/v1/market/watchlists/{wl_id}/items/{inst.id}",
        headers=normal_user_token_headers,
    )
    assert del_itm_resp.status_code == 204


def test_user_alerts_and_notification_trigger(client, normal_user_token_headers, db_session: Session):
    """Verifies creating an alert rule and receiving an in-app event notification upon matching news."""
    # Create alert for keyword "cloud"
    alert_resp = client.post(
        "/api/v1/market/alerts",
        json={"keyword": "cloud", "alert_type": "NEWS"},
        headers=normal_user_token_headers,
    )
    assert alert_resp.status_code == 201
    alert_id = alert_resp.json()["id"]

    # Ingest an article mentioning "cloud"
    source = NewsIngestionService.get_or_create_source(db_session, "Alert Test Source")
    article = RawArticleData(
        title="Major Cloud Transformation Initiative Announced",
        canonical_url=f"https://test.com/cloud-{uuid.uuid4()}",
        published_at=datetime.now(timezone.utc),
    )
    NewsIngestionService.ingest_articles(db_session, source.id, [article])

    # Fetch notifications for user
    notif_resp = client.get("/api/v1/market/notifications", headers=normal_user_token_headers)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert len(notifs) >= 1
    target_notif = notifs[0]
    assert "cloud" in target_notif["title"].lower() or "cloud" in target_notif["message"].lower()

    # Mark as read
    read_resp = client.put(f"/api/v1/market/notifications/{target_notif['id']}/read", headers=normal_user_token_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True
