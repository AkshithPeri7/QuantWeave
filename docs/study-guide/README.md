# QuantWeave — Comprehensive Engineering & Quantitative Study Guide

Welcome to the definitive study guide for **QuantWeave**, an institutional-grade educational financial intelligence and quantitative research platform. 

This curriculum bridges modern full-stack web software engineering (Python, FastAPI, SQLAlchemy 2.0, Next.js 15, TypeScript, Tailwind CSS) with institutional quantitative finance (time-weighted returns, Newton-Raphson XIRR solvers, Wilder's smoothing, lookahead-free backtesting, and tool-augmented AI agents).

Whether preparing for quantitative developer interviews, full-stack software engineering assessments, campus placements, or final-year project defenses, this guide provides complete theoretical rigor, explicit mathematical derivations, and exact references to the live production codebase.

---

## Study Guide Architecture & Table of Contents

| File | Subject Area | Core Competencies |
| :--- | :--- | :--- |
| [`LEARNING_ROADMAP.md`](./LEARNING_ROADMAP.md) | **12-Week Curriculum** | Structured weekly roadmap covering fundamentals to advanced algorithmic trading and AI copilot engineering. |
| [`PYTHON_FASTAPI_SQL.md`](./PYTHON_FASTAPI_SQL.md) | **Backend Architecture & Ledgers** | Python OOP, typing, FastAPI dependency injection, Pydantic validation, double-entry ledger design, and PostgreSQL concurrency. |
| [`REACT_NEXTJS_TYPESCRIPT.md`](./REACT_NEXTJS_TYPESCRIPT.md) | **Frontend Engineering & Design** | React 19, Next.js 15 App Router, Server/Client components, dynamic CSS theme tokens, and accessible viewport portals. |
| [`FINANCIAL_CALCULATIONS.md`](./FINANCIAL_CALCULATIONS.md) | **Financial Mathematics** | Precise mathematical formulas, edge-case guards, and reference calculations for returns, technicals, ratios, and risk metrics. |
| [`QUANTLAB_BACKTESTING.md`](./QUANTLAB_BACKTESTING.md) | **Algorithmic Simulation** | Look-ahead bias elimination, next-bar Open execution, slippage models, transaction fee modeling, and train/test splits. |
| [`AI_RAG_AND_TOOL_CALLING.md`](./AI_RAG_AND_TOOL_CALLING.md) | **Financial AI & Tool Orchestration** | Deterministic tool execution, vectorless semantic RAG, prompt-injection defense, and citation verification. |
| [`SECURITY_AND_DEPLOYMENT.md`](./SECURITY_AND_DEPLOYMENT.md) | **Hardening & Infrastructure** | HttpOnly cookie auth, sliding-window rate limiters, CSRF mitigation, Docker containerization, and PostgreSQL runbooks. |
| [`INTERVIEW_QA.md`](./INTERVIEW_QA.md) | **40+ Technical Interview Q&A** | Comprehensive questions and answers spanning system design, concurrency, math proofs, frontend architecture, and testing. |
| [`PROJECT_DEMO_SCRIPT.md`](./PROJECT_DEMO_SCRIPT.md) | **Live Demonstration Scripts** | 30-second elevator pitch, 2-minute overview, and 5–7 minute detailed interview walk-through of live features. |

---

## Recommended Study Order

To extract maximum value from this study guide, follow this progression:

```
┌────────────────────────────────────────────────────────┐
│  Stage 1: System Foundations                           │
│  LEARNING_ROADMAP.md ➔ PYTHON_FASTAPI_SQL.md           │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Stage 2: Frontend Engineering & Design Tokens         │
│  REACT_NEXTJS_TYPESCRIPT.md                            │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Stage 3: Quantitative Mathematics & Simulation        │
│  FINANCIAL_CALCULATIONS.md ➔ QUANTLAB_BACKTESTING.md    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Stage 4: AI Architecture & Security Hardening         │
│  AI_RAG_AND_TOOL_CALLING.md ➔ SECURITY_AND_DEPLOYMENT.md│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Stage 5: Placement & Interview Mastery                │
│  INTERVIEW_QA.md ➔ PROJECT_DEMO_SCRIPT.md              │
└────────────────────────────────────────────────────────┘
```

---

## How Each Topic Relates to QuantWeave

- **The Relational Ledger**: QuantWeave does not store mutable user cash or stock balances. All valuations and cost-basis metrics are deterministically computed on-the-fly from an append-only ledger (`portfolio_transactions`).
- **Mathematical Exactness**: Financial functions (such as XIRR, Sharpe ratio, and Wilder's RSI) implement numerical stability checks, zero-division guards, and Newton-Raphson solvers with bisection fallbacks.
- **Lookahead-Free Backtesting**: In QuantLab, strategies calculate signals on bar $t$'s Close and execute orders on bar $t+1$'s Open with simulated slippage and exchange fees.
- **Auditable AI Copilot**: The AI Copilot is strictly prohibited from guessing or fabricating numbers. Every analytical figure returned to the user is queried through authenticated, read-only Python tool functions with explicit markdown citations.
- **Design System Resilience**: 4 persistent themes (`signal-loom`, `daybreak`, `nebula`, `oceanic`) and 6 avatar presets are managed via dynamic CSS custom properties, eliminating runtime styling flashing.
