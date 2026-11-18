# Security Hardening, Authentication & Production Deployment

This guide outlines the defense-in-depth security model and production deployment infrastructure of **QuantWeave**.

---

## 1. Authentication & Cookie-Based JWT Architecture

QuantWeave implements JSON Web Token (JWT) authentication using cryptographically signed HMAC-SHA256 (`HS256`) tokens.

### Token Delivery Strategy: HttpOnly Cookies vs Bearer Tokens
Many single-page applications store JWTs in browser `localStorage`. However, `localStorage` is accessible to JavaScript, making tokens vulnerable to Cross-Site Scripting (XSS) attacks.

QuantWeave employs **HttpOnly cookies** as its primary authentication channel:
- **`HttpOnly` Flag**: Prevents client-side scripts from reading the token (`document.cookie` cannot access it).
- **`SameSite=Lax`**: Protects against cross-site request forgery while permitting safe top-level navigations.
- **`Secure` Flag**: Enabled automatically in production environments to mandate HTTPS transport.
- **Bearer Header Fallback**: Supported for programmatic API clients and automated tests.

---

## 2. Cross-Site Request Forgery (CSRF) Mitigation

Because browser cookies are automatically attached to cross-origin requests, QuantWeave implements multi-layered CSRF defense:
1. **Custom Header Requirement**: State-mutating API routes (`POST`, `PATCH`, `DELETE`) require custom headers (such as `Content-Type: application/json` or `X-Requested-With`). Standard HTML `<form>` submissions cannot attach custom headers without CORS preflight approval.
2. **CORS Origin Whitelisting**: FastAPI strictly restricts CORS origins via `CORSMiddleware`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.cors_origins, # e.g. ["http://localhost:3000"]
       allow_credentials=True,
       allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
       allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
   )
   ```

---

## 3. Sliding-Window Rate Limiting (`apps/api/app/core/rate_limiter.py`)

To safeguard public and authenticated endpoints against credential stuffing and resource exhaustion, QuantWeave implements an in-memory sliding-window log rate limiter:

### Sliding-Window Algorithm
1. When a request arrives, the client is identified by IP address (or authenticated `user_id`).
2. Current epoch timestamp $t$ is recorded in an in-memory queue for that key.
3. Timestamps older than $t - \text{window\_seconds}$ are purged.
4. If remaining timestamps in the window exceed `max_requests`, the request is rejected with `429 Too Many Requests` and a `Retry-After` header.
5. Periodic garbage collection purges stale buckets to prevent memory leaks.

---

## 4. Multi-Tenant Account & Portfolio Isolation

Every user resource in QuantWeave (portfolios, transactions, saved strategies, chat conversations, theme preferences) is tied directly to a `user_id` foreign key.

```sql
SELECT * FROM portfolios WHERE id = :portfolio_id AND user_id = :current_user_id;
```
If an authenticated user attempts to access a valid `portfolio_id` owned by another user, the query returns zero rows, triggering an immediate `404 Not Found` (or `403 Forbidden`). This prevents resource enumeration and IDOR (Insecure Direct Object Reference) vulnerabilities.

---

## 5. Docker Multi-Stage Containerization

QuantWeave provides a multi-container `docker-compose.yml` orchestrating FastAPI, Next.js, and PostgreSQL:

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: quantweave
      POSTGRES_PASSWORD: quantweave_secure_password
      POSTGRES_DB: quantweave
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    restart: always
    environment:
      ENVIRONMENT: production
      DATABASE_URL: postgresql+psycopg://quantweave:quantweave_secure_password@db:5432/quantweave
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - db
    ports:
      - "8000:8000"

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  pgdata:
```

---

## 6. PostgreSQL Production Runbook & Migration Commands

To deploy against a managed cloud PostgreSQL instance (AWS RDS, Supabase, Neon, or self-hosted):

```bash
# 1. Set production environment variable
export DATABASE_URL="postgresql+psycopg://user:password@hostname:5432/quantweave"

# 2. Run Alembic schema migrations
cd apps/api
alembic upgrade head

# 3. Seed initial reference data (demo equities, mutual funds, financial statements)
python -m app.services.ingestion
```
