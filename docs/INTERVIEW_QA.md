# QuantWeave — Technical Interview Questions & Answers

A comprehensive technical reference covering system design, database architecture, financial mathematics, API security, and AI orchestration for QuantWeave.

---

## Domain 1: Database Design & Relational Modeling

### Q1.1: Why did you choose an append-only transaction ledger instead of maintaining mutable position records in the portfolio table?
**Answer**:
A mutable `positions` table that updates a `quantity` column via `UPDATE portfolios SET shares_held = shares_held + X` suffers from severe data integrity and compliance flaws:
1. **Loss of Auditability**: You cannot reconstruct historical balances at arbitrary past dates or verify tax lots.
2. **Race Conditions**: Concurrent buy/sell requests can lead to lost updates or negative cash states.
3. **Double-Entry Reconciliation**: An append-only ledger (`PortfolioTransaction` with `BUY`, `SELL`, `CASH_DEPOSIT`, `CASH_WITHDRAWAL`, `DIVIDEND`) guarantees an auditable timeline. Every state transition is recorded as a discrete event. Current holdings and Weighted-Average Cost Basis (WACB) are calculated deterministically by scanning transactions up to a target `as_of_date`.

### Q1.2: How does QuantWeave prevent duplicate transactions if a network drop causes a client to retry a submission?
**Answer**:
We use an **Idempotency Key pattern**. The `portfolio_transactions` table enforces a unique constraint on `(portfolio_id, idempotency_key)`. When a transaction request is received:
- If the idempotency key already exists for the portfolio, the backend safely returns the existing transaction record with an HTTP 200/409 without double-debiting cash or duplicating shares.
- If the idempotency key was previously submitted under a *different* portfolio, it raises a security violation (`DuplicateTransactionError`).

### Q1.3: How is Alembic migration linearity maintained across 8 feature releases?
**Answer**:
We strictly maintain a single linear branch (`down_revision` pointers form a singly-linked list without divergence or multiple heads). The chain progresses linearly:
`9ee3a29b8445 -> 35b3591b794d -> a1b2c3d4e5f6 -> b2c3d4e5f6a1 -> c3d4e5f6a1b2 -> d4e5f6a1b2c3 -> e5f6a1b2c3d4 -> f6a1b2c3d4e5 (HEAD)`.
This guarantees that automated CI/CD pipelines and production deployments can run `alembic upgrade head` idempotently without encountering branch resolution ambiguities.

---

## Domain 2: API Architecture & Fast Performance

### Q2.1: Why did you select FastAPI over traditional frameworks like Django or Flask?
**Answer**:
1. **Asynchronous Concurrency**: Built on Starlette and ASGI, FastAPI handles hundreds of concurrent connections with minimal memory footprint.
2. **Pydantic v2 Serialization**: Core serialization and validation routines are compiled in Rust, providing up to 5x faster JSON parsing than Python-native serializers.
3. **Strict Dependency Injection**: FastAPI's `Depends` system enables modular, mockable components for database session lifecycle (`get_db`), authentication (`get_current_user`), and rate limiters.
4. **Automated OpenAPI Contracts**: Interactive documentation (`/docs`) and typed schema export directly synchronize backend contracts with our frontend TypeScript client.

### Q2.2: How do you handle CPU-intensive numerical analytics (e.g., 504-bar Bollinger Bands or multi-parameter grid searches) in an async event loop?
**Answer**:
Running heavy NumPy or Pandas vector calculations directly on the async event loop would block Starlette from processing incoming I/O. We define compute-heavy endpoints as standard synchronous functions (`def endpoint(...)`) or dispatch them via `anyio.to_thread.run_sync()`. FastAPI automatically offloads standard synchronous route functions to its internal worker threadpool, ensuring the async event loop remains responsive.

---

## Domain 3: Authentication & Security Architecture

### Q3.1: How does QuantWeave protect authentication tokens against XSS attacks?
**Answer**:
Rather than storing JWT access tokens in browser `localStorage` or `sessionStorage` (which are vulnerable to client-side script injection via XSS), QuantWeave sets tokens inside **`HttpOnly`, `Secure`, `SameSite=Lax` cookies**:
- `HttpOnly`: Disallows JavaScript `document.cookie` access entirely.
- `Secure`: Ensures cookies are transmitted only over encrypted TLS/HTTPS connections.
- `SameSite=Lax`: Prevents cookies from being transmitted during cross-site sub-resource requests.

