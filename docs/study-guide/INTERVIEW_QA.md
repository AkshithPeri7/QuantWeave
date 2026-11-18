# QuantWeave — 40+ Technical Interview Questions & In-Depth Answers

This document contains over 40 technical interview questions spanning system design, concurrency, relational ledgers, quantitative algorithms, frontend performance, AI safety, and security.

---

## Domain 1: System Design & Relational Ledger Architecture

### Q1: Why did you design the portfolio system using an append-only transaction ledger instead of mutable user balances?
**Answer**: In financial applications, mutable state (e.g. `UPDATE portfolios SET cash = cash - 5000`) creates major auditability and race condition vulnerabilities. If a balance drops or corrupts, there is no historical record explaining how the balance reached that state. QuantWeave adopts an append-only ledger (`portfolio_transactions`). Every cash deposit, withdrawal, stock purchase, and stock sale is recorded as an immutable ledger event with an `idempotency_key`. The user's current cash and holdings are deterministically computed on-the-fly via mathematical reduction, guaranteeing perfect auditability.

### Q2: How do you prevent double-spending or duplicate transactions if a network timeout occurs?
**Answer**: QuantWeave implements client-generated `idempotency_key` UUIDs for all state-mutating transactions. When an order is submitted, the API checks for the existence of the key within a database transaction. If the key already exists, the server rejects the duplicate request and returns the original transaction receipt, preventing network retry duplication.

### Q3: What database isolation level is required for portfolio order execution?
**Answer**: Read Committed with explicit row-level locking (`SELECT ... FOR UPDATE` in PostgreSQL) or Serializable isolation. In QuantWeave, order processing runs inside an atomic transaction block that locks the portfolio record, verifies available cash from the ledger, and inserts the transaction before committing.

### Q4: How does QuantWeave support both local development and cloud production without code changes?
**Answer**: QuantWeave utilizes SQLAlchemy 2.0 with the `psycopg` (v3) driver. The application reads `DATABASE_URL` dynamically from the environment. When set to SQLite (`sqlite:///...`), it configures `connect_args={"check_same_thread": False}`. In production, pointing `DATABASE_URL` to PostgreSQL automatically utilizes native PostgreSQL features without modifying domain services.

### Q5: How do you handle schema evolution across multiple deployment stages?
**Answer**: Through linear Alembic migrations. Every schema modification (e.g. adding the `user_preferences` table) is captured in a timestamped Python migration script with explicit `upgrade()` and `downgrade()` methods. CI pipelines run `alembic upgrade head` before booting server processes.

---

## Domain 2: Python Backend, Concurrency & FastAPI

### Q6: Why did you choose FastAPI over Flask or Django for this platform?
**Answer**: FastAPI provides asynchronous request handling via Starlette, automatic request validation and serialization via Pydantic v2, and dependency injection out of the box. For financial systems, automatic type enforcement eliminates entire categories of type-coercion bugs, and OpenAPI documentation is generated automatically.

### Q7: What is the purpose of FastAPI's lifespan context manager in `app/main.py`?
**Answer**: The lifespan manager executes startup and shutdown logic. On startup, it checks database health and automatically seeds reference equities, financial statements, and mutual funds if the database is unpopulated. On shutdown, it cleans up open connection pools gracefully.

### Q8: How does FastAPI's dependency injection (`Depends`) improve testability?
**Answer**: Dependency injection allows replacing real production dependencies (like a PostgreSQL database or cloud LLM provider) with test doubles (like in-memory SQLite sessions or mock AI handlers) via `app.dependency_overrides` during unit tests, without changing a single line of production code.

### Q9: Why is `check_same_thread: False` needed for SQLite in FastAPI?
**Answer**: In FastAPI, asynchronous endpoints execute on an event loop while synchronous operations run in thread pools. By default, Python's SQLite driver raises an exception if a connection created on one thread is accessed by another. Setting `check_same_thread: False` enables multi-threaded connection sharing in memory.

