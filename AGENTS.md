# Instructions for AI coding agents

These instructions apply to all work in this repository.

## Product rules
- Build QuantWeave as an educational financial analytics and research platform.
- Initial market: Indian equities and Indian mutual funds.
- Support investors, traders and students.
- No live broker execution, real-money orders or personalised buy/sell advice.
- Start with a modular monolith: Next.js frontend, FastAPI backend, PostgreSQL database.
- Use demo/sample data when provider access is unavailable. Clearly label demo data.

## Financial correctness
- Financial calculations must be deterministic Python functions with tests.
- Never ask an LLM to calculate prices, returns, ratios, holdings, portfolio weights or backtest metrics.
- AI may explain results returned by trusted application tools.
- Every AI-generated financial claim must reference a metric, source record or document citation.
- Never fabricate a provider, data source, price, financial statement or citation.
- Handle missing data explicitly; do not silently fill gaps with invented values.
- Use decimal/numeric types for money and quantities where precision matters.
- Document formula definitions, annualisation assumptions and limitations.

## Engineering rules
- Inspect existing files before editing.
- Follow the established module structure and naming conventions.
- Keep route handlers thin; put business logic in services and calculations in domain modules.
- Use SQLAlchemy 2.x and Alembic for database changes.
- Validate API inputs and outputs with Pydantic.
- Add tests with every feature; test edge cases.
- Do not add dependencies without explaining why.
- Do not introduce microservices, Kubernetes, Kafka or paid infrastructure unless specifically approved.
- Do not leave core functionality as TODOs or fake success responses.
- Never commit `.env`, API keys, passwords, tokens or private user data.
- Use safe parameterised database operations.
- Check ownership/authorisation for every user-specific resource.
- Avoid arbitrary code execution for user-created trading strategies. Use a constrained strategy schema/DSL.

## Frontend rules
- Use TypeScript strictly; avoid `any`.
- Build responsive, accessible interfaces with loading, empty, error and stale-data states.
- Show source, date range and data freshness for financial data.
- Clearly distinguish actual historical data, derived analytics, demo data and simulated results.
- Do not use visual elements that imply a real trade has been placed.

## Workflow
For each requested milestone:
1. Inspect relevant code and docs.
2. Summarise the implementation plan and affected files.
3. Implement only the requested milestone.
4. Run relevant tests, lint/type checks and build commands.
5. Fix failures caused by the changes.
6. Update docs and roadmap checkboxes.
7. Report exact commands run, test results, changed files and remaining limitations.

Do not claim success for commands that were not run. If an external API key or data licence is unavailable, implement the provider interface and demo adapter, and state the limitation.