### Q3.2: If tokens are stored in cookies, how does the platform defend against Cross-Site Request Forgery (CSRF)?
**Answer**:
We employ defense-in-depth CSRF mitigation implemented in `app/api/deps.py`:
When an authenticated state-mutation request (POST, PUT, PATCH, DELETE) relies on cookie credentials, the server verifies:
1. The request payload has an explicit `Content-Type: application/json` or `multipart/form-data` (which cannot be submitted via simple HTML `<form>` cross-site posts without preflight).
2. The request carries a custom client header: `X-Requested-With: XMLHttpRequest`.
3. If an `Origin` header is present, it must strictly match the whitelisted CORS domain.

### Q3.3: How does your sliding-window rate limiter work, and how does it prevent memory exhaustion?
**Answer**:
Implemented in `app/core/rate_limiter.py`, `SlidingWindowRateLimiter` tracks a list of Unix epoch timestamps per client IP. On each incoming request:
1. It discards timestamps older than `now - 60.0` seconds.
2. If remaining timestamps are below `max_requests`, the current timestamp is appended and the request is permitted.
3. If capped, an `HTTPException(429, detail="Too Many Requests")` is raised with a `Retry-After: 60` header.
4. **Memory Leak Mitigation**: A periodic sweep checks whether `time.time() - last_cleanup > cleanup_interval`. Stale IP buckets with zero active timestamps are purged from the dictionary.

---

## Domain 4: Financial Mathematics & Quantitative Modeling

### Q4.1: Why does QuantWeave use Wilder's Exponential Smoothing for RSI instead of a simple moving average of gains and losses?
**Answer**:
The standard Relative Strength Index defined by J. Welles Wilder Jr. (1978) does not use an arithmetic SMA. Instead, after the initial 14-period seed average, it updates average gain and loss using an exponential decay smoothing:
\[
\text{AvgGain}_t = \frac{\text{AvgGain}_{t-1} \times 13 + \text{Gain}_t}{14}
\]
\[
\text{AvgLoss}_t = \frac{\text{AvgLoss}_{t-1} \times 13 + \text{Loss}_t}{14}
\]
Using a simple moving average creates abrupt step-function drops when high volatility periods exit the 14-day window. Wilder's smoothing ensures historical price movement decays smoothly, preventing artificial whipsaws.

### Q4.2: What is the exact mathematical difference between Time-Weighted Return (TWR) and Extended Internal Rate of Return (XIRR)?
**Answer**:
- **Time-Weighted Return (TWR)** measures the compound rate of growth of the portfolio while completely eliminating the distorting effects of cash inflows and outflows. It breaks the timeline into sub-periods at each external cash flow date, calculates sub-period returns \(R_k = (V_k - C_k - V_{k-1}) / V_{k-1}\), and compounds them:
  \[
  \text{TWR} = \prod_{k=1}^n (1 + R_k) - 1
  \]
  TWR evaluates the quality of investment decisions independent of cash flow timing.
- **Extended Internal Rate of Return (XIRR)** is a **Money-Weighted Return**. It solves for the discount rate \(r\) that equates the net present value (NPV) of all dated external cash flows plus terminal market value to zero:
  \[
  \sum_{i=0}^N \frac{\text{CF}_i}{(1 + r)^{(d_i - d_0)/365}} = 0
  \]
  XIRR reflects the investor's personalized return based on their timing of deposits and withdrawals.

