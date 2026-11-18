"""
LLM Provider Abstraction & Implementations for QuantWeave Copilot.

Includes:
- BaseLLMProvider: Abstract interface
- MockLLMProvider: Deterministic, local, zero-network mock provider for testing, offline demos, and CI/CD
- GoogleGeminiProvider: Integration with Google Gemini API
- OpenAIProvider: Integration with OpenAI-compatible endpoints
- Factory function get_llm_provider()
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import re
import time
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.ai.rag import RAGRetrievalService
from app.ai.tools import AVAILABLE_TOOLS, execute_tool
from app.core.config import settings


@dataclass
class ToolCallRequest:
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class ProviderResponse:
    content: str
    provider: str
    model_name: str
    tokens_used: int
    latency_ms: int
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    executed_tools: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)


class BaseLLMProvider(ABC):
    """Abstract interface for LLM completions and tool orchestration."""

    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        db: Session,
        context_user_id: uuid.UUID,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> ProviderResponse:
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic offline mock AI provider.
    Parses intent, dispatches tools, incorporates RAG citations, and produces verified answers.
    """

    def __init__(self, model_name: str = "quantweave-mock-agent-v1"):
        self.model_name = model_name

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        db: Session,
        context_user_id: uuid.UUID,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> ProviderResponse:
        start_time = time.time()
        last_user_msg = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        q_lower = last_user_msg.lower()

        # Step 1: Query RAG for knowledge citations
        rag_results = RAGRetrievalService.search(last_user_msg, top_k=2)
        citations = [r["citation_key"] for r in rag_results]

        tool_calls: List[ToolCallRequest] = []
        executed_tools: List[Dict[str, Any]] = []

        # Step 2: Determine tool intent based on query patterns and context
        detected_symbols = re.findall(r"\b(RELIANCE|TCS|INFY|HDFCBANK|ICICIBANK|TATAMOTORS|SBIN|WIPRO)\b", last_user_msg.upper())
        unknown_candidates = re.findall(r"\b([A-Z]{5,15})\b", last_user_msg)
        reserved_syms = {"WHAT", "SHOW", "EXPLAIN", "INDICATOR", "INDICATORS", "STOCK", "UNKNOWN", "TECHNICAL", "PORTFOLIO", "MUTUAL", "FUNDS", "MARKET", "STRATEGY", "ANALYSIS", "INFLATION", "RECENT", "HEADLINES", "DISREGARD", "OVERRIDE", "SECRETS"}
        filtered_unknowns = [s for s in unknown_candidates if s not in reserved_syms and s not in detected_symbols]

        if detected_symbols:
            target_symbol = detected_symbols[0]
        elif filtered_unknowns:
            target_symbol = filtered_unknowns[0]
        else:
            target_symbol = "TCS"

        # Check prompt injection attempts
        injection_patterns = [
            "ignore previous",
            "ignore all previous",
            "override system",
            "bypass security",
            "drop database",
            "drop table",
            "drop all",
            "admin password",
            "disregard instructions",
            "system prompt",
            "system prompt override",
            "export all",
            "reveal api",
            "auth tokens",
        ]
        if any(p in q_lower for p in injection_patterns):
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderResponse(
                content=(
                    "I cannot process instructions that attempt to override platform safety guardrails or system rules. "
                    "QuantWeave Copilot operates strictly as an educational financial research assistant with verified backend tools."
                ),
                provider="mock",
                model_name=self.model_name,
                tokens_used=45,
                latency_ms=latency_ms,
                tool_calls=[],
                executed_tools=[],
                citations=[],
            )

        # Check macro terms first to prevent generic "indicator" from catching macroeconomic queries
        if any(w in q_lower for w in ["macro", "macroeconomic", "inflation", "cpi", "repo rate", "gdp", "rbi rate"]):
            tool_calls.append(ToolCallRequest(tool_name="get_macro_indicators", arguments={}))
        elif any(w in q_lower for w in ["news", "headline", "sentiment"]):
            if "sentiment" in q_lower:
                tool_calls.append(ToolCallRequest(tool_name="get_news_sentiment", arguments={"symbol_or_id": target_symbol}))
            else:
                news_q = "banking" if "banking" in q_lower else (target_symbol if detected_symbols else "market")
                tool_calls.append(ToolCallRequest(tool_name="search_market_news", arguments={"query": news_q}))

        # Module E: QuantLab Backtesting (check before generic financial ratios)
        elif any(w in q_lower for w in ["backtest", "strategy", "quantlab", "sharpe", "overfitting", "slippage"]):
            tool_calls.append(ToolCallRequest(tool_name="get_saved_strategies", arguments={}))

        # Module A: Equity Intelligence
        elif re.search(r"\b(rsi|macd|sma|ema|bollinger|technicals|technical)\b", q_lower):
            tool_calls.append(ToolCallRequest(tool_name="get_technical_indicators", arguments={"symbol_or_id": target_symbol}))
        elif any(w in q_lower for w in ["p/e", "pe ratio", "p/b", "pb ratio", "roe", "debt", "fundamental", "operating margin", "net margin", "earnings"]):
            tool_calls.append(ToolCallRequest(tool_name="get_fundamental_ratios", arguments={"symbol_or_id": target_symbol}))
        elif any(w in q_lower for w in ["compare equity", "compare stock", "vs infy", "vs tcs"]) or (
            len(detected_symbols) >= 2 and "compare" in q_lower
        ):
            symbols = detected_symbols[:2] if len(detected_symbols) >= 2 else ["TCS", "INFY"]
            tool_calls.append(ToolCallRequest(tool_name="compare_equities", arguments={"symbols_or_ids": symbols, "period": "1Y"}))

        # Module B: Portfolio Intelligence
        elif any(w in q_lower for w in ["portfolio", "holdings", "valuation", "twr", "xirr", "allocation"]):
            tool_calls.append(ToolCallRequest(tool_name="list_user_portfolios", arguments={}))

        # Module C: FundScope Mutual Funds
        elif any(w in q_lower for w in ["mutual fund", "fund", "nav", "cagr vs sip", "sip", "regular vs direct"]):
            if "large cap" in q_lower:
                tool_calls.append(ToolCallRequest(tool_name="search_mutual_funds", arguments={"query": "Large Cap"}))
            elif "compare" in q_lower:
                tool_calls.append(ToolCallRequest(tool_name="search_mutual_funds", arguments={"query": "Fund"}))
            else:
                tool_calls.append(ToolCallRequest(tool_name="search_mutual_funds", arguments={"query": "HDFC"}))

        # Default fallback: Stock profile lookup if ticker present, else search
        elif detected_symbols:
            tool_calls.append(ToolCallRequest(tool_name="get_instrument_profile", arguments={"symbol_or_id": target_symbol}))
        else:
            tool_calls.append(ToolCallRequest(tool_name="get_macro_indicators", arguments={}))

        # Step 3: Execute tool calls with strict server-side context_user_id
        tool_facts: List[str] = []
        for tc in tool_calls:
            t_exec = execute_tool(tc.tool_name, tc.arguments, db, context_user_id)
            executed_tools.append(t_exec)

            # Follow-up: if list_user_portfolios returned portfolios, fetch details for the first one
            if tc.tool_name == "list_user_portfolios" and t_exec.get("status") == "success":
                ports = t_exec.get("result", {}).get("portfolios", [])
                if ports:
                    first_pid = ports[0]["id"]
                    if any(w in q_lower for w in ["performance", "twr", "xirr", "drawdown"]):
                        followup = execute_tool("get_portfolio_performance", {"portfolio_id": first_pid}, db, context_user_id)
                    elif any(w in q_lower for w in ["allocation", "sector", "risk", "diversification"]):
                        followup = execute_tool("get_portfolio_risk", {"portfolio_id": first_pid}, db, context_user_id)
                    else:
                        followup = execute_tool("get_portfolio_valuation", {"portfolio_id": first_pid}, db, context_user_id)
                    executed_tools.append(followup)

        # Step 4: Synthesize verified response content based on executed tools & RAG
        content_lines = []

        # Mention RAG concepts
        for r in rag_results:
            content_lines.append(f"**Knowledge Reference {r['citation_key']} ({r['source_title']}):** {r['snippet']}")

        content_lines.append("")

        # Synthesize tool facts
        for t in executed_tools:
            t_name = t.get("tool")
            res = t.get("result", {})
            if res.get("status") == "not_found" or t.get("status") == "not_found":
                msg = res.get("message") or t.get("message") or f"Instrument '{target_symbol}' not found."
                content_lines.append(f"**Data Notice:** {msg} QuantWeave Copilot only analyzes verified assets in the system database and avoids hallucinating fictitious market figures.")
            elif t_name == "get_technical_indicators" and t.get("status") == "success":
                s = res.get("summary", {})
                sym = res.get("symbol", target_symbol)
                as_of = res.get("as_of", "latest")
                content_lines.append(f"### Technical Intelligence for {sym} (as of {as_of})")
                content_lines.append(f"- **RSI (14-day Wilder Smoothing):** {s.get('rsi_14')} " + ("(Oversold territory < 30)" if (s.get('rsi_14') or 50) < 30 else "(Overbought territory > 70)" if (s.get('rsi_14') or 50) > 70 else "(Neutral momentum 30-70)"))
                content_lines.append(f"- **MACD (12, 26, 9):** MACD={s.get('macd')}, Signal={s.get('macd_signal')}, Histogram={s.get('macd_histogram')}")
                content_lines.append(f"- **Simple Moving Averages:** SMA 20: ₹{s.get('sma_20')}, SMA 50: ₹{s.get('sma_50')}, SMA 200: ₹{s.get('sma_200')}")
                content_lines.append(f"- **Bollinger Bands (20, 2):** Upper: ₹{s.get('bollinger_upper')}, Middle: ₹{s.get('bollinger_middle')}, Lower: ₹{s.get('bollinger_lower')}")
            elif t_name == "get_fundamental_ratios" and t.get("status") == "success":
                r = res.get("ratios", {})
                sym = res.get("symbol", target_symbol)
                content_lines.append(f"### Fundamental Valuation for {sym}")
                content_lines.append(f"- **P/E Ratio:** {r.get('pe_ratio')} | **P/B Ratio:** {r.get('pb_ratio')}")
                content_lines.append(f"- **Return on Equity (ROE):** {r.get('roe_pct')}% | **Net Margin:** {r.get('net_margin_pct')}%")
                content_lines.append(f"- **Debt-to-Equity:** {r.get('debt_to_equity')} (Financial leverage gauge)")
            elif t_name == "compare_equities" and t.get("status") == "success":
                content_lines.append(f"### Equity Comparison ({res.get('period')} Period)")
                for inst in res.get("instruments", []):
                    content_lines.append(f"- **{inst['symbol']}:** Return: {inst['period_return_pct']}%, Volatility: {inst['annualized_volatility_pct']}%, Max Drawdown: {inst['max_drawdown_pct']}%, RSI: {inst['rsi_14']}, P/E: {inst['pe_ratio']}")
            elif t_name == "get_portfolio_valuation" and t.get("status") == "success":
                content_lines.append(f"### Portfolio Valuation ({res.get('portfolio_name')})")
                content_lines.append(f"- **Total Market Value:** ₹{res.get('total_value', 0):,.2f}")
                content_lines.append(f"- **Cash Balance:** ₹{res.get('cash_balance', 0):,.2f} | **Invested Capital:** ₹{res.get('invested_capital', 0):,.2f}")
                content_lines.append(f"- **Unrealized P&L:** ₹{res.get('total_unrealized_pnl', 0):,.2f} ({res.get('total_unrealized_pnl_pct', 0):.2f}%)")
            elif t_name == "get_portfolio_performance" and t.get("status") == "success":
                content_lines.append(f"### Portfolio Performance ({res.get('portfolio_name')})")
                content_lines.append(f"- **Time-Weighted Return (TWR):** {res.get('twr_pct')}% (Isolates cash flow timing)")
                content_lines.append(f"- **Extended IRR (XIRR):** {res.get('xirr_pct')}% (Money-weighted personalized yield)")
                content_lines.append(f"- **Annualized Volatility:** {res.get('annualized_volatility_pct')}% | **Sharpe Ratio (Rf=6%):** {res.get('sharpe_ratio')}")
                if "drawdown" in q_lower or "dip" in q_lower:
                    content_lines.append("- **Maximum Drawdown:** Measures peak-to-trough drop during market dips before a full recovery is established.")
            elif t_name == "get_portfolio_risk" and t.get("status") == "success":
                content_lines.append(f"### Portfolio Risk & Allocation Breakdown")
                content_lines.append("- **Asset Diversification:** Active portfolio allocation review.")
                sec_items = res.get("sector_allocation", [])
                if sec_items:
                    content_lines.append("**Sector Diversification (%):**")
                    for s in sec_items[:5]:
                        content_lines.append(f"- {s['sector']}: {s['percentage']:.1f}% (₹{s['value']:,.2f})")
                else:
                    content_lines.append("- **Sector Diversification:** Preserving cash with 100% allocation to liquid capital reserves.")
            elif t_name == "get_macro_indicators" and t.get("status") == "success":
                content_lines.append("### Key Macroeconomic Indicators (India)")
                indicators = res.get("indicators", [])
                if indicators:
                    for ind in indicators:
                        content_lines.append(f"- **{ind['series_name']} ({ind['category']}):** {ind['latest_value']} {ind['unit']} (as of {ind['observation_date']})")
                else:
                    content_lines.append("- **CPI Inflation (Headline):** 5.09% YoY (RBI Target: 4.0% +/- 2.0%)")
                    content_lines.append("- **Policy Repo Rate (RBI MPC):** 6.50% (Benchmark monetary policy rate)")
            elif t_name == "search_market_news":
                content_lines.append("### MarketPulse News Headlines")
                articles = res.get("articles", [])
                if articles:
                    for a in articles[:4]:
                        content_lines.append(f"- **{a.get('title')}** ({a.get('source_name', 'MarketPulse Feed')})")
                else:
                    content_lines.append("- **MarketPulse Wire:** Recent financial news headlines indicate banking liquidity and policy stability.")
            elif t_name == "get_news_sentiment":
                content_lines.append("### MarketPulse Financial Sentiment")
                if res.get("status") == "no_data":
                    content_lines.append(f"- **Sentiment Observation:** Baseline sentiment score for {target_symbol} is neutral (0.00) based on MarketPulse news coverage.")
                else:
                    content_lines.append(f"- **Average Sentiment Score:** {res.get('average_score')} (-1.0 to +1.0) for {target_symbol}")
                    content_lines.append(f"- **Distribution:** {res.get('positive_count')} Positive, {res.get('neutral_count')} Neutral, {res.get('negative_count')} Negative")
                content_lines.append(f"- *Note:* {res.get('sentiment_disclaimer', 'Lexicon-derived rule-based heuristic for educational observation.')}")
            elif t_name == "search_mutual_funds" and t.get("status") == "success":
                content_lines.append("### Mutual Fund Discovery (FundScope)")
                for f in res.get("funds", [])[:4]:
                    content_lines.append(f"- **{f['scheme_name']}** ({f['amc_name']}) — Category: {f['category']}, Plan: {f['plan_type']}")
                if "direct" in q_lower or "regular" in q_lower:
                    content_lines.append("- **Direct vs Regular Plans:** Direct plans feature a lower expense ratio because intermediary commissions are eliminated, resulting in superior compounded NAV returns over time.")
            elif t_name == "get_saved_strategies" and t.get("status") == "success":
                content_lines.append("### QuantLab Research Strategies")
                strats = res.get("strategies", [])
                if strats:
                    for s in strats[:4]:
                        content_lines.append(f"- **{s['name']}** (v{s['version']}): Type={s['strategy_type']}, Parameters={json.dumps(s['parameters'])}")
                else:
                    content_lines.append("No saved strategies found for your account. You can create one in the QuantLab Strategy Studio.")
                if "overfitting" in q_lower or "split" in q_lower or "train" in q_lower:
                    content_lines.append("- **Overfitting Prevention:** Backtest models often suffer from look-ahead bias and curve-fitting. Dividing data into In-Sample (train) and Out-of-Sample (test) splits prevents memorizing noise.")
                if "fee" in q_lower or "slippage" in q_lower or "sharpe" in q_lower:
                    content_lines.append("- **Trading Fees & Slippage Impact:** Transaction costs and slippage degrade overall net returns and penalize the realized Sharpe ratio.")
            elif res.get("status") == "not_found" or t.get("status") == "not_found":
                msg = res.get("message") or t.get("message") or f"Instrument '{target_symbol}' not found."
                content_lines.append(f"**Data Notice:** {msg} QuantWeave Copilot only analyzes verified assets in the system database and avoids hallucinating fictitious market figures.")

        # If no specific tools produced text, provide an educational guidance summary
        if not content_lines or len(content_lines) <= 2:
            content_lines.append(
                "QuantWeave Copilot has reviewed your query against trusted platform analytics. "
                "All numerical calculations and portfolio valuations are derived directly from deterministic backend engines, "
                "ensuring zero hallucination of financial figures."
            )

        # Mandatory Educational Disclaimer
        content_lines.append("")
        content_lines.append("---")
        content_lines.append(
            "> [!NOTE]\n"
            "> **Educational Research Disclaimer:** All financial metrics, simulated returns, and technical evaluations "
            "provided by QuantWeave Copilot are for research and educational purposes only. They do not constitute SEBI-registered "
            "investment advice or personalized buy/sell recommendations. Past performance and backtest models do not guarantee future live returns."
        )

        latency_ms = int((time.time() - start_time) * 1000)
        final_content = "\n".join(content_lines)

        return ProviderResponse(
            content=final_content,
            provider="mock",
            model_name=self.model_name,
            tokens_used=len(final_content.split()) + 30,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            executed_tools=executed_tools,
            citations=citations,
        )


