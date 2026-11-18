# QuantWeave — Live Project Demonstration Scripts

These scripts provide structured verbal presentations and exact click-by-click instructions for hiring managers, technical interviewers, and academic evaluators.

---

## 1. The 30-Second Elevator Pitch

> *"QuantWeave is an institutional-grade financial intelligence and quantitative research platform built with Next.js 15, FastAPI, SQLAlchemy 2.0, and a deterministic mathematical engine. Unlike typical financial dashboards with mock balances, QuantWeave implements an append-only double-entry transaction ledger with idempotency keys, an exact Newton-Raphson XIRR solver for irregular cash flows, lookahead-free next-bar backtesting with slippage and commission modeling, a 4-theme design token system, and a tool-augmented AI research copilot with strict read-only authorization. The entire platform is backed by 144 passing backend tests, automated Playwright E2E browser suites, and a production-grade security architecture."*

---

## 2. The 2-Minute Technical Overview

> *"Hello, I’d like to walk you through QuantWeave, a platform I engineered to bridge institutional quantitative analytics with modern full-stack web software engineering.
>
> In financial software, data integrity and mathematical precision are paramount. In QuantWeave, user cash and stock holdings are never stored as mutable numbers. Instead, we architected an append-only ledger where every financial event—deposits, withdrawals, buys, and sells—is recorded as an immutable row. Real-time cash balances, Weighted-Average Cost Basis, and unrealized profit-and-loss are calculated on-the-fly with mathematical guarantees.
>
> On the algorithmic side, our QuantLab simulation engine eliminates look-ahead bias by evaluating signals at bar Close and executing trades at the next bar’s Open with modeled slippage and exchange fees. We also built an in-sample and out-of-sample grid search optimizer to detect overfitting before deployment.
>
> For our AI Copilot, we solved the problem of financial hallucinations by enforcing a strict separation of concerns: the language model handles natural language intent and tool selection, while our deterministic Python engine executes all numerical calculations and injects verified markdown citations.
>
> The frontend is built on Next.js 15 and Tailwind CSS with a 4-theme design token system that eliminates styling flashes. The entire application is verified by 144 passing backend regression tests and automated Playwright browser test suites."*

---

## 3. The 5–7 Minute Full Technical Walkthrough

### Preparation
1. Ensure FastAPI is running on `http://localhost:8000`.
2. Ensure Next.js is running on `http://localhost:3000`.
3. Open browser to `http://localhost:3000`.

---

### Segment 1: Landing Page & Security Architecture (1 Minute)
- **On Screen**: Start on the public landing page (`http://localhost:3000/`).
- **Verbal Walkthrough**:
  > *"Here is the QuantWeave landing page. Notice that access to the financial intelligence dashboard is strictly gated behind authentication. Let's register a new researcher account or log into our existing profile."*
- **Actions**: Click **Sign In** $\to$ enter credentials $\to$ submit.
- **Key Technical Point**:
  > *"Upon login, the backend issues an HMAC-SHA256 JWT stored in an HttpOnly, SameSite=Lax cookie. This prevents token exfiltration via client-side XSS attacks, while our custom header requirements neutralize Cross-Site Request Forgery."*

---

### Segment 2: Design System & 4-Theme Dynamic Switching (1 Minute)
- **On Screen**: Main Dashboard (`/dashboard`).
- **Verbal Walkthrough**:
  > *"Once inside, we enter the Signal Loom quantitative interface. Notice the responsive sidebar with our collapsible navigation and bottom user profile card. Let's open the profile menu."*
- **Actions**: Click the profile trigger button at the bottom left of the sidebar.
- **Key Technical Point**:
  > *"Notice that the dropdown menu anchors upwards and is strictly contained within the visible viewport bounds with zero clipping, even on small screens or mobile drawers. From here, we can switch across all 4 built-in themes: Signal Loom, Daybreak, Nebula, and Oceanic. The entire color palette updates instantaneously via CSS custom properties, without a page reload or styling flicker, and persists across both browser localStorage and our PostgreSQL user preferences table."*

---

### Segment 3: Equity Intelligence & Technical Indicators (1.5 Minutes)
- **On Screen**: Navigate to `/equity`.
- **Actions**: Select `RELIANCE` or `TCS` from the search bar.
- **Verbal Walkthrough**:
  > *"Under Equity Intelligence, we visualize historical daily OHLCV prices alongside institutional technical indicators. Our backend calculates Simple Moving Averages, Exponential Moving Averages, Bollinger Bands, and Wilder’s Relative Strength Index.
  >
  > Notice the RSI chart: standard implementations use a simple moving average, which introduces step-function distortions. In QuantWeave, we implement J. Welles Wilder’s true exponential smoothing with alpha equals 1 over 14. In addition, our numerical engine incorporates zero-division guards for flat trading ranges, ensuring numerical stability."*

---

### Segment 4: Portfolio Ledger & XIRR Solver (1.5 Minutes)
- **On Screen**: Navigate to `/portfolio`.
- **Actions**: View current cash balance $\to$ click **Record Transaction** $\to$ deposit cash or execute a BUY order $\to$ observe real-time recalculation.
- **Verbal Walkthrough**:
  > *"Here in Portfolio Intelligence, we demonstrate our append-only double-entry ledger. Notice that we never execute an SQL UPDATE on user cash. When we record a transaction, an immutable record is inserted with an idempotency key.
  >
  > The system recalculates Weighted-Average Cost Basis, realized gains on sales, and unrealized gains on open positions on-the-fly. For overall performance, rather than simple CAGR which distorts short-term irregular cash flows, our backend runs a custom Newton-Raphson solver to compute exact XIRR, backed by a robust bisection search fallback if non-linear cash flows fail to converge."*

---

### Segment 5: QuantLab Backtesting Engine (1.5 Minutes)
- **On Screen**: Navigate to `/quantlab`.
- **Actions**: Select **SMA Crossover Strategy** $\to$ Set Fast SMA = 10, Slow SMA = 30 $\to$ Click **Run Backtest**.
- **Verbal Walkthrough**:
  > *"QuantLab is our algorithmic backtesting simulator. A common flaw in commercial backtesters is look-ahead bias—filling orders at the same bar's Close where the signal was generated.
  >
  > In QuantLab, all signals evaluated at bar t's Close are executed strictly at bar t plus 1's Open price. Furthermore, the engine models execution slippage and broker commissions on every trade.
  >
  > Notice the interactive equity curve comparing our strategy against the benchmark buy-and-hold index, alongside Sharpe, Sortino, and Maximum Drawdown metrics. We also support parameter grid searches with train/test splits to detect and prevent strategy overfitting."*

---

### Segment 6: AI Copilot & Placement Wrap-Up (30 Seconds)
- **On Screen**: Navigate to `/ai`.
- **Actions**: Type: `"What is the current technical outlook and RSI for TCS?"` $\to$ Submit.
- **Verbal Walkthrough**:
  > *"Finally, here is the QuantWeave AI Copilot. The language model never performs calculations in prose. It dispatches a read-only tool call to our Python calculation engine, retrieves the exact numerical values, and synthesizes an auditable response with citations.
  >
  > In summary, QuantWeave demonstrates end-to-end full-stack engineering, rigorous quantitative modeling, and production-grade security, validated by 144 passing tests and automated Playwright E2E suites. Thank you!"*
