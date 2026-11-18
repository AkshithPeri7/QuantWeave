# QuantWeave — Production Deployment Guide

This guide details deployment options for QuantWeave across Docker Compose, self-hosted Linux servers, and cloud platform providers (Vercel, Railway, and Render).

---

## 1. Environment Configuration

Create a production `.env` file in the project root based on `.env.example`:

```bash
# =========================================================================
# QuantWeave Production Environment Configuration
# =========================================================================

# Environment Mode: "production" or "development"
ENVIRONMENT=production

# Security: Secret key for signing HS256 JWT tokens (Must be >= 32 characters in production)
SECRET_KEY=ChangeThisInProductionToAStrongRandom64ByteHexOrBase64StringForSecurityHS256!

# Database Connection (PostgreSQL with psycopg v3 driver)
DATABASE_URL=postgresql+psycopg://quantweave_user:SecurePassword123@db:5432/quantweave_db

# CORS Configuration: Whitelisted Frontend Origins
CORS_ORIGINS=["http://localhost:3000","https://quantweave.example.com"]

# Educational Demo Mode Flag
DEMO_MODE=true

# AI Provider Configuration: "mock", "gemini", "openai"
AI_PROVIDER=mock
GEMINI_API_KEY=
OPENAI_API_KEY=

# Public API URL for Web Client
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 2. Docker Compose Deployment (Recommended)

QuantWeave includes an orchestrated multi-container `docker-compose.yml` for unified local or production deployments.

### Multi-Container Topology
```
           +-----------------------+
           |   Host / Cloud Load   |
           |       Balancer        |
           +-----------+-----------+
                       |
       +---------------+---------------+
       |                               |
       v (Port 3000)                   v (Port 8000)
+---------------+              +---------------+
|   Next.js     |              |   FastAPI     |
|   Web UI      |              |   Backend     |
+---------------+              +-------+-------+
                                       |
                                       v (Port 5432 - Internal Only)
                               +---------------+
                               |  PostgreSQL   |
                               |  Database     |
                               +---------------+
```

### Steps to Deploy
```bash
# 1. Clone repository
git clone https://github.com/your-username/QuantWeave.git
cd QuantWeave

# 2. Configure production secrets
cp .env.example .env
# Edit .env with secure production values

# 3. Build and launch services in background
docker compose up -d --build

# 4. Apply database migrations to PostgreSQL
docker compose exec api alembic upgrade head

# 5. Seed initial reference market data
docker compose exec api python -c "
from app.core.database import SessionLocal
from app.services.ingestion import seed_demo_market_data
from app.providers.financial_fixtures import seed_demo_financial_statements
from app.providers.fund_fixtures import seed_demo_mutual_funds
from app.services.news_ingestion import NewsIngestionService

db = SessionLocal()
seed_demo_market_data(db)
seed_demo_financial_statements(db)
seed_demo_mutual_funds(db)
NewsIngestionService.seed_demo_market_pulse(db)
db.close()
print('Initial reference fixtures seeded successfully.')
"
```

### Verifying Service Health
```bash
# Inspect container status
docker compose ps

# Check API health endpoint
curl http://localhost:8000/api/v1/health

# Check Database connectivity
curl http://localhost:8000/api/v1/health/db
```

---

## 3. Cloud Provider Deployment

### A. Frontend on Vercel
1. Link your GitHub repository to Vercel.
2. Set Root Directory to `apps/web`.
3. Framework Preset: Next.js.
4. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL`: URL of your deployed backend (e.g. `https://api.quantweave.example.com`).
5. Deploy.

### B. Backend on Railway or Render
1. Set Root Directory to `apps/api`.
2. Environment: Python 3.12 or 3.13.
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`.
5. Attach a managed PostgreSQL database and link `DATABASE_URL`.
6. Add Pre-Deploy Command: `alembic upgrade head`.

---

## 4. Production Rollback Procedure

If a deployed revision introduces an unexpected regression:

```bash
# 1. Revert container code to previous Git checkpoint
git checkout <previous_stable_commit>
docker compose up -d --build

# 2. Downgrade database schema if migration was problematic
docker compose exec api alembic downgrade -1

# 3. Verify health
curl -f http://localhost:8000/api/v1/health || echo "Health check failed!"
```
