# QuantWeave — What Needs to Be Built

## Current status
This ZIP is a **starter scaffold and specification**, not a finished application. The repository contains a Next.js landing-page shell, a FastAPI health endpoint, SQL schema and design documentation. The following features must be implemented and tested.

## MVP — build first (in this order)
1. **Project foundation:** local setup, PostgreSQL Docker service, SQLAlchemy models, Alembic migrations, environment configuration, CI, linting and tests.
2. **Accounts:** sign up/sign in, secure password hashing, sessions/tokens, profile and authorization on private resources.
3. **Market data:** instrument master, provider adapter, synthetic demo data, daily OHLCV ingestion, freshness timestamps and source attribution.
4. **Equity dashboard:** stock search, company details, price chart, SMA/EMA/RSI indicators, comparisons and carefully sourced financial ratios.
5. **Portfolio manager:** portfolios, deposits/withdrawals, buy/sell transaction ledger, derived holdings, cost basis, P&L, allocation and return calculations.
6. **Mutual funds (FundScope):** fund search, NAV history, NAV charts, returns, SIP simulator and comparison.
7. **QuantWeave Copilot v1:** read-only tools to explain backend-calculated values, source links, as-of dates, missing-data messages and basic evaluation tests.
8. **Release quality:** responsive design, loading/error/empty states, demo mode, security checks, unit/integration/E2E tests, deployment and polished README/screenshots.

## Phase 2 — advanced features
9. **MarketPulse:** permitted news feeds, article deduplication, event classification, entity extraction and sentiment with confidence and evaluation.
10. **QuantLab:** constrained strategy definitions, SMA/RSI backtests, fees/slippage, no look-ahead bias, trade ledger, equity curve and reproducibility.
11. **Paper trading:** virtual cash, virtual orders, positions and performance; **no live broker execution**.
12. **Advanced analytics:** volatility, beta, Sharpe, maximum drawdown, portfolio stress tests and fund holdings overlap when reliable dated data exists.
13. **AI v2:** cross-module grounded research summaries and retrieval over permitted documents with citations.

## Main screens
- Landing, registration/login, dashboard
- Market explorer, stock details, compare stocks
- Portfolio list, portfolio details, add transaction, risk view
- Mutual fund explorer, fund details, SIP calculator, compare funds
- MarketPulse feed and article/event details
- QuantLab strategy builder, backtest results, paper account
- QuantWeave Copilot chat, settings, data-source/status page

## Suggested module boundaries
`auth`, `market`, `equity`, `portfolio`, `funds`, `news`, `quantlab`, `paper`, `ai`, `admin`.

## Completion rule
A feature is complete only when its API, UI, database migration, authorization, input validation, tests, loading/error states and documentation work together. Do not treat a mock screenshot as a completed feature.

## Safety and correctness
Backend code calculates all financial metrics. AI may explain only retrieved calculations and must show dates/sources. Clearly mark demo/synthetic data. Do not promise returns, provide personalized trading recommendations, or connect live-money orders in the initial release.
