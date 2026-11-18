# Product Requirements Document

## 1. Vision
QuantWeave gives users a single workspace to research listed companies, understand portfolios, compare mutual funds, interpret market events and test investment strategies.

## 2. Personas and user stories

### Investor
- As an investor, I can search for an Indian listed company and inspect its historical price and available financial data.
- I can create a portfolio and record buy/sell transactions.
- I can understand holdings, allocation, gains/losses and risk.
- I can compare mutual fund NAV histories and simulate SIP cash flows.
- I can ask the assistant to explain a metric and inspect its source.

### Trader
- I can create a strategy using supported indicators and rules.
- I can backtest the strategy over a selected historical period.
- I can inspect each simulated trade, assumptions, fees and performance metrics.
- I can paper trade with virtual money.

### Student/researcher
- I can inspect formula definitions and assumptions.
- I can use sample data without API credentials.
- I can compare algorithm outputs with independently computed test cases.

## 3. Functional requirements

### Equity Intelligence
- Search instruments by symbol/name/exchange.
- Show instrument profile, exchange, sector and data source.
- Show historical daily OHLCV.
- Show technical indicators with sufficient-data checks.
- Show fundamental ratios only when source statements are available.
- Compare a small number of companies side by side.
- Explain metrics using an AI assistant grounded in computed values.

### Portfolio Intelligence
- Create, rename and archive portfolios.
- Record cash deposits/withdrawals and buy/sell transactions.
- Derive positions from transaction history.
- Display invested amount, market value, P&L and allocation.
- Calculate returns with clear methodology.
- Calculate volatility, beta, Sharpe ratio and drawdown when data coverage is sufficient.
- Run hypothetical stress scenarios.

### FundScope
- Search mutual fund schemes by name/code.
- Show scheme category and plan/option metadata where available.
- Show NAV history and return calculations.
- Simulate SIP contributions.
- Compare funds over common date ranges.
- Calculate overlap only from dated holdings data with matching instrument identifiers.

### MarketPulse
- Store news/article metadata and source links.
- Deduplicate articles.
- Extract entities and event categories.
- Produce sentiment classification with model version and confidence.
- Show historical price windows around events as descriptive analysis, not causal proof.

### QuantLab
- Support a safe, constrained strategy configuration format.
- Start with daily OHLCV strategies: moving-average crossover and RSI threshold.
- Use documented signal and execution timing.
- Include costs and slippage assumptions.
- Store reproducible run configuration and data version.
- Show equity curve, trade ledger and metrics.
- Support virtual paper accounts and orders only.

### AI assistant
- Route questions to appropriate module tools.
- Retrieve computed analytics and permitted documents.
- Provide citations and as-of dates.
- State when data is missing or stale.
- Never invent numerical values or make personalised recommendations.

## 4. Non-functional requirements
- Responsive desktop-first UI with mobile support.
- Server-side authorisation for all private data.
- Clear loading, empty, stale and error states.
- API validation and consistent error format.
- Unit tests for calculations.
- Integration tests for core API flows.
- Reproducible backtests.
- Logs must not contain passwords, tokens or sensitive portfolio data.
- Demo mode must work without paid services.

## 5. MVP acceptance criteria
- User can run the application locally using documented commands.
- Demo data is visibly labelled.
- User can search a seeded instrument and view a price chart.
- User can create a portfolio and record a transaction.
- Holdings are derived from the ledger.
- Portfolio metrics have tested formulas and documented limitations.
- User can search a seeded mutual fund and view NAV history.
- AI can explain a computed metric with a traceable source reference.
- Tests pass and README setup instructions are accurate.
