# Database Design

The executable starter schema is in `database/schema.sql`. Use Alembic migrations as the authoritative schema evolution mechanism once the backend is connected.

## Conventions
- UUID primary keys for application-owned entities.
- `NUMERIC` for money, NAV, price and quantity.
- `DATE` for exchange trading dates; UTC timestamps for event times.
- Store provider/source and ingestion timestamps.
- Use foreign keys and unique constraints.
- Use append-only portfolio transaction records; derive positions from ledger events.
- Never use a user-supplied symbol alone as a globally unique identifier. Identify instruments by exchange + symbol or a stable provider/security identifier.

## Main domains
1. Identity: users, settings, watchlists.
2. Reference data: instruments, data sources.
3. Market: daily prices, corporate actions, statements and ratios.
4. Portfolio: portfolios, transactions, snapshots and metric runs.
5. Funds: schemes, NAV and dated holdings.
6. News: articles, events and instrument links.
7. Quant: strategies, backtests, trades and paper accounts.
8. AI: sessions, messages, insights and citations.
9. Operations: ingestion runs and audit logs.

## Important modelling choices
- Price history unique key: `(instrument_id, trade_date, provider_id)`.
- Fund NAV unique key: `(fund_id, nav_date, provider_id)`.
- Store adjusted and unadjusted close distinctly.
- A fund holding is a dated observation; do not assume today's holdings apply historically.
- Backtest stores strategy version, data range, data version, costs and execution assumptions.
- Store calculated metrics with the calculation timestamp and methodology version.
