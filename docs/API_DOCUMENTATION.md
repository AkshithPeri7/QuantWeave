# QuantWeave — REST API Documentation

Comprehensive API documentation for the QuantWeave backend analytics engine.

- **Base URL**: `http://localhost:8000/api/v1`
- **Interactive OpenAPI Specification**: `http://localhost:8000/docs`
- **Authentication**: JWT token transmitted via `Authorization: Bearer <token>` or `HttpOnly` cookie.
- **CSRF Protection**: State-mutating requests (POST, PUT, PATCH, DELETE) require `X-Requested-With: XMLHttpRequest`.

---

## 1. Authentication & User Profile (`/api/v1/auth`)

### `POST /auth/register`
Creates a new user account.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "StrongPassword123!",
    "full_name": "Jane Doe"
  }
  ```
- **Response (201 Created)**: User record, sets `access_token` and `refresh_token` in `HttpOnly` cookies.

### `POST /auth/login`
Authenticates user credentials.
- **Request Body**: `application/x-www-form-urlencoded` or JSON with `username` (email) and `password`.
- **Response (200 OK)**: User profile, sets authentication cookies.

### `GET /auth/me`
Retrieves currently authenticated user profile and settings.

### `PATCH /auth/me`
Updates user display name or email address.

### `PATCH /auth/me/preferences`
Updates user UI appearance settings (theme and avatar).
- **Request Body**:
  ```json
  {
    "theme": "signal-loom",
    "avatar_preset": "signal-cyan"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "theme": "signal-loom",
    "avatar_preset": "signal-cyan",
    "updated_at": "2026-11-17T12:00:00Z"
  }
  ```

---

## 2. Equity Intelligence (`/api/v1/equity`)

### `GET /equity/instruments`
Lists and searches available securities with pagination and ticker filtering.
- **Query Params**: `q` (search query), `page` (default 1), `limit` (default 20).

### `GET /equity/instruments/{id}/prices`
Returns historical OHLCV bar series.
- **Query Params**: `start_date`, `end_date`, `interval` (`1d`, `1w`).

### `GET /equity/instruments/{id}/technicals`
Computes verified technical indicators.
- **Response**:
  ```json
  {
    "rsi_14": 58.42,
    "macd": {
      "macd": 1.25,
      "signal": 0.88,
      "histogram": 0.37
    },
    "bollinger": {
      "upper": 2940.50,
      "middle": 2860.00,
      "lower": 2779.50
    },
    "sma_50": 2810.15,
    "sma_200": 2650.30
  }
  ```

### `GET /equity/instruments/{id}/fundamentals`
Returns fundamental ratios and statement snapshots (P/E, P/B, ROE, Debt/Equity).

### `POST /equity/compare`
Multi-ticker comparison returning aligned returns and valuation metrics.

---

## 3. Portfolio Intelligence (`/api/v1/portfolios`)

### `GET /portfolios`
Lists all portfolios owned by the authenticated user.

### `POST /portfolios`
Creates a new portfolio container.
- **Request Body**:
  ```json
  {
    "name": "Growth Strategy",
    "currency": "INR",
    "initial_cash": 100000.00
  }
  ```

### `POST /portfolios/{id}/transactions`
Appends an immutable financial transaction to the ledger.
- **Request Body**:
  ```json
  {
    "transaction_type": "BUY",
    "instrument_id": 4,
    "shares": 25.0,
    "price_per_share": 2850.00,
    "fees": 15.00,
    "idempotency_key": "c7a1e0b5-7c9e-4e6a-bdf8-92716a5b9e01"
  }
  ```

### `GET /portfolios/{id}/performance`
Calculates comprehensive performance metrics:
- Total Valuation & Available Cash.
- Unrealized and Realized Capital Gains (via WACB).
- Money-Weighted Return via Newton-Raphson XIRR solver.
- Asset Allocation breakdown.

---

## 4. FundScope Mutual Fund Intelligence (`/api/v1/funds`)

### `GET /funds`
Lists available mutual funds with category, risk rating, and expense ratio.

### `POST /funds/sip-calculator`
Executes daily historical SIP simulation.
- **Request Body**:
  ```json
  {
    "fund_id": 1,
    "monthly_amount": 5000.0,
    "start_date": "2021-01-01",
    "end_date": "2024-01-01",
    "sip_day": 5
  }
  ```
- **Response**: Historical units accumulated, terminal valuation, money-weighted XIRR, and comparison against benchmark index.

---

## 5. MarketPulse Macro & Market Overview (`/api/v1/market`)

### `GET /market/summary`
Returns broad market indices (NIFTY 50, SENSEX, BANKNIFTY), advances/declines, and top gainers/losers.

### `GET /market/watchlist`
Retrieves user-customized watchlist.

### `POST /market/watchlist`
Adds a ticker to user watchlist.

---

## 6. QuantLab Quantitative Research & Backtesting (`/api/v1/quantlab`)

### `POST /quantlab/backtest`
Executes an instant lookahead-free strategy backtest.
- **Request Body**:
  ```json
  {
    "strategy_type": "SMA_CROSSOVER",
    "instrument_id": 1,
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000.0,
    "parameters": {
      "fast_period": 10,
      "slow_period": 30
    },
    "commission_bps": 10.0,
    "slippage_bps": 5.0
  }
  ```
- **Response**:
  ```json
  {
    "total_return_pct": 24.8,
    "cagr_pct": 24.8,
    "sharpe_ratio": 1.42,
    "sortino_ratio": 1.85,
    "max_drawdown_pct": -8.4,
    "trades_count": 14,
    "win_rate_pct": 64.3,
    "equity_curve": [...]
  }
  ```

### `POST /quantlab/grid-search`
Optimizes strategy parameters over parameter ranges with in-sample/out-of-sample split.

---

## 7. AI Financial Research Copilot (`/api/v1/ai`)

### `POST /ai/conversations`
Creates a new research session.

### `POST /ai/conversations/{id}/messages`
Submits a query to the AI Copilot.
- **Request Body**:
  ```json
  {
    "message": "Analyze Reliance's current RSI and MACD, and check if my portfolio holds any shares."
  }
  ```
- **Response**:
  ```json
  {
    "response": "Based on verified backend data...",
    "tools_invoked": [
      "get_equity_technicals",
      "get_portfolio_summary"
    ],
    "disclaimer": "QuantWeave Copilot provides educational research analysis and does not constitute registered investment advice."
  }
  ```
