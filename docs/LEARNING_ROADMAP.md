# What to Learn to Build QuantWeave

Learn in dependency order. Build a small working feature after each topic rather than watching tutorials without coding.

| Stage | Learn | Practical outcome |
|---|---|---|
| 1 | Python: functions, OOP, type hints, virtual environments, exceptions, pytest; Git/GitHub | Write and test a price-return calculator; commit it |
| 2 | HTML, CSS, JavaScript, TypeScript, React, Next.js | Build a responsive stock-detail page with dummy data |
| 3 | SQL, PostgreSQL, relational design, indexes, transactions | Design users, instruments, portfolios and transactions |
| 4 | FastAPI, REST, Pydantic, SQLAlchemy, Alembic, authentication | Implement tested stock and portfolio CRUD APIs |
| 5 | NumPy, Pandas, date/time handling, data cleaning | Parse OHLCV data and compute rolling indicators |
| 6 | Financial concepts: OHLCV, NSE/BSE, NAV, SIP, P&L, cost basis, TWR/XIRR, volatility, beta, Sharpe, drawdown | Build verified calculations with known test cases |
| 7 | Data visualisation, charts, UX, API error states | Connect charts to live backend endpoints |
| 8 | Quant research: moving averages, RSI, backtesting, slippage, fees, look-ahead bias | Reproducible SMA crossover backtest |
| 9 | AI: LLM APIs, tool calling, structured output, RAG, citations, evaluation | Copilot explains retrieved verified portfolio metrics |
| 10 | Docker, CI/CD, security, logging, deployment | Deploy and demo a tested full-stack app |

## Suggested 18-week plan
- **Weeks 1–2:** Python, Git, testing.
- **Weeks 3–4:** SQL, PostgreSQL and schema design.
- **Weeks 5–6:** FastAPI, REST, SQLAlchemy and authentication.
- **Weeks 7–8:** React, Next.js, TypeScript, charts.
- **Weeks 9–11:** Finance basics, Pandas/NumPy, equity and portfolio analytics.
- **Weeks 12–14:** FundScope, QuantLab basics, backtest correctness.
- **Weeks 15–16:** LLM tool calling, retrieval, grounding, evaluation.
- **Weeks 17–18:** Docker, security, tests, deployment, project demo.

## Interview-ready explanations to prepare
- Why use a transaction ledger instead of manually storing portfolio holdings?
- How do you prevent duplicate market-data ingestion?
- What is the difference between simple return, CAGR, TWR and XIRR?
- How do you prevent look-ahead bias in backtesting?
- How does the AI avoid hallucinating market prices and portfolio values?
- How do authentication and authorization differ?
- How do migrations and CI keep deployments reproducible?

## Recommended learning priority
**Must know deeply:** Python, SQL, FastAPI, React/TypeScript, Git, financial calculations, testing.
**Learn as needed:** Docker, CI, Pandas, indicators, LLM tools/RAG.
**Later:** Redis/Celery, advanced portfolio optimization, streaming market feeds, complex multi-agent architectures.
