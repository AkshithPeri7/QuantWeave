# Implementation Roadmap

This roadmap is sequential. Do not start a later phase until the preceding phase's acceptance criteria pass.

## Phase 0 — repository and tooling
- [x] Confirm Python (3.13.1), Node (v24.15.0), npm (11.12.1). (Docker not detected in environment; SQLite fallback verified).
- [x] Run frontend and backend scaffolds.
- [x] Configure PostgreSQL docker-compose and local migration infrastructure.
- [x] Add CI/test scripts for backend pytest (21 tests) and frontend Next.js production build (13 static routes).

## Phase 1 — foundation
- [x] FastAPI config, logging, CORS, health.
- [x] SQLAlchemy engine/session and declarative base.
- [x] Alembic initial migration (9ee3a29b8445 creating users table with UUID primary key).
- [x] User model and secure authentication (bcrypt password hashing, JWT access/refresh tokens, HttpOnly cookie support).
- [x] Authenticated /api/v1/users/me and /api/v1/auth/me endpoints.
- [x] Frontend shell, responsive layout, and typed API client.
- [x] Frontend sign-in and register pages with validation and error handling.
- [x] Tests (21 pytest unit/integration tests passing).

## Phase 2 — market data
- [x] Instrument model, repository, and CRUD/search endpoints.
- [x] Provider interface (BaseMarketDataProvider) and DemoMarketDataProvider with deterministic data for 10 liquid Indian equities.
- [x] Price history model with Decimal/NUMERIC financial fields and idempotent upsert.
- [x] Ingestion run tracking with IngestionRun model recording status, records processed, failures, and timestamp ranges.
- [x] DataSource tracking with provider name, source type, and update timestamps.
- [x] CSV market data import service with strict validation (OHLC invariants, volume >= 0, date formats).
- [x] Interactive frontend search, equity intelligence directory, and instrument detail pages with responsive SVG price/volume charts and date-range filters (1M, 3M, 6M, 1Y, ALL).
- [x] Validation tests (34 pytest unit/integration tests passing; duplicate ingestion, invalid OHLC, pagination, search, migrations verified).

## Phase 3 — Equity MVP
- [x] Stock search and detailed instrument profiles with exchange & sector metadata.
- [x] Historical price API and responsive SVG financial chart with period filters.
- [x] Pure technical indicator analytics engine (SMA 20/50/200, EMA 12/26, Wilder RSI 14, MACD 12/26/9, Bollinger Bands 20/2) with look-ahead bias prevention.
- [x] Financial statements model, Alembic migration, and deterministic synthetic multi-year accounting fixtures.
- [x] Fundamental ratios engine (P/E, P/B, ROE, Gross/Operating/Net Margins, Debt/Equity, Current Ratio) with zero-division safeguards.
- [x] Multi-instrument equity comparison engine and dedicated comparison page (/equity/compare) for up to 4 equities with normalized return charts, volatility, drawdown, and aligned metrics.
- [x] Equity test suite (50 total pytest tests passing covering technical indicator math, fundamental ratios, comparison alignment, and security audits; Next.js 15 production build verified).

## Phase 4 — Portfolio MVP
- [x] Portfolio CRUD with owner-isolation.
- [x] Transaction ledger (BUY, SELL, DIVIDEND, CASH_DEPOSIT, CASH_WITHDRAWAL) with overselling protection and idempotency keys.
- [x] Derived holdings with Weighted-Average Cost Basis (WACB).
- [x] Daily valuation timeline and unrealized/realized P&L.
- [x] Time-Weighted Return (TWR) and Money-Weighted Return (XIRR) numerical solvers.
- [x] Risk metrics (volatility, Sharpe ratio with Rf=6.0%, max drawdown) and asset/sector allocations.
- [x] Portfolio tests (59 pytest unit/integration tests passing).

## Phase 5 — FundScope
- [x] Scheme search, directory pagination, and category filtering (Equity, Debt, Hybrid).
- [x] NAV history ingestion with Decimal precision and interactive SVG charts.
- [x] Returns analytics (Absolute return, 1Y/2Y/3Y/5Y CAGR with minimum history safeguards).
- [x] Monthly SIP and Lump-Sum wealth compounding calculators with monthly installment projections.
- [x] Multi-fund side-by-side comparison engine (up to 4 schemes).
- [x] FundScope tests (73 pytest unit/integration tests passing).

## Phase 6 — MarketPulse
- [x] Financial news feed with category filtering, sentiment tags, and ticker tagging.
- [x] Explainable financial sentiment engine (-1.0 to +1.0) with negation and intensifier windows.
- [x] Macroeconomic indicator tracking (CPI Inflation, RBI Repo Rate, GDP Growth) with historical series charts.
- [x] User watchlists with cross-user isolation and custom price/sentiment alert engine.
- [x] MarketPulse tests (87 pytest unit/integration tests passing).

## Phase 7 — QuantLab
- [x] Strategy interface with versioned JSON parameter schemas (SMA, EMA, RSI, Buy-and-Hold).
- [x] Event-driven historical backtesting engine with next-bar Open pricing, fees, and slippage modeling.
- [x] Quantitative performance analytics (CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor).
- [x] Trade log analysis and equity/drawdown curve visualization.
- [x] Parameter grid search optimizer with In-Sample / Out-of-Sample train/test split and overfitting warnings.
- [x] Multi-run side-by-side performance comparison.
- [x] QuantLab tests (100 pytest unit/integration tests passing).

## Phase 8 — AI Financial Copilot & Intelligent Research
- [x] Modular LLM provider abstraction (`BaseLLMProvider`, `MockLLMProvider`, `GoogleGeminiProvider`, `OpenAIProvider`, `get_llm_provider`).
- [x] 22 server-side typed read-only financial tools across Equity, Portfolio, FundScope, MarketPulse, and QuantLab.
- [x] Strict user isolation on portfolio and backtesting tools (`context_user_id` injected server-side).
- [x] Retrieval-Augmented Generation (RAG) over authoritative platform methodology and formula chunks with `[DOC-...]` citations.
- [x] Relational persistence schema (`ai_conversations`, `ai_messages`, `ai_tool_executions`, `ai_retrieval_sources`, `ai_evaluation_runs`) with Alembic migration `f6a1b2c3d4e5`.
- [x] REST APIs under `/api/v1/ai` (conversations, messages, tool catalog, benchmark evaluation).
- [x] Next.js 15 Copilot workspace (`/ai`) with conversational sidebar, markdown streaming, tool execution inspector, source citations, suggested prompts, and copy feedback.
- [x] Contextual "Explain with Copilot" links embedded across Equity, Instruments, Portfolio, FundScope, MarketPulse, and QuantLab.
- [x] Security guardrails: prompt injection refusal, max 5 tool executions per turn, mandatory SEBI educational research disclaimer.
- [x] Automated benchmark evaluation suite (9 standard test cases + prompt injection refusal).
- [x] Milestone 8 tests: 16 AI tests passing, 116 total backend tests passing, Next.js production build clean.

## Phase 9 — release
- [ ] End-to-end tests.
- [ ] Security review.
- [ ] Performance baseline.
- [ ] Demo deployment.
- [ ] Screenshots/demo video.
- [ ] Final architecture and user documentation.
