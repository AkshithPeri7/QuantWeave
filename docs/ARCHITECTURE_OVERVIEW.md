# QuantWeave — System Architecture Overview

```
                                  +------------------------------------------+
                                  |         Next.js 15 Web Frontend          |
                                  |  (React 19, TypeScript, Tailwind CSS)   |
                                  +--------------------+---------------------+
                                                       |
                                      REST API (JSON)  |  HttpOnly Secure Cookies
                                                       v
+----------------------------------------------------------------------------------------------------+
|                                    FastAPI Backend Application                                     |
|                                                                                                    |
|  +---------------------+  +----------------------+  +---------------------+  +-------------------+ |
|  |  Security / Auth    |  |  Market Data API     |  |  Equity Intelligence|  |  Portfolio Engine | |
|  |  - JWT & Cookies    |  |  - CSV Ingestion     |  |  - Technicals (SMA, |  |  - Append-Only   | |
|  |  - Rate Limiter     |  |  - OHLCV Persistence |  |    EMA, RSI, MACD)  |  |    Ledger (BUY/   | |
|  |  - CSRF Mitigations |  |  - Demo Data Fixtures|  |  - Fundamental Ratios|  |    SELL, WACB)   | |
|  +---------------------+  +----------------------+  +---------------------+  +-------------------+ |
|                                                                                                    |
|  +---------------------+  +----------------------+  +---------------------+  +-------------------+ |
|  |  FundScope Funds    |  |  MarketPulse Wire    |  |  QuantLab Backtest  |  |  AI Copilot       | |
|  |  - Scheme Directory |  |  - News & RSS Feeds  |  |  - Event-Driven Sim |  |  - Orchestrator   | |
|  |  - SIP & CAGR Calc  |  |  - Lexicon Sentiment |  |  - Slippage & Fees  |  |  - Read-Only Tools| |
|  |  - Normalized Chart |  |  - Macro Series      |  |  - Grid Optimizer   |  |  - RAG Retrieval  | |
|  +---------------------+  +----------------------+  +---------------------+  +-------------------+ |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                     SQLAlchemy ORM| psycopg Driver (v3)
                                                   v
+----------------------------------------------------------------------------------------------------+
|                                       PostgreSQL Database                                          |
|                                                                                                    |
|  - Users & Auth Credentials             - MarketPulse News, Sentiments & Macro Series              |
|  - Instruments & OHLCV PriceHistory     - QuantLab Strategies, BacktestRuns & Trades               |
|  - Audited FinancialStatements          - AI Conversations, Messages, ToolExecutions & Evals       |
|  - Portfolios & Transaction Ledgers     - MutualFunds & Historical NAV Series                      |
+----------------------------------------------------------------------------------------------------+
```

---

## 1. System Layers & Technologies

### A. Presentation Layer (Frontend)
- **Framework**: Next.js 15 (App Router) with React 19.
- **Styling**: Tailwind CSS with custom institutional slate/emerald design system.
- **Icons**: Lucide React.
- **Charts**: Custom SVG visualizations for historical equity curves, Bollinger Bands, normalized fund charts, and backtest drawdowns.
- **API Client**: Strongly typed TypeScript wrapper (`lib/api.ts`) managing token persistence, `X-Requested-With` headers for CSRF mitigation, and automatic error handling.

### B. Application & API Layer (Backend)
- **Framework**: FastAPI (Python 3.12+).
- **Type Safety**: Pydantic v2 schemas for strict input/output serialization and validation.
- **Dependency Injection**: Reusable dependencies for database session lifecycle (`get_db`), user authentication (`get_current_user`), and sliding-window rate limiting.
- **Asynchronous Concurrency**: Non-blocking request handling with threadpool offloading for CPU-bound numerical tasks.

