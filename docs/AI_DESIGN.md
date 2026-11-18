# QuantWeave AI Design — Financial Copilot & Intelligent Research

## Principle & Grounding Axiom
AI in QuantWeave serves strictly as an **explanation and retrieval layer**, never as an unconstrained or authoritative source of primary financial truth.
- All numbers, performance metrics, and portfolio balances are generated deterministically by backend Python analytics engines.
- The AI never calculates financial returns, holdings balances, or indicators from scratch in free-form generative text.
- The AI never invents financial figures, accesses other users' private accounts, or executes real-money trades.

---

## Allowed AI Responsibilities
- Explain computed technical and fundamental metrics (RSI, MACD, Bollinger Bands, P/E, ROE).
- Ground natural language explanations using verified platform documentation and methodology chunks (`[DOC-01]`, etc.).
- Inspect and summarize user portfolios, asset allocations, and performance metrics (TWR, XIRR).
- Explain mutual fund structures, scheme details, and the difference between Direct and Regular expense ratios.
- Provide contextual insights into macroeconomic indicators (CPI Inflation, Repo Rate) and news sentiment heuristics.
- Clarify quantitative backtesting mechanics, event-driven simulation assumptions, and overfitting risks in QuantLab.
- Refuse malicious prompts, prompt injections, and queries attempting to override safety policies or extract private credentials.

## Strictly Disallowed AI Actions
- **Zero Real-Money Trading:** No broker integrations, API order routing, or buy/sell execution.
- **Zero Hallucinated Financial Data:** Never generate speculative prices, fabricated quarterly earnings, or synthetic NAVs without clear demo labels.
- **Zero Cross-User Data Exposure:** Portfolios, transactions, strategies, and backtest results are strictly isolated by `context_user_id` enforced server-side.
- **Zero Arbitrary Code Execution:** LLM cannot run arbitrary Python/shell scripts or mutate the underlying SQL database.

---

## Modular Provider Architecture
QuantWeave Copilot implements a provider-agnostic interface (`BaseLLMProvider`) located in `app.ai.providers`:

```
                           +----------------------+
                           |   AIOrchestrator     |
                           +----------+-----------+
                                      |
                     +----------------+----------------+
                     |                |                |
             +-------v------+  +------v-------+  +-----v--------+
             | MockProvider |  | GeminiProvider| | OpenAIProvider|
             | (Offline/Dev)|  | (Google GenAI)| | (OpenAI API) |
             +--------------+  +--------------+  +--------------+
```

1. **`MockLLMProvider` (Default in Demo/Testing):**
   - 100% deterministic, offline, and self-contained.
   - Extracts intent, dispatches server-side tools, scores RAG chunks, and synthesizes structured verified explanations.
   - Requires zero external API keys or cloud dependencies.
2. **`GoogleGeminiProvider`:**
   - Powered by `google-genai` using Gemini 2.0 / Flash.
   - Supports native function calling using OpenAPI schemas generated from tool definitions.
3. **`OpenAIProvider`:**
   - Powered by OpenAI API (GPT-4o / GPT-4o-mini) with function calling.
4. **`get_llm_provider()` Factory:**
   - Reads `AI_PROVIDER` (`mock`, `gemini`, `openai`, `none`) from application settings.

---

## Server-Side Typed Read-Only Tools (22 Registered Tools)
All tools in `app.ai.tools` are strictly read-only and enforce server-side user context:

### 1. Equity Intelligence Tools
- `search_instruments(query, limit)`
- `get_instrument_profile(symbol_or_id)`
- `get_price_history(symbol_or_id, limit)`
- `get_technical_indicators(symbol_or_id)`
- `get_fundamental_ratios(symbol_or_id)`
- `compare_equities(symbols_or_ids, period)`

### 2. Portfolio Intelligence Tools (Authenticated)
- `list_user_portfolios()` — *strictly filtered by `context_user_id`*
- `get_portfolio_valuation(portfolio_id)` — *verifies ownership*
- `get_portfolio_holdings(portfolio_id)` — *weighted-average cost basis & unrealized P&L*
- `get_portfolio_performance(portfolio_id)` — *TWR, XIRR, Volatility, Sharpe*
- `get_portfolio_risk(portfolio_id)` — *asset allocation and sector diversification*

### 3. FundScope Mutual Fund Tools
- `search_mutual_funds(query, category, limit)`
- `get_fund_profile(scheme_code_or_id)`
- `get_fund_nav_history(scheme_code_or_id, limit)`
- `get_fund_analytics(scheme_code_or_id)`
- `compare_mutual_funds(scheme_codes_or_ids)`

### 4. MarketPulse Tools
- `search_market_news(query, limit)`
- `get_news_sentiment(symbol_or_id)`
- `get_macro_indicators()`

