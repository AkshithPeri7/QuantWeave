# Python, FastAPI & Relational Database Architecture

This guide covers the backend engineering foundation of **QuantWeave**, detailing how modern Python 3.13, FastAPI, Pydantic v2, and SQLAlchemy 2.0 work together to deliver a secure, high-throughput financial analytics engine.

---

## 1. Modern Python: Typing & Object-Oriented Principles

QuantWeave enforces strict type annotations across the entire backend codebase. This eliminates runtime `TypeError` exceptions and enables comprehensive static analysis via tools like Pyrefly and Pyright.

### Generics and Optional Typing
Python 3.10+ native union syntax (`|`) and generic collections (`list[str]`, `dict[str, Any]`) are used throughout:

```python
# From apps/api/app/services/analytics.py
from typing import Optional

def calculate_sma(prices: list[float], period: int = 20) -> list[Optional[float]]:
    """Calculates Simple Moving Average over a price series.
    
    Returns None for the first (period - 1) indices where insufficient data exists.
    """
    if len(prices) < period or period <= 0:
        return [None] * len(prices)
    
    sma_values: list[Optional[float]] = [None] * (period - 1)
    current_sum = sum(prices[:period])
    sma_values.append(current_sum / period)
    
    for i in range(period, len(prices)):
        current_sum += prices[i] - prices[i - period]
        sma_values.append(current_sum / period)
        
    return sma_values
```

### Encapsulation and Domain Services
Business logic is never placed in API route handlers. Instead, it is encapsulated within dedicated stateless domain services (e.g., `PortfolioService`, `AnalyticsService`, `QuantLabEngine`):

```python
# Encapsulated domain logic pattern
class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def execute_buy(
        self, 
        portfolio_id: uuid.UUID, 
        user_id: uuid.UUID, 
        instrument_id: uuid.UUID, 
        shares: float, 
        price: float
    ) -> PortfolioTransaction:
        # Atomic validation and append-only ledger record
        ...
```

---

## 2. FastAPI Routing & Request Lifecycle

FastAPI decomposes endpoints into modular APIRouters grouped by domain:
- `/auth`: Registration, login, session tokens, password changes.
- `/users`: Profile management and theme preferences.
- `/instruments`: Equity metadata, daily historical OHLCV data.
- `/portfolios`: Append-only ledgers, holdings, valuations, XIRR.
- `/funds`: Mutual fund discovery, NAV history, SIP calculators.
- `/market`: News headlines, sentiment scores, economic indicators.
- `/quantlab`: Algorithmic backtesting, grid search, parameter optimization.
- `/ai`: Conversational copilot, tool calling, and RAG retrieval.

### Central Application Configuration (`app/main.py`)

```python
from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.portfolios import router as portfolios_router

app = FastAPI(
    title="QuantWeave API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(portfolios_router)
```

---

## 3. Dependency Injection (DI)

FastAPI's dependency injection system (`fastapi.Depends`) provides clean lifecycle management, authentication enforcement, and database connection pooling.

### Database Session Lifecycle Dependency (`app/core/database.py`)

```python
from typing import Generator
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    """Provides a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

When a request arrives, `get_db` opens a new connection from the connection pool. Once the request completes (or fails with an exception), the `finally` block ensures the session is returned to the pool, preventing connection leaks.

### Authenticated User Extraction (`app/api/deps.py`)

Endpoints declare `get_current_user` as a dependency. If the token is missing, expired, or tampered with, FastAPI immediately aborts the request with `401 Unauthorized` before the controller logic executes:

```python
from fastapi import Depends, HTTPException, status
from app.models.user import User

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user
```

---

## 4. Pydantic v2 Schema Validation

Input validation and output serialization are enforced using Pydantic `BaseModel`. Pydantic guarantees that only valid data enters the domain layer and strips sensitive internal database fields (like `password_hash`) from responses.

### Input Sanitization & Password Strength Rules

```python
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
```

---

## 5. SQLAlchemy 2.0 Declarative Models

QuantWeave uses modern SQLAlchemy 2.0 declarative models with `Mapped[]` type hints.

### The Double-Entry Transaction Ledger (`app/models/portfolio.py`)

Rather than mutating a user's cash balance directly, every financial event is recorded as an immutable row in `portfolio_transactions`:

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), 
        nullable=False
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), 
        nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Types: "DEPOSIT", "WITHDRAWAL", "BUY", "SELL"
    
    shares: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Total cash impact
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    instrument = relationship("Instrument")

    __table_args__ = (
        Index("idx_tx_portfolio_time", "portfolio_id", "timestamp"),
    )
```

---

## 6. Database Migrations with Alembic

Database schemas change over time. QuantWeave tracks schema changes through linear Alembic migrations.

### Running Migrations
```bash
# Apply all pending migrations up to the latest revision
alembic upgrade head

# Rollback the last migration
alembic downgrade -1
```

### Migration Verification Test (`tests/test_postgres_compatibility.py`)
To ensure PostgreSQL compatibility even when running local development on SQLite, a dedicated regression test compiles all SQLAlchemy models against the PostgreSQL dialect:

```python
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from app.core.database import Base

def test_postgresql_ddl_compilation():
    """Validates that all tables compile valid PostgreSQL DDL without errors."""
    for table in Base.metadata.sorted_tables:
        ddl = CreateTable(table).compile(dialect=postgresql.dialect())
        assert ddl is not None
        assert len(str(ddl).strip()) > 0
```

---

## 7. PostgreSQL Concurrency & Transaction Boundaries

In financial applications, race conditions (such as double-spending cash or overselling shares) must be prevented at the database level.

### Transaction Isolation
FastAPI sessions wrapped in `with db.begin():` enforce atomicity:

```python
def process_order(db: Session, portfolio_id: uuid.UUID, order: OrderRequest):
    with db.begin():
        # 1. Lock portfolio row with SELECT ... FOR UPDATE (in PostgreSQL)
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).with_for_update().first()
        
        # 2. Recompute current cash balance from immutable ledger
        current_cash = compute_cash_balance(db, portfolio_id)
        if current_cash < order.total_cost:
            raise InsufficientFundsException("Insufficient cash balance")
            
        # 3. Insert transaction record
        tx = PortfolioTransaction(...)
        db.add(tx)
        # Automatic COMMIT occurs at end of block; automatic ROLLBACK on exception.
```