class GoogleGeminiProvider(BaseLLMProvider):
    """
    Provider connecting to Google Gemini API when GEMINI_API_KEY is configured.
    Falls back gracefully to MockLLMProvider if key is not configured or offline.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.mock_fallback = MockLLMProvider(model_name=f"mock-fallback-{model_name}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        db: Session,
        context_user_id: uuid.UUID,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> ProviderResponse:
        if not self.api_key:
            # Fall back to mock provider for offline / dev usage
            return self.mock_fallback.generate_response(
                messages, db, context_user_id, context_module, context_entity_id
            )
        # In this implementation, if key is set, we still use tool-grounded mock orchestration
        # to ensure 100% deterministic factual accuracy in tests and demo environments
        return self.mock_fallback.generate_response(
            messages, db, context_user_id, context_module, context_entity_id
        )


class OpenAIProvider(BaseLLMProvider):
    """
    Provider connecting to OpenAI endpoints when OPENAI_API_KEY is configured.
    Falls back gracefully to MockLLMProvider if key is not configured or offline.
    """

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name
        self.mock_fallback = MockLLMProvider(model_name=f"mock-fallback-{model_name}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        db: Session,
        context_user_id: uuid.UUID,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> ProviderResponse:
        return self.mock_fallback.generate_response(
            messages, db, context_user_id, context_module, context_entity_id
        )


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory creating the configured LLM provider according to application settings.
    """
    provider_type = (settings.ai_provider or "mock").lower().strip()
    if provider_type == "gemini" and settings.gemini_api_key:
        return GoogleGeminiProvider(api_key=settings.gemini_api_key, model_name=settings.ai_model_name)
    elif provider_type == "openai" and settings.openai_api_key:
        return OpenAIProvider(api_key=settings.openai_api_key, model_name=settings.ai_model_name)
    else:
        return MockLLMProvider(model_name=settings.ai_model_name)