### C. Financial Analytics & Modeling Engines
- **NumPy & Pandas**: Vectorized financial calculations with strict chronological ordering to prevent lookahead bias.
- **Technical Engine (`app.analytics.technical`)**: SMA (20, 50, 200), EMA (12, 26), RSI 14 (Wilder's exponential smoothing), MACD (12, 26, 9), and Bollinger Bands (20, 2).
- **Ledger Engine (`app.services.portfolio`)**: Weighted-Average Cost Basis (WACB), realized/unrealized P&L, negative cash prevention, and oversell protection.
- **Performance Engine (`app.analytics.portfolio_analytics`)**: Time-Weighted Return (TWR) cash flow isolation, Money-Weighted Extended Internal Rate of Return (XIRR) with Newton-Raphson solver, annualized volatility, and Sharpe Ratio (Rf=6%).
- **Backtesting Engine (`app.analytics.backtesting`)**: Event-driven bar-by-bar simulation, next-bar Open pricing, transaction fees, slippage modeling, and In-Sample / Out-of-Sample grid search.

### D. Storage & Data Persistence Layer
- **Database**: PostgreSQL 16+ (with SQLite fallback for local test suites).
- **ORM**: SQLAlchemy 2.0 with type-annotated `Mapped` attributes.
- **Driver**: `psycopg` (v3).
- **Migrations**: Alembic with linear revision tracking from `9ee3a29b8445` to `f6a1b2c3d4e5`.

---

## 2. Multi-Layer Security Architecture

### A. Authentication & Session Management
- **Password Hashing**: Passlib with bcrypt and secure salt rounds.
- **Token Format**: HS256 JWT containing user ID (`sub`), role, and expiration timestamp.
- **Cookie Security**: HttpOnly, Secure, SameSite=Lax cookies preventing JavaScript client-side exfiltration.

### B. CSRF Defense
- For cookie-authenticated state mutations (POST, PUT, PATCH, DELETE), FastAPI dependency inspects:
  1. `Content-Type: application/json` or `multipart/form-data`.
  2. `X-Requested-With: XMLHttpRequest` custom header.
  3. Valid allowed Origin matching CORS whitelist.

### C. Sliding-Window Rate Limiting
- In-memory sliding-window limiter (`app.core.rate_limiter`) tracking timestamped buckets per client IP:
  - Login route: 15 requests / minute.
  - AI chat route: 25 requests / minute.
  - QuantLab backtests: 20 requests / minute.
  - Parameter grid searches: 10 requests / minute.
- Automatic background cleanup purging expired IP buckets to prevent memory leaks.

### D. Input Hardening & CSV Sanitization
- File upload checks rejecting null bytes (`\x00`), binary executables, and files exceeding 10MB.
- Rejection of spreadsheet formula injection characters (`=`, `+`, `-`, `@`).

### E. AI Copilot Guardrails
- **Read-Only Server-Side Tools**: Zero mutate/delete tools exposed to LLM.
- **Strict User Scoping**: Authenticated `context_user_id` injected server-side by FastAPI, never accepted from LLM arguments.
- **Deterministic Number Grounding**: All figures originate from verified Python analytics engines.
- **Injection Pattern Defenses**: Refusal of override patterns (`"ignore previous"`, `"system prompt override"`, `"admin password"`).

---

## 3. Core Data Flow Walkthroughs

### 1. Portfolio Transaction & Valuation Flow
```
User records BUY -> Route validates CSRF & Auth -> PortfolioService verifies cash balance
  -> Checks idempotency key -> Computes WACB -> Inserts PortfolioTransaction record
  -> PortfolioAnalyticsService reconstructs ledger -> Generates real-time valuation & equity curve
```

### 2. AI Copilot Intelligent Retrieval Flow
```
User submits prompt -> AIOrchestrator records user turn -> Mock/Gemini/OpenAI Provider
  -> RAGRetrievalService searches 11 methodology chunks -> Intent parser extracts tool calls
  -> Tools execute read-only queries with context_user_id -> Provider synthesizes verified answer
  -> RAG citations + Educational Disclaimer appended -> Persisted in ai_messages & ai_tool_executions
```