### Q4.3: How does your XIRR numerical solver handle irregular non-periodic cash flows?
**Answer**:
In `app/analytics/portfolio_analytics.py`, our `calculate_xirr()` function implements the **Newton-Raphson method**:
\[
r_{n+1} = r_n - \frac{f(r_n)}{f'(r_n)}
\]
where \(f'(r)\) is the analytic first derivative with respect to \(r\). If Newton-Raphson diverges due to a near-zero derivative or alternating slopes, our solver falls back to **Bisection Search** within the bounded interval \([-0.999, 10.0]\), ensuring convergence even on challenging cash flow series.

---

## Domain 5: Mutual Fund Intelligence & FundScope

### Q5.1: How does FundScope calculate true historical SIP returns rather than using theoretical annuity formulas?
**Answer**:
Theoretical annuity SIP formulas assume a constant fixed CAGR over time. FundScope implements a **daily historical simulation**:
1. On each monthly SIP date (e.g. 5th of each month), the engine queries the exact historical NAV for that day (or the preceding business day if the 5th was a market holiday).
2. It accumulates units: \(\Delta \text{Units}_k = \text{Amount} / \text{NAV}_k\).
3. At the end of the investment horizon, final valuation is \(\text{Total Units} \times \text{NAV}_{\text{final}}\).
4. The exact dated cash flows are passed to our XIRR engine to compute the annualized compounded yield.

### Q5.2: How does the platform quantify the cost drag between Direct and Regular mutual fund plans?
**Answer**:
Direct plans have no distributor commissions, typically resulting in an expense ratio 0.50% to 1.00% lower than Regular plans. Over a 10–20 year horizon, this difference compounds significantly. FundScope models this by comparing the historical NAV growth trajectories of identical underlying portfolios under both share classes, illustrating that an investor in a Regular plan often sacrifices 15% to 25% of their terminal wealth to distribution commissions.

---

## Domain 6: Backtesting Engine & Quantitative Research

### Q6.1: What is look-ahead bias in backtesting, and how does QuantLab mathematically prevent it?
**Answer**:
Look-ahead bias occurs when a trading algorithm uses information from day \(t\) (such as day \(t\)'s Close price or volume) that was not known or accessible when placing orders on day \(t\).
In QuantLab:
1. Signal evaluation at bar \(t\) uses data strictly up to bar \(t\) Close.
2. Order execution is simulated on **bar \(t+1\) Open** (next-bar open pricing).
3. Technical indicators are pre-computed on chronologically sorted series without forward indexing.

### Q6.2: How are execution slippage and brokerage fees modeled?
**Answer**:
A frictionless backtest will drastically overestimate performance, especially for higher-frequency turnover strategies. QuantLab incorporates:
- **Brokerage Commission**: A basis point fee (e.g. 10 bps / 0.1%) deducted from available cash upon execution.
- **Execution Slippage**: A simulated market impact penalty (e.g. 5 bps) where Buy orders execute at \(\text{Open} \times (1 + \text{slippage})\) and Sell orders execute at \(\text{Open} \times (1 - \text{slippage})\).

### Q6.3: How does the parameter grid search evaluate overfitting?
**Answer**:
When optimizing indicator parameters (e.g. SMA windows [5, 10, 20, 50]), an algorithm can easily curve-fit historical market noise. QuantLab supports **In-Sample (Train) vs. Out-of-Sample (Test) partitioning**:
- The strategy parameters are optimized on the first 70% of chronological data (In-Sample).
- The top-performing parameter sets are then tested against the unseen remaining 30% of data (Out-of-Sample).
- If Sharpe ratio or CAGR drops drastically in the Out-of-Sample segment, the strategy is flagged for curve-fitting.

---

## Domain 7: AI Copilot, RAG & Function Calling

### Q7.1: Why are all AI Copilot tools strictly read-only and injected with `context_user_id` server-side?
**Answer**:
If an LLM had access to mutate functions (e.g., `execute_trade`, `delete_portfolio`), an indirect prompt injection attack through an external news article or prompt could trigger unintended financial actions. Furthermore, if the LLM could supply the `user_id` parameter, an attacker could instruct the model: *"Check portfolio details for user_id = admin"*.
By injecting `context_user_id` on the server from the authenticated JWT session, the LLM physically cannot access or query data belonging to other accounts.

### Q7.2: How does QuantWeave ensure the AI Copilot never hallucinates financial numbers?
**Answer**:
The AI Copilot does **zero primary financial calculations** inside generative text. All math (RSI values, Sharpe ratios, cash balances, P/E ratios) is calculated deterministically by our Python analytics engines. The LLM only receives verified structured JSON payloads from tool executions and RAG documentation chunks. Its role is strictly to explain and contextualize verified figures.

---

## Domain 8: Full-Stack Engineering, Testing & Deployment

### Q8.1: What is the testing strategy across the repository?
**Answer**:
Our testing pyramid includes:
1. **Unit Tests**: Pure financial algorithms (Wilder RSI smoothing, XIRR solver, WACB calculation, Sharpe ratio).
2. **Integration Tests**: FastAPI REST endpoints with SQLite in-memory database using `StaticPool` for concurrency safety.
3. **Security Regression Tests**: CSRF validation, sliding-window rate limiting, cross-user authorization barriers, and CSV upload null-byte injection rejection.
4. **End-to-End User Journeys**: Automated suites covering all 17 user journeys from registration to backtesting and AI conversation deletion.
5. **AI Evaluation Benchmarks**: Automated 18-case benchmark suite auditing factual correctness, tool invocation precision, disclaimer compliance, and prompt injection resilience.

### Q8.2: How does QuantWeave run in a containerized production environment?
**Answer**:
Using **Docker Compose**, the platform deploys three coordinated services:
- `db`: PostgreSQL 16 image with persistent volume storage and automated health check.
- `api`: FastAPI application running under Uvicorn workers behind a health-checked container.
- `web`: Next.js 15 standalone Node.js production server.
Internal communication between containers uses private Docker bridge networking with zero external exposure of database ports.
