from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> Tuple[bool, str]:
    """Tests the database connection and returns (is_healthy, message)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True, "connected"
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return False, str(exc)
