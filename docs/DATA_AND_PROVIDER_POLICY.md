# Data and Provider Policy

## Provider abstraction
Implement interfaces for:
- Equity historical prices and reference instruments.
- Corporate actions.
- Company financial statements.
- Mutual fund schemes and NAV.
- Mutual fund holdings.
- News and corporate announcements.

The domain layer must not depend directly on a specific provider SDK. Each adapter converts provider responses into internal Pydantic/domain models.

## Initial source candidates
These are candidates to investigate, not guaranteed entitlements:
- TejHQ: Indian equity historical data and related datasets; check current plan, terms and licensing.
- MFapi.in: mutual fund scheme/NAV API; verify availability and terms.
- Official exchange/regulatory sources: use only through permitted access and terms.
- News providers: use a provider/API whose licence permits the intended storage, analysis and display.

## Demo mode
- Include a small synthetic or properly licensed sample dataset.
- Mark every sample row and UI panel as DEMO.
- Never blend demo and live data without an explicit label.
- Do not make synthetic values resemble verified real-time quotes.

## Ingestion requirements
- Idempotent upserts.
- Provider name and dataset stored for each ingestion.
- Retrieved timestamp and source date.
- Validate high >= low, non-negative volume and sensible OHLC relationships.
- Record failed jobs and error summaries.
- Detect gaps; do not silently forward-fill market prices for display.
- Preserve raw provider payload only if terms permit and retention is justified.
- Handle corporate actions and adjusted/unadjusted price distinction.

## Freshness
Every data response should carry:
- `as_of` or `trade_date`.
- `retrieved_at`.
- `source`.
- `is_demo`.
- Optional `stale` flag or freshness status.

## No provider credentials
Do not ask the user to paste secrets into chat or commit them. Configure keys in local `.env` or deployment secrets.
