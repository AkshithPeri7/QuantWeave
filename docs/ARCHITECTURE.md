# QuantWeave Architecture

## Architectural Style
Modular monolith with background workers. One Next.js 15 application (`apps/web`), one FastAPI application (`apps/api`), one PostgreSQL database (with SQLite testing fallback), and optional background workers. Each domain owns its models, schemas, analytics engines, services, and REST routers.

```
+-----------------------------------------------------------------------------------+
|                                  NEXT.JS 15 WEB                                   |
|   /dashboard   /equity   /portfolio   /funds   /market   /quantlab   /ai (Copilot)    |
+------------------------------------------+----------------------------------------+
                                           | HTTPS / JSON
+------------------------------------------v----------------------------------------+
|                                FASTAPI BACKEND                                    |
|   [Auth & Users]   [Market Data]   [Equities]   [Portfolios]   [Funds]   [Market] |
|   [QuantLab Backtesting]           [QuantWeave Copilot AI Engine]                 |
+--------------------+-------------------------------------+------------------------+
                     |                                     |
       +-------------v--------------+       +--------------v---------------+
       | Deterministic Analytics    |       | AI Copilot Subsystem         |
       | - Technicals (SMA/EMA/RSI) |       | - AIOrchestrator             |
       | - Fundamentals (P/E, ROE)  |       | - 22 Read-Only Tools         |
       | - Portfolio (TWR, XIRR)    |       | - RAG Knowledge Engine       |
       | - Fund Analytics & SIP     |       | - Interchangeable Providers  |
       | - Lexicon Sentiment NLP    |       |   (Mock, Gemini, OpenAI)     |
       | - Event Backtest Engine    |       | - Benchmark Eval Runner      |
       +-------------+--------------+       +--------------+---------------+
                     |                                     |
+--------------------v-------------------------------------v------------------------+
|                             POSTGRESQL / SQLITE                                   |
|   instruments, price_history, financial_statements, portfolios, transactions,     |
|   mutual_funds, fund_nav_history, news_articles, sentiment, macro_series,         |
|   research_strategies, backtest_runs, backtest_trades,                            |
|   ai_conversations, ai_messages, ai_tool_executions, ai_retrieval_sources         |
+-----------------------------------------------------------------------------------+
```

## Logical Components
- **Web (`apps/web`):** Next.js 15 App Router, React 19, Tailwind CSS. Provides responsive dashboards, interactive SVG charts, trade logs, and the full QuantWeave Copilot AI workspace.
- **API (`apps/api`):** FastAPI application with Pydantic v2 schemas, JWT authentication, and scoped route handlers.
- **Domain Modules:**
  1. `equity`: Historical OHLCV, moving averages, Wilder's RSI, MACD, Bollinger Bands, audited statement ratios, multi-stock comparison.
  2. `portfolio`: Double-entry position ledger, cash balance controls, overselling guards, WACB accounting, daily valuation timeline, TWR and XIRR solvers.
  3. `funds` (FundScope): AMFI scheme metadata, daily NAV tracking, CAGR & rolling returns, SIP and lump-sum wealth calculators, multi-scheme comparisons.
  4. `market` (MarketPulse): Financial news wire, explainable financial lexicon sentiment, macroeconomic series (CPI, Repo Rate, GDP), watchlists and alert notifications.
  5. `quantlab`: Reusable quantitative strategy interfaces, event-driven backtesting with next-bar Open pricing, fee modeling, parameter grid search, and train/test overfitting detection.
  6. `ai` (QuantWeave Copilot): Provider-agnostic AI research assistant (`BaseLLMProvider`, `MockLLMProvider`, `GoogleGeminiProvider`, `OpenAIProvider`), 22 typed read-only tools, RAG retrieval over methodology chunks, audit logging, and automated benchmark evaluation suite.

## AI Security & Grounding Principles
1. **Server-Side Authorization:** Tool executions taking user context inject `context_user_id` server-side from session dependencies. The LLM cannot override or inspect other users' data.
2. **Read-Only Invariance:** All 22 tools registered with the AI orchestrator are strictly read-only.
3. **Loop Bounds & Timeouts:** Execution is capped at a maximum of 5 tool calls per turn to eliminate infinite recursion loops.
4. **Mandatory Educational Disclaimer:** All assistant responses automatically include a SEBI research disclaimer clarifying that QuantWeave is an educational analytics platform.
