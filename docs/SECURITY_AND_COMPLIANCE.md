# Security, Privacy and Compliance

## Security
- Hash passwords with Argon2id or bcrypt using a maintained library.
- Use short-lived access tokens and secure refresh-token handling.
- Validate resource ownership on the server for every private object.
- Use CORS allowlists, rate limits and request-size limits.
- Use parameterised SQL/ORM operations.
- Keep secrets out of Git and logs.
- Restrict file upload types and sizes if document upload is added.
- Run backtests in a constrained worker; never execute arbitrary user Python.
- Add audit events for authentication and sensitive user actions.
- Use HTTPS in deployed environments.

## Privacy
- Collect only data required for the feature.
- Explain what is stored and why.
- Provide account/data deletion strategy before public launch.
- Do not send a user's full portfolio to an LLM when a small aggregate is sufficient.
- Avoid storing raw prompts containing sensitive personal data longer than needed.

## AI Copilot Security & Guardrails (Milestone 8)
- **Zero Real-Money Trading:** Strictly zero order execution, zero broker credentials, and zero trade mutation capabilities.
- **Server-Side Authorization on Tools:** Tools that access private user data (e.g. `list_user_portfolios`, `get_portfolio_valuation`, `get_saved_strategies`, `get_backtest_results`) take `context_user_id` injected directly from the authenticated session (`get_current_user`), ignoring any user-supplied prompt parameters.
- **Prompt Injection Defense:** Multi-layer defense in `MockLLMProvider` and prompt templates rejecting attempts to override system rules, drop tables, extract passwords, or bypass security.
- **Strictly Read-Only Execution:** Every registered tool executes non-mutating SQL reads or pure mathematical calculations.
- **Recursion & Rate Limits:** Tool executions are capped at a maximum of 5 tool calls per chat turn with a 15-second timeout.
- **Audit Logging:** Every AI message turn records tool execution latency, arguments, outputs, and RAG knowledge source citations in `ai_tool_executions` and `ai_retrieval_sources`.

## Financial boundaries
Initial release is an educational analytics/research tool:
- No real-money order placement.
- No broker credentials.
- No personalised buy/sell recommendations.
- No guaranteed return claims.
- Clearly label backtests and paper trading as simulations.
- Show source, timestamp and methodology.
- A disclaimer does not replace legal/regulatory analysis.

Before any public or commercial launch in India, obtain qualified review of applicable SEBI rules, data licensing, privacy and consumer obligations. Product classification depends on actual functionality and how it is marketed.
