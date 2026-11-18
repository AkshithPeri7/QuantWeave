import os
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Force testing configuration
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import settings
settings.environment = "testing"
settings.database_url = "sqlite:///:memory:"

from app.core.database import Base, get_db as core_get_db
import app.core.database as core_db
from app.api.deps import get_db as deps_get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User

# In-memory SQLite database configured with StaticPool for thread-safe test isolation
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
core_db.engine = test_engine
core_db.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_test_db():
    """Creates database schema before each test and drops it after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides an isolated database session for a test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient that uses the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[core_get_db] = override_get_db
    app.dependency_overrides[deps_get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Creates a sample registered user for testing."""
    user = User(
        name="Test Analyst",
        email="analyst@quantweave.test",
        password_hash=hash_password("StrongPassword123!"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Generates an access token for the test user."""
    return create_access_token(
        subject=str(test_user.id),
        claims={"email": test_user.email, "role": test_user.role},
    )
