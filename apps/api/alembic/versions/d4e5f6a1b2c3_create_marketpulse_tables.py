"""create marketpulse tables

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-11-16 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. news_sources
    op.create_table(
        'news_sources',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('provider_name', sa.String(length=150), nullable=False),
        sa.Column('provider_url', sa.String(length=500), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_successful_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_news_sources_provider_name', 'news_sources', ['provider_name'], unique=True)

    # 2. news_articles
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('short_description', sa.Text(), nullable=True),
        sa.Column('canonical_url', sa.String(length=1000), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['news_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_news_articles_canonical_url', 'news_articles', ['canonical_url'], unique=True)
    op.create_index('ix_news_articles_content_hash', 'news_articles', ['content_hash'], unique=True)
    op.create_index('ix_news_articles_published_at', 'news_articles', ['published_at'], unique=False)
    op.create_index('ix_news_articles_category', 'news_articles', ['category'], unique=False)
    op.create_index('ix_news_articles_source_id', 'news_articles', ['source_id'], unique=False)

    # 3. article_instrument_links
    op.create_table(
        'article_instrument_links',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('article_id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=False),
        sa.Column('match_method', sa.String(length=50), nullable=False),
        sa.Column('match_confidence', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['news_articles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'instrument_id', name='uq_article_instrument'),
    )
    op.create_index('ix_article_instrument_links_article_id', 'article_instrument_links', ['article_id'], unique=False)
    op.create_index('ix_article_instrument_links_instrument_id', 'article_instrument_links', ['instrument_id'], unique=False)

    # 4. news_sentiments
    op.create_table(
        'news_sentiments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('article_id', sa.Uuid(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('positive_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('negative_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('neutral_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('sentiment_label', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['news_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', name='uq_sentiment_article_id'),
    )
    op.create_index('ix_news_sentiments_article_id', 'news_sentiments', ['article_id'], unique=True)
    op.create_index('ix_news_sentiments_sentiment_label', 'news_sentiments', ['sentiment_label'], unique=False)

    # 5. macro_economic_series
    op.create_table(
        'macro_economic_series',
        sa.Column('series_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(length=50), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('series_id'),
    )

    # 6. macro_economic_observations
    op.create_table(
        'macro_economic_observations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('series_id', sa.String(length=50), nullable=False),
        sa.Column('observation_date', sa.Date(), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('release_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['macro_economic_series.series_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('series_id', 'observation_date', name='uq_series_observation_date'),
    )
    op.create_index('ix_macro_obs_series_id', 'macro_economic_observations', ['series_id'], unique=False)
    op.create_index('ix_macro_obs_date', 'macro_economic_observations', ['observation_date'], unique=False)

    # 7. watchlists
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_watchlist_name'),
    )
    op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'], unique=False)

    # 8. watchlist_items
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('watchlist_id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('watchlist_id', 'instrument_id', name='uq_watchlist_instrument'),
    )
    op.create_index('ix_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'], unique=False)
    op.create_index('ix_watchlist_items_instrument_id', 'watchlist_items', ['instrument_id'], unique=False)

    # 9. user_alerts
    op.create_table(
        'user_alerts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=True),
        sa.Column('target_sentiment', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_alerts_user_id', 'user_alerts', ['user_id'], unique=False)
    op.create_index('ix_user_alerts_instrument_id', 'user_alerts', ['instrument_id'], unique=False)

    # 10. alert_notifications
    op.create_table(
        'alert_notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('alert_id', sa.Uuid(), nullable=True),
        sa.Column('article_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['user_alerts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['article_id'], ['news_articles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alert_notifications_user_id', 'alert_notifications', ['user_id'], unique=False)
    op.create_index('ix_alert_notifications_is_read', 'alert_notifications', ['is_read'], unique=False)


def downgrade() -> None:
    op.drop_table('alert_notifications')
    op.drop_table('user_alerts')
    op.drop_table('watchlist_items')
    op.drop_table('watchlists')
    op.drop_table('macro_economic_observations')
    op.drop_table('macro_economic_series')
    op.drop_table('news_sentiments')
    op.drop_table('article_instrument_links')
    op.drop_table('news_articles')
    op.drop_table('news_sources')
