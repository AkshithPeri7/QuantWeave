# Testing and Acceptance

## Backend
- Unit tests for every financial formula.
- Tests for invalid/insufficient history.
- Tests for missing values and zero denominators.
- API tests for validation and error responses.
- Authentication and authorisation tests.
- Database integration tests for unique constraints and transaction ownership.
- Provider adapter tests using fixtures, not live calls in the normal test suite.
- Backtest tests for next-bar execution and no look-ahead.

## Frontend
- Responsive layout checks.
- Loading, empty, error and stale-data states.
- Form validation.
- Authenticated route protection.
- Chart date-range and demo-data labels.
- Keyboard navigation and accessible labels.

## AI
- Test answers with known expected facts.
- Verify all citations exist and support the claims.
- Test missing-data refusal.
- Test prompt injection in retrieved documents.
- Ensure the model cannot call write/execute tools.

## MVP acceptance checklist
- [ ] Local setup documented and reproducible.
- [ ] Database migration runs from an empty database.
- [ ] Demo mode works without API keys.
- [ ] Stock search and historical chart work.
- [ ] Financial metrics have unit tests and methodology docs.
- [ ] Portfolio ledger derives holdings correctly.
- [ ] Portfolio calculations handle deposits and withdrawals appropriately.
- [ ] Fund search and NAV history work.
- [ ] AI explanation cites computed data.
- [ ] User data is isolated by ownership.
- [ ] No secrets are committed.
- [ ] README and screenshots are current.