### 5. QuantLab Strategy & Backtesting Tools
- `get_saved_strategies()` — *strictly filtered by `context_user_id`*
- `get_backtest_results(run_id)` — *verifies run ownership*
- `compare_backtest_runs(run_ids)` — *verifies multi-run ownership*

---

## Retrieval-Augmented Generation (RAG)
`RAGRetrievalService` in `app.ai.rag` indexes exactly 11 authoritative platform methodology documentation chunks:
1. **`[DOC-METHOD]`**: Platform analytics philosophy, deterministic calculations, zero hallucinations, and educational scope.
2. **`[DOC-RSI]`**: J. Welles Wilder Jr. 14-day exponential smoothing and momentum zones (30/70).
3. **`[DOC-MACD]`**: Trend-following momentum, MACD Line (12, 26), Signal Line (9), and histogram crossover mechanics.
4. **`[DOC-SMA-EMA]`**: Simple vs. Exponential moving average lag, weighting, and sensitivity characteristics.
5. **`[DOC-BOLLINGER]`**: Volatility envelope, 20-period SMA, 2-standard-deviation bands, and bandwidth contraction / squeeze.
6. **`[DOC-RATIOS]`**: Audited statement ratios: P/E, P/B, ROE, Debt/Equity, and Net Margin.
7. **`[DOC-TWR-XIRR]`**: Cash flow timing separation: Time-Weighted Return (TWR) vs. Money-Weighted Return (XIRR).
8. **`[DOC-RISK-METRICS]`**: Annualized volatility, Sharpe Ratio (Rf=6%), and Maximum Drawdown peak-to-trough mechanics.
9. **`[DOC-MUTUAL-FUNDS]`**: Mutual fund direct vs regular expense ratios, NAV compounding, and rolling returns.
10. **`[DOC-SENTIMENT]`**: Explainable financial lexicon sentiment heuristics (-1.0 to +1.0) and Indian macro series (CPI Inflation, RBI Repo Rate).
11. **`[DOC-QUANTLAB]`**: Backtest simulation assumptions, next-bar Open pricing, fee modeling, and In-Sample vs. Out-of-Sample overfitting prevention.

---

## AI Persistence Architecture
Stored in relational database tables managed via Alembic migration `f6a1b2c3d4e5_create_ai_tables.py`:
- `ai_conversations`: Session metadata (`id`, `user_id`, `title`, `context_module`, `context_entity_id`, timestamps).
- `ai_messages`: User and assistant turns (`role`, `content`, `tokens_used`, `latency_ms`, `status`).
- `ai_tool_executions`: Full audit trail of executed tools (`tool_name`, `arguments`, `result`, `status`, `execution_time_ms`).
- `ai_retrieval_sources`: Provenance citations (`citation_key`, `source_title`, `snippet`, `relevance_score`).
- `ai_evaluation_runs`: Benchmark accuracy runs (`total_cases`, `passed_cases`, `accuracy_pct`, `results_summary`).

---

## Evaluation & Benchmark Framework
`app.ai.evaluation` provides an automated 18-point benchmark suite covering factual correctness, edge cases, missing entities, and security:
1. `EVAL-EQ-01`: Technical indicators explanation (TCS RSI/MACD).
2. `EVAL-EQ-02`: Fundamental ratio interpretation (Reliance P/E, ROE).
3. `EVAL-EQ-03`: Multi-company side-by-side comparison (TCS vs INFY).
4. `EVAL-PORT-01`: Portfolio market valuation and cash balance.
5. `EVAL-PORT-02`: Methodology distinction between TWR and XIRR.
6. `EVAL-FUNDS-01`: Mutual fund discovery and Direct vs Regular expense ratio impact.
7. `EVAL-MARKET-01`: Indian macroeconomic indicator inspection (CPI & Repo).
8. `EVAL-QUANT-01`: Overfitting prevention and train/test partition theory.
9. `EVAL-SEC-01`: Prompt injection defense and safe refusal.
10. `EVAL-EQ-04`: Non-existent stock ticker handling and refusal to hallucinate fake metrics.
11. `EVAL-EQ-05`: Moving average and Bollinger Band analysis for Infosys.
12. `EVAL-PORT-03`: Sector diversification and asset allocation breakdown.
13. `EVAL-PORT-04`: Portfolio maximum drawdown interpretation during market dips.
14. `EVAL-FUNDS-02`: Fund category filtering and search (Large Cap funds in FundScope).
15. `EVAL-MARKET-02`: Equity news sentiment scoring and lexicon distribution for TCS.
16. `EVAL-MARKET-03`: MarketPulse financial news headlines search for banking sector.
17. `EVAL-QUANT-02`: Trading fees and slippage impact on strategy Sharpe ratio.
18. `EVAL-SEC-02`: Indirect prompt injection and credential extraction defense.

Accessible via `POST /api/v1/ai/evaluate` and directly in the Copilot UI.