### Q10: How do you handle unhandled server exceptions without leaking internal stack traces?
**Answer**: In `app/main.py`, a global exception handler catches `Exception`, logs the full stack trace and request metadata to internal secure logs, and returns a sanitized JSON response: `{"detail": "An internal server error occurred. Please try again later."}` with status code 500.

---

## Domain 3: Frontend Architecture, React 19 & Next.js 15

### Q11: Why does QuantWeave use the Next.js 15 App Router instead of the legacy Pages router?
**Answer**: The App Router introduces React Server Components (RSC) and nested layouts. Layout shells (like the sidebar and navigation) persist across page transitions without re-rendering, and route groups `(dashboard)` cleanly organize authenticated routes without polluting the URL structure.

### Q12: How does the 4-theme system prevent Flash of Unstyled Content (FOUC)?
**Answer**: Themes are implemented using CSS custom properties (`--bg-primary`, `--accent-primary`) attached to a `[data-theme]` attribute on the `<html>` root. A synchronous script runs in `layout.tsx` before DOM paint, reading `localStorage` and setting `data-theme` immediately, preventing white flashes on dark themes.

### Q13: How does `UserProfileMenu.tsx` ensure that dropdown menus are never clipped off-screen?
**Answer**: The menu is positioned dynamically using upward anchoring (`bottom-full mb-2`) from the bottom sidebar trigger. Furthermore, it enforces responsive max-width bounds (`max-w-[calc(100vw-24px)]`) and ARIA menu semantics, closing automatically upon detecting an `Escape` key press.

### Q14: How are client-side API requests authenticated in Next.js?
**Answer**: The browser automatically transmits HttpOnly cookies with every same-origin API request (`credentials: "include"`). For development environments where frontend and backend run on different ports, the API client attaches `X-Requested-With: XMLHttpRequest` and respects CORS origin whitelisting.

### Q15: How do you achieve type synchronization between backend and frontend?
**Answer**: The frontend maintains TypeScript interfaces in `apps/web/lib/types.ts` that mirror backend Pydantic schemas (e.g. `PortfolioSummary`, `HoldingItem`, `BacktestResult`), ensuring compile-time type safety across the network boundary.

---

## Domain 4: Quantitative Finance & Mathematics

### Q16: What is the difference between Time-Weighted Return (TWR) and Money-Weighted Return (MWR / XIRR)?
**Answer**: TWR measures the compound rate of growth of a portfolio by breaking the timeline into sub-periods at each cash flow, eliminating the impact of deposit/withdrawal timing. XIRR (Money-Weighted Return) solves for the internal rate of return where the NPV of all cash flows equals zero, reflecting the actual personal investor experience based on cash flow timing.

### Q17: How does your XIRR solver guarantee numerical convergence on irregular cash flows?
**Answer**: QuantWeave implements the **Newton-Raphson method** using the first derivative of the NPV polynomial. Because non-linear cash flows can create local extrema where Newton-Raphson oscillates or diverges, QuantWeave monitors iteration count. If convergence is not reached within 50 iterations, it automatically falls back to **Bisection Search** over bracket $[-0.99, 10.0]$, mathematically guaranteeing convergence.

### Q18: What is Wilder's smoothing, and why is it preferred over a simple moving average for RSI?
**Answer**: Wilder's smoothing uses an exponential decay factor of $\alpha = 1/N$ (compared to standard EMA's $\alpha = 2/(N+1)$). Unlike an SMA, which abruptly drops old values at period $N$ causing artificial "step" movements, Wilder's smoothing continuously incorporates all past history with decaying weights, creating a smooth and responsive oscillator.

### Q19: How does QuantWeave safeguard against division-by-zero in financial ratios?
**Answer**: In `apps/api/app/services/analytics.py` and `fundamentals.py`, all ratio functions check denominators before division. For instance, in P/E ratios, if EPS $\le 0$, the ratio returns `None` rather than raising a ZeroDivisionError or returning infinity. Similarly, if 14 days of prices are identical ($\text{AvgGain}=0$ and $\text{AvgLoss}=0$), RSI safely returns $50.0$.

