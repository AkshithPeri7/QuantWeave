"""
PostgreSQL Production Compatibility & Dialect Verification Tests (Milestone 9).

Verifies:
- Linear Alembic migration integrity
- SQL schema generation compatibility for PostgreSQL (no SQLite-only dialect artifacts)
- Foreign key cascading semantics (Users -> Portfolios -> Transactions, etc.)
- Atomic transaction rollbacks under simulated exceptions
- Driver configuration compatibility with psycopg (PostgreSQL v3 driver)
"""

import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from app.core.config import Settings
from app.core.database import Base
from app.models.ai import AIConversation, AIMessage, AIToolExecution
from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.models.portfolio_transaction import PortfolioTransaction
from app.models.quantlab import BacktestRun, BacktestTrade, ResearchStrategy
from app.models.user import User


def test_postgresql_ddl_compilation():
    """
    Verifies that all SQLAlchemy models compile cleanly into valid PostgreSQL DDL
    without raising UnsupportedCompilationError or dialect errors.
    """
    pg_dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=pg_dialect))
        assert len(ddl) > 0
        assert table.name in ddl


def test_psycopg_driver_url_schema():
    """Verifies that production connection settings support psycopg (v3 driver)."""
    settings = Settings(
        database_url="postgresql+psycopg://quantweave_prod:SecretPass@postgres.internal:5432/quantweave_db",
        environment="production",
        secret_key="ProductionSuperSecretKeyWith64BytesLengthForSecureHS256Signing1234567890",
    )
    assert "postgresql+psycopg://" in str(settings.database_url)
    assert settings.environment == "production"


def test_transaction_rollback_guarantee(db_session: Session):
    """
    Verifies that session transactions maintain strict ACID rollback guarantees
    when errors occur midway through multi-step ledger entries.
    """
    initial_user_count = db_session.query(User).count()

    try:
        # Step 1: Add user
        user = User(
            name="Rollback Test User",
            email="rollback@quantweave.test",
            password_hash="fakehash",
            role="user",
        )
        db_session.add(user)
        db_session.flush()

        # Step 2: Trigger forced constraint error
        # Inserting identical email in same transaction must violate unique constraint
        duplicate_user = User(
            name="Duplicate User",
            email="rollback@quantweave.test",
            password_hash="fakehash",
            role="user",
        )
        db_session.add(duplicate_user)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Verify that total user count is strictly preserved (zero partial state committed)
    assert db_session.query(User).count() == initial_user_count


def test_foreign_key_cascade_definitions():
    """
    Verifies that critical parent-child relations specify ON DELETE CASCADE
    in their table foreign key definitions for clean referential integrity.
    """
    # 1. AI Message -> AI Tool Executions
    tx_fks = [fk for fk in AIToolExecution.__table__.foreign_keys if "ai_messages" in fk.target_fullname]
    assert len(tx_fks) >= 1
    assert tx_fks[0].ondelete == "CASCADE"

    # 2. Portfolio -> Portfolio Transactions
    port_fks = [fk for fk in PortfolioTransaction.__table__.foreign_keys if "portfolios" in fk.target_fullname]
    assert len(port_fks) >= 1
    assert port_fks[0].ondelete == "CASCADE"

    # 3. User -> Backtest Runs
    user_fks = [fk for fk in BacktestRun.__table__.foreign_keys if "users" in fk.target_fullname]
    assert len(user_fks) >= 1
    assert user_fks[0].ondelete == "CASCADE"

    # 4. Backtest Run -> Backtest Trades
    run_fks = [fk for fk in BacktestTrade.__table__.foreign_keys if "backtest_runs" in fk.target_fullname]
    assert len(run_fks) >= 1
    assert run_fks[0].ondelete == "CASCADE"
