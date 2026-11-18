"""
News Ingestion and Aggregation Engine for QuantWeave MarketPulse.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.analytics.sentiment_engine import FinancialSentimentEngine
from app.models.market import (
    AlertNotification,
    ArticleInstrumentLink,
    NewsArticle,
    NewsSentiment,
    NewsSource,
    UserAlert,
)
from app.providers.macro_fixtures import seed_demo_macroeconomic_data
from app.providers.news_provider import DemoNewsProvider, RawArticleData
from app.services.news_linking import NewsLinkingService


class NewsIngestionService:
    """Service handling multi-source financial news ingestion, deduplication, and alerting."""

    @classmethod
    def get_or_create_source(
        cls,
        db: Session,
        provider_name: str,
        provider_url: Optional[str] = None,
        source_type: str = "DEMO",
    ) -> NewsSource:
        source = db.query(NewsSource).filter(NewsSource.provider_name == provider_name).first()
        if not source:
            source = NewsSource(
                id=uuid.uuid4(),
                provider_name=provider_name,
                provider_url=provider_url,
                source_type=source_type,
                is_active=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
        return source

    @classmethod
    def ingest_articles(
        cls,
        db: Session,
        source_id: uuid.UUID,
        articles: List[RawArticleData],
        auto_analyze_sentiment: bool = True,
        auto_link_instruments: bool = True,
    ) -> Dict[str, int]:
        """
        Deduplicates, validates, and stores news articles.
        Automatically links to instruments, computes sentiment, and generates in-app alert notifications.
        """
        source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
        if not source:
            raise ValueError(f"News source '{source_id}' does not exist.")

        now_utc = datetime.now(timezone.utc)
        max_future_allowed = now_utc + timedelta(hours=1)

        ingested_count = 0
        sentiment_count = 0
        links_count = 0
        alerts_triggered = 0

        # Load active alerts once
        active_alerts = db.query(UserAlert).filter(UserAlert.is_active == True).all()

        for raw in articles:
            # Timestamp validation
            pub_date = raw.published_at
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            if pub_date > max_future_allowed:
                # Reject invalid future publication dates
                continue

            # Deduplication by canonical URL or content hash
            chash = raw.content_hash
            existing = (
                db.query(NewsArticle.id)
                .filter((NewsArticle.canonical_url == raw.canonical_url) | (NewsArticle.content_hash == chash))
                .first()
            )
            if existing:
                continue

            article = NewsArticle(
                id=uuid.uuid4(),
                source_id=source_id,
                title=raw.title.strip(),
                short_description=raw.short_description.strip() if raw.short_description else None,
                canonical_url=raw.canonical_url.strip(),
                published_at=pub_date,
                category=raw.category,
                language=raw.language,
                is_demo=raw.is_demo,
                content_hash=chash,
            )
            db.add(article)
            db.flush()
            ingested_count += 1

            # Auto-link to instruments
            linked_inst_ids = set()
            if auto_link_instruments:
                links = NewsLinkingService.link_article_to_instruments(db, article)
                links_count += len(links)
                for l in links:
                    linked_inst_ids.add(l.instrument_id)

            # Auto-compute sentiment
            sentiment_label = "NEUTRAL"
            if auto_analyze_sentiment:
                s_res = FinancialSentimentEngine.analyze_text(f"{article.title} {article.short_description or ''}")
                sentiment_record = NewsSentiment(
                    id=uuid.uuid4(),
                    article_id=article.id,
                    model_name=s_res.model_name,
                    positive_score=Decimal(str(s_res.positive_score)),
                    negative_score=Decimal(str(s_res.negative_score)),
                    neutral_score=Decimal(str(s_res.neutral_score)),
                    sentiment_label=s_res.label,
                    confidence=Decimal(str(s_res.confidence)),
                )
                db.add(sentiment_record)
                sentiment_count += 1
                sentiment_label = s_res.label

            # Evaluate user alerts
            for alert in active_alerts:
                should_alert = False

                # Keyword match
                if alert.keyword:
                    kw = alert.keyword.lower().strip()
                    if kw in article.title.lower() or (article.short_description and kw in article.short_description.lower()):
                        should_alert = True

                # Instrument match
                if alert.instrument_id and alert.instrument_id in linked_inst_ids:
                    should_alert = True

                # Sentiment filter match
                if should_alert and alert.target_sentiment:
                    if alert.target_sentiment.upper() != sentiment_label.upper():
                        should_alert = False

                if should_alert:
                    notification = AlertNotification(
                        id=uuid.uuid4(),
                        user_id=alert.user_id,
                        alert_id=alert.id,
                        article_id=article.id,
                        title=f"Alert: {alert.keyword or 'Watched Stock'} Mentioned in News",
                        message=article.title,
                        is_read=False,
                    )
                    db.add(notification)
                    alerts_triggered += 1

        source.last_successful_sync = now_utc
        db.commit()

        return {
            "articles_ingested": ingested_count,
            "sentiment_computed": sentiment_count,
            "links_created": links_count,
            "alerts_triggered": alerts_triggered,
        }

    @classmethod
    def seed_demo_market_pulse(cls, db: Session) -> Dict[str, int]:
        """Seeds demo news source, headlines, sentiment, instrument links, and macroeconomic series."""
        source = cls.get_or_create_source(
            db,
            provider_name="QuantWeave Financial Wire",
            provider_url="https://quantweave.demo",
            source_type="DEMO",
        )

        demo_articles = DemoNewsProvider().fetch_articles(limit=50)
        news_stats = cls.ingest_articles(
            db,
            source_id=source.id,
            articles=demo_articles,
            auto_analyze_sentiment=True,
            auto_link_instruments=True,
        )

        macro_stats = seed_demo_macroeconomic_data(db)

        return {
            **news_stats,
            **macro_stats,
        }