### Q20: Why does QuantWeave suppress CAGR for holding periods under 365 days?
**Answer**: Annualizing returns over short durations produces extreme statistical distortion (e.g. a 3% gain in 7 days annualizes to over 350%). QuantWeave only computes CAGR when the duration exceeds 365 days; otherwise, it reports the absolute holding period return.

---

## Domain 5: Algorithmic Simulation & QuantLab

### Q21: What is look-ahead bias, and how does QuantLab eliminate it?
**Answer**: Look-ahead bias occurs when a trading algorithm uses future price information to make current trading decisions. In many naive backtesters, signals calculated at Day $t$'s Close are filled at Day $t$'s Close (which is impossible in reality). QuantLab strictly enforces **next-bar Open execution**: signals are generated on bar $t$'s Close, and trades are filled at the Open price of bar $t+1$.

### Q22: How does QuantLab model execution slippage and exchange commissions?
**Answer**: QuantLab applies a slippage penalty to fill prices ($P \times (1 + \text{slippage})$ for buys, $P \times (1 - \text{slippage})$ for sells) to model bid-ask spread and market impact. In addition, it deducts transaction fees (brokerage, STT, exchange turnover) on every executed order.

### Q23: Why is Sortino ratio often a superior metric to Sharpe ratio for equity strategies?
**Answer**: The Sharpe ratio penalizes both upside volatility and downside volatility equally. For equity strategies, high upside volatility (large sudden gains) is desirable. The Sortino ratio only penalizes downside deviations below a minimum acceptable return (risk-free rate), providing a truer assessment of harmful risk.

### Q24: How does QuantLab prevent server denial-of-service during grid search parameter optimization?
**Answer**: In `apps/api/app/services/quantlab_engine.py`, the Cartesian product of parameter combinations is calculated before execution. If `total_combinations > 100`, the engine immediately rejects the request with a 400 Bad Request error, preventing CPU starvation.

### Q25: How do you identify whether a backtested trading strategy is overfitted?
**Answer**: By performing In-Sample (Train) and Out-of-Sample (Test) splits. If a strategy achieves a Sharpe of 2.8 on training data but drops to negative returns on unseen test data, the strategy has memorized historical noise rather than discovered generalizable market alpha.

---

## Domain 6: Financial AI Copilot & Tool Orchestration

### Q26: Why should Large Language Models never perform financial calculations directly?
**Answer**: LLMs are probabilistic language models prone to mathematical hallucinations, calculation drift, and rounding errors. In financial applications, numbers must be exact and auditable. QuantWeave forces the AI Copilot to invoke deterministic Python tool functions for all analytics and calculations.

### Q27: How do you prevent a user from asking the AI Copilot to access another user's portfolio?
**Answer**: The tool execution router in `apps/api/app/services/ai_tools.py` intercepts all tool calls. For any user-scoped tool (`get_portfolio_summary`), the server ignores any `user_id` passed by the model and injects the authenticated `user_id` extracted from the user's verified JWT token.

### Q28: How does QuantWeave defend against prompt injection attacks?
**Answer**: QuantWeave uses hardened system prompt instructions with clear operational boundaries, restricts tool calling to a strictly read-only whitelist, and isolates user inputs in structured conversational schemas. Destructive actions (like submitting orders or deleting accounts) are not available to the AI agent.

### Q29: What is the purpose of the deterministic `mock` AI provider?
**Answer**: The mock provider enables instant, 100% reproducible testing without external network dependencies, API subscription keys, or cloud costs. It simulates tool calls, responses, and citations, allowing full test suite execution in CI/CD environments.

### Q30: How does the AI Copilot generate verifiable citations?
**Answer**: The semantic RAG service indexes curated technical documents with chunk metadata. When a chunk is retrieved and injected into the model's context, the agent must reference the explicit section title and chunk identifier in its final markdown response.

