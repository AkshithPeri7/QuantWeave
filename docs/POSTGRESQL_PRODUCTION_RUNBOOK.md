# QuantWeave — PostgreSQL Production Database Runbook

This runbook defines operational guidelines, connection pooling, migration procedures, disaster recovery protocols, and performance tuning for QuantWeave running on PostgreSQL in production.

---

## 1. Production Driver & Connection Architecture

QuantWeave standardizes on **`psycopg` (v3)** as its asynchronous-ready, high-performance PostgreSQL driver for Python 3.12+.

### Connection URL Scheme
```bash
# Standard Production Connection String
DATABASE_URL=postgresql+psycopg://<username>:<password>@<db-host>:5432/<database_name>
```

### Engine Pool Configuration
Configured in `app/core/database.py`:
```python
engine = create_engine(
    settings.database_url,
    pool_size=10,             # Persistent pool connections per worker process
    max_overflow=20,          # Temporary burst connections during traffic spikes
    pool_timeout=30,          # Seconds to wait before failing on connection starvation
    pool_recycle=1800,        # 30-minute connection recycle to prevent stale TCP sockets
    pool_pre_ping=True,       # Liveness health-check ("SELECT 1") before checkout
)
```

---

## 2. Linear Migration Architecture

Database schema evolution is strictly versioned through linear Alembic migrations.

### Complete Linear Revision Chain
```
9ee3a29b8445 (Initial Core Schema: users, instruments, price_history, data_sources, ingestion_runs)
      │
      ▼
35b3591b794d (Financial Statements & Fundamental Line Items)
      │
      ▼
a1b2c3d4e5f6 (Portfolio Ledger, Holdings & Transactions)
      │
      ▼
b2c3d4e5f6a1 (FundScope Mutual Funds, NAV History & Categories)
      │
      ▼
c3d4e5f6a1b2 (MarketPulse News Articles, Sentiment, Macro Series & Alerts)
      │
      ▼
d4e5f6a1b2c3 (QuantLab Research Strategies, Backtest Runs & Trades)
      │
      ▼
e5f6a1b2c3d4 (Portfolio Ledger Integrity & Foreign Key Indexes)
      │
      ▼
f6a1b2c3d4e5 (AI Copilot Conversations, Messages, Tool Executions, RAG Sources, Evals) [HEAD]
```

### Applying Migrations in Production
```bash
# Navigate to API root
cd apps/api

# Check current migration revision
alembic current

# Run migrations to head
alembic upgrade head

# Verify status
alembic check
```

---

## 3. High-Performance Indexing Strategy

QuantWeave relies on tailored indexes to ensure sub-10ms query execution across historical market timelines:

1. **`price_history`**:
   - `ix_price_history_instrument_trade_date`: Composite unique index on `(instrument_id, trade_date)` for zero-lookahead chronological pricing.
2. **`fund_nav_history`**:
   - `ix_fund_nav_fund_id_date`: Composite unique index on `(fund_id, nav_date)` for fast NAV range queries.
3. **`portfolio_transactions`**:
   - `ix_portfolio_tx_portfolio_date`: Composite index on `(portfolio_id, trade_date, created_at)` for instant WACB ledger reconstruction.
4. **`news_articles` & `news_sentiment`**:
   - `ix_news_articles_published_at`: Reverse chronological index on `published_at DESC`.
   - `ix_news_sentiment_article_id`: One-to-one foreign key index.
5. **`ai_messages` & `ai_tool_executions`**:
   - `ix_ai_messages_conversation_created`: Ordered retrieval by `(conversation_id, created_at ASC)`.
   - `ix_ai_tool_executions_message_id`: Fast lookup of tool telemetry per turn.

---

## 4. Disaster Recovery & Backup Protocol

### Daily Automated Backup (Custom Format)
```bash
# Run automated backup with pg_dump custom compressed format (-Fc)
pg_dump -h <db-host> -U quantweave_prod -d quantweave_db -Fc -f "/var/backups/quantweave_$(date +%Y%m%d_%H%M%S).dump"
```

### Safe Restoration Runbook
```bash
# 1. Stop web application services to prevent conflicting transactions
docker compose stop api web

# 2. Terminate active database connections
psql -h <db-host> -U postgres -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'quantweave_db' AND pid <> pg_backend_pid();"

# 3. Clean and restore from backup file
pg_restore -h <db-host> -U postgres -d quantweave_db --clean --if-exists --no-owner "/var/backups/quantweave_TARGET.dump"

# 4. Run Alembic migration check
alembic upgrade head

# 5. Restart application services
docker compose start api web
```

---

## 5. Production Health Monitoring Queries

Run these diagnostic queries via `psql` to audit live database health:

```sql
-- 1. Active Connections by Client State
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname = 'quantweave_db' 
GROUP BY state;

-- 2. Slow Queries (> 200ms)
SELECT pid, now() - query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - query_start) > interval '200 milliseconds' 
  AND state != 'idle';

-- 3. Cache Hit Ratio (Should be > 99%)
SELECT 
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_pct 
FROM pg_statio_user_tables;
```