---

## Domain 7: Security Hardening & Rate Limiting

### Q31: Why are HttpOnly cookies superior to browser `localStorage` for JWT tokens?
**Answer**: Tokens stored in `localStorage` are fully accessible to any client-side JavaScript executing in the origin, leaving them vulnerable to theft via Cross-Site Scripting (XSS). HttpOnly cookies cannot be accessed or read by client JavaScript, neutralizing token exfiltration.

### Q32: How does QuantWeave defend against Cross-Site Request Forgery (CSRF)?
**Answer**: QuantWeave pairs `SameSite=Lax` cookies with strict CORS origin validation and requires custom JSON request headers (`Content-Type: application/json` and `X-Requested-With`) on all state-mutating HTTP methods.

### Q33: How does the sliding-window rate limiter operate?
**Answer**: It maintains an in-memory queue of request timestamps per client IP. Upon each request, timestamps older than the sliding window (e.g. 60 seconds) are dropped. If the count of recent timestamps exceeds the threshold, the request is rejected with `429 Too Many Requests`.

### Q34: What password hashing algorithm is used, and why?
**Answer**: QuantWeave uses **bcrypt** with a dynamic salt and cost factor of 12. Bcrypt is a computationally intensive, memory-hard key derivation function specifically designed to resist brute-force and GPU dictionary attacks.

### Q35: How do you protect against CSV upload attacks in equity data ingestion?
**Answer**: In `apps/api/app/api/routes/instruments.py`, uploaded files are validated for size limits (5MB maximum), inspected for null-byte injections, verified for UTF-8 encoding, and parsed using strict Pydantic row validation schemas before database insertion.

---

## Domain 8: Testing, DevOps & Quality Assurance

### Q36: How many tests are in the backend regression suite, and what do they cover?
**Answer**: The backend suite comprises 144 passing unit, integration, and security tests covering: authentication, multi-tenant isolation, portfolio ledgers, XIRR solvers, technical indicators, mutual fund CAGR, QuantLab backtesting, AI tool calling, RAG retrieval, CSRF hardening, and rate limiting.

### Q37: How do you perform end-to-end browser testing without UI flakiness?
**Answer**: QuantWeave uses **Playwright** (`run_playwright_e2e.py`) to launch headless Chromium, log in a test user, inspect layout bounding boxes, verify zero clipping across mobile (390px), tablet (768px), and desktop viewports, and capture high-resolution screenshots.

### Q38: Why did Pyrefly report `Cannot find module playwright.sync_api`, and how was it solved?
**Answer**: Pyrefly defaulted to the system Python interpreter where Playwright was not installed. The issue was resolved by adding `pyrefly.toml` and `.vscode/settings.json` explicitly configuring Pyrefly to use the virtual environment interpreter (`apps/api/.venv/Scripts/python.exe`) and documenting `playwright` in `requirements-dev.txt`.

### Q39: Why does running Next.js production builds in sandboxed environments occasionally trigger EPERM errors?
**Answer**: On Windows, sandboxed container filesystem filters sometimes restrict deep directory creation by Node.js worker threads inside `.next/server/app/`. Running the build with proper permissions or cleaning stale `.next` lockfiles resolves the transient collision.

### Q40: What are the key architectural trade-offs made in QuantWeave?
**Answer**: 
1. **On-the-fly Ledger Valuation vs Precomputed Cached Balances**: On-the-fly valuation requires slightly more CPU compute per query but guarantees 100% mathematical consistency without cache invalidation desynchronization.
2. **Deterministic Mock vs Cloud LLM**: Using a deterministic mock provider ensures zero external runtime dependency and instant CI execution, while maintaining full code readiness for cloud LLMs (Gemini/OpenAI) via environment toggles.
3. **Pure CSS Tokens vs Runtime CSS-in-JS**: Using CSS custom properties eliminates runtime JavaScript style calculation overhead and ensures instant theme rendering.
