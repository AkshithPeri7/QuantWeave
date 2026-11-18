"""
Retrieval-Augmented Generation (RAG) Knowledge Base & Search Engine for QuantWeave.

Indexes:
- Financial indicator methodologies (SMA, EMA, Wilder's RSI, MACD, Bollinger Bands)
- Corporate finance valuation definitions (P/E, P/B, ROE, Debt/Equity)
- Portfolio intelligence formulas (TWR, XIRR, Sharpe, Sortino, Max Drawdown)
- FundScope mutual fund categorizations and comparison methodologies
- MarketPulse news sentiment heuristics and macroeconomic principles
- QuantLab strategy simulation assumptions, friction modeling, and overfitting hazards
- Educational disclaimers and SEBI regulatory boundaries

Architecture:
Uses lexical TF-IDF token matching with metadata scoring for fast, deterministic, offline retrieval.
Document upgrade path: Vector embeddings with pgvector or Chroma/FAISS when document volume exceeds 10,000 chunks.
"""

from dataclasses import dataclass
import math
import re
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeChunk:
    doc_id: str
    citation_key: str
    title: str
    category: str  # 'methodology', 'technical', 'fundamentals', 'portfolio', 'funds', 'market', 'quantlab'
    section: str
    content: str
    source_url: Optional[str] = None


KNOWLEDGE_CHUNKS: List[KnowledgeChunk] = [
    # 1. Platform Methodology & Legal Boundaries
    KnowledgeChunk(
        doc_id="METHOD-01",
        citation_key="[DOC-METHOD]",
        title="QuantWeave Platform Simulation & Research Scope",
        category="methodology",
        section="Educational Scope & Regulatory Disclaimer",
        content=(
            "QuantWeave is an educational analytics, research, and simulation platform. "
            "It is not a registered investment advisor, broker, or depository participant under SEBI regulations. "
            "Simulated backtests, historical calculations, and paper trading ledgers model market dynamics with synthetic "
            "data and do not represent actual live brokerage trades. Past performance is strictly illustrative and does not "
            "guarantee future capital returns."
        ),
        source_url="https://quantweave.test/docs/methodology",
    ),
    # 2. Technical Indicators (RSI, MACD, Moving Averages)
    KnowledgeChunk(
        doc_id="TECH-01",
        citation_key="[DOC-RSI]",
        title="Relative Strength Index (RSI) Calculation & Interpretation",
        category="technical",
        section="RSI 14 Wilder Smoothing",
        content=(
            "RSI measures momentum on a scale of 0 to 100 using J. Welles Wilder Jr.'s exponential smoothing. "
            "Calculated as 100 - (100 / (1 + RS)), where RS is Average Gain divided by Average Loss over 14 bars. "
            "Readings below 30 typically suggest oversold conditions, while readings above 70 suggest overbought conditions. "
            "RSI is a momentum gauge and does not guarantee price reversals."
        ),
        source_url="https://quantweave.test/docs/technicals/rsi",
    ),
    KnowledgeChunk(
        doc_id="TECH-02",
        citation_key="[DOC-MACD]",
        title="Moving Average Convergence Divergence (MACD)",
        category="technical",
        section="MACD (12, 26, 9) Standard",
        content=(
            "MACD is a trend-following momentum indicator showing the relationship between two exponential moving averages. "
            "MACD Line = 12-day EMA minus 26-day EMA. "
            "Signal Line = 9-day EMA of the MACD Line. "
            "MACD Histogram = MACD Line minus Signal Line. "
            "Bullish crossover occurs when MACD crosses above Signal Line; bearish crossover occurs when MACD crosses below."
        ),
        source_url="https://quantweave.test/docs/technicals/macd",
    ),
    KnowledgeChunk(
        doc_id="TECH-03",
        citation_key="[DOC-SMA-EMA]",
        title="Moving Averages: SMA vs EMA",
        category="technical",
        section="Trend Analysis with Moving Averages",
        content=(
            "Simple Moving Average (SMA) assigns equal weight to all prices in the window (e.g. 20, 50, 200 days). "
            "Exponential Moving Average (EMA) applies exponentially decreasing weights to older prices, reacting faster to recent volatility. "
            "Golden Cross: 50-day moving average crossing above 200-day moving average (bullish trend). "
            "Death Cross: 50-day moving average crossing below 200-day moving average (bearish trend)."
        ),
        source_url="https://quantweave.test/docs/technicals/moving-averages",
    ),
    KnowledgeChunk(
        doc_id="TECH-04",
        citation_key="[DOC-BOLLINGER]",
        title="Bollinger Bands Volatility Envelope",
        category="technical",
        section="Bollinger Bands (20, 2)",
        content=(
            "Bollinger Bands consist of a middle 20-day SMA and upper/lower bands set 2 standard deviations away. "
            "Band width expands during periods of high volatility and contracts during consolidation (The Squeeze). "
            "Prices touching the upper band indicate strength but may be overextended; touching the lower band indicates weakness."
        ),
        source_url="https://quantweave.test/docs/technicals/bollinger",
    ),
    # 3. Fundamental Valuation Ratios
    KnowledgeChunk(
        doc_id="FUND-01",
        citation_key="[DOC-RATIOS]",
        title="Fundamental Valuation Ratios: P/E, P/B, ROE, Debt/Equity",
        category="fundamentals",
        section="Financial Statement Ratios",
        content=(
            "P/E (Price-to-Earnings): Market price per share divided by annual Earnings Per Share (EPS). Indicates valuation relative to earnings. "
            "P/B (Price-to-Book): Market price per share divided by Book Value Per Share (Net Assets). "
            "ROE (Return on Equity): Net Income divided by Shareholders' Equity. Measures management's profitability with shareholders' capital. "
            "Debt-to-Equity: Total Debt divided by Total Equity. Gauges financial leverage and solvency risk."
        ),
        source_url="https://quantweave.test/docs/fundamentals/ratios",
    ),
    # 4. Portfolio Intelligence (TWR vs XIRR, Sharpe, Drawdown)
    KnowledgeChunk(
        doc_id="PORT-01",
        citation_key="[DOC-TWR-XIRR]",
        title="Portfolio Returns: Time-Weighted (TWR) vs Money-Weighted (XIRR)",
        category="portfolio",
        section="Performance Measurement Methodologies",
        content=(
            "Time-Weighted Return (TWR) measures compound investment growth while completely isolating the manager's performance "
            "from the timing and size of external cash deposits and withdrawals. "
            "Extended Internal Rate of Return (XIRR) is a money-weighted return that accounts for the exact dates and amounts "
            "of all deposits and withdrawals, reflecting the actual personal annualized yield achieved by the investor."
        ),
        source_url="https://quantweave.test/docs/portfolio/twr-xirr",
    ),
    KnowledgeChunk(
        doc_id="PORT-02",
        citation_key="[DOC-RISK-METRICS]",
        title="Risk-Adjusted Return Metrics: Sharpe, Sortino, Drawdown",
        category="portfolio",
        section="Institutional Risk Metrics",
        content=(
            "Sharpe Ratio: (Portfolio Return - Risk-Free Rate) / Annualized Volatility. Measures excess return per unit of total risk (Rf = 6.0% benchmark). "
            "Sortino Ratio: Excess return divided by Downside Deviation (semi-variance), ignoring upside volatility. "
            "Maximum Drawdown (MDD): The largest peak-to-trough percentage loss before a new peak is achieved. "
            "Calmar Ratio: Annualized return divided by Maximum Drawdown."
        ),
        source_url="https://quantweave.test/docs/portfolio/risk-metrics",
    ),
    # 5. FundScope (Mutual Funds, CAGR, SIP)
    KnowledgeChunk(
        doc_id="FUNDS-01",
        citation_key="[DOC-MUTUAL-FUNDS]",
        title="Mutual Fund Plans, Categories, and CAGR vs SIP Returns",
        category="funds",
        section="FundScope Intelligence",
        content=(
            "Direct Plans: Sold directly by the AMC with no distributor commissions, resulting in a lower expense ratio and higher compound returns. "
            "Regular Plans: Involve commission paid to distributors, resulting in higher expense ratios. "
            "CAGR (Compound Annual Growth Rate): Used for lump-sum investments held for 1 year or more: (End NAV / Start NAV)^(365/days) - 1. "
            "For SIPs (Systematic Investment Plans), multiple periodic cash flows require XIRR rather than simple CAGR."
        ),
        source_url="https://quantweave.test/docs/funds/plans",
    ),
    # 6. MarketPulse (Sentiment Heuristics & Macro Factors)
    KnowledgeChunk(
        doc_id="NEWS-01",
        citation_key="[DOC-SENTIMENT]",
        title="MarketPulse Sentiment Analysis & Macroeconomic Indicators",
        category="market",
        section="Sentiment Heuristics & Macro Influences",
        content=(
            "News sentiment in QuantWeave uses an explainable financial lexicon with negation and intensifier windows. "
            "Sentiment scores range from -1.0 (strongly negative) to +1.0 (strongly positive) and are heuristic observations, "
            "not predictive buy/sell signals. "
            "Macroeconomic series like CPI Inflation and RBI Repo Rate influence borrowing costs, corporate margins, and discount rates."
        ),
        source_url="https://quantweave.test/docs/market/sentiment",
    ),
    # 7. QuantLab (Next-Bar Execution, Friction, Overfitting)
    KnowledgeChunk(
        doc_id="QUANT-01",
        citation_key="[DOC-QUANTLAB]",
        title="QuantLab Strategy Backtesting & Overfitting Hazards",
        category="quantlab",
        section="Simulation Conventions & In-Sample / Out-of-Sample Validation",
        content=(
            "QuantLab enforces chronological bar execution without look-ahead bias: signals triggered at bar t close execute on bar t+1 Open. "
            "Transaction fees and slippage are modeled on all entries and exits. "
            "Overfitting Hazard: Optimizing strategy parameters exclusively on historical data risks curve-fitting noise. "
            "QuantLab enforces a 70/30 In-Sample (training) and Out-of-Sample (testing) split. If out-of-sample performance degrades severely, "
            "an Overfitting Warning is raised."
        ),
        source_url="https://quantweave.test/docs/quantlab/methodology",
    ),
]


class RAGRetrievalService:
    """
    Retrieval-Augmented Generation search service.
    Retrieves evidence snippets matching the user query with transparent citation metadata.
    """

    @classmethod
    def search(cls, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Token-based lexical matching with stop-word filtering and term-frequency scoring.
        """
        clean_q = re.sub(r"[^\w\s]", " ", query.lower())
        tokens = set(t for t in clean_q.split() if len(t) > 2)

        if not tokens:
            return []

        scored_chunks = []
        for chunk in KNOWLEDGE_CHUNKS:
            searchable_text = f"{chunk.title} {chunk.section} {chunk.content}".lower()
            matched_count = sum(1 for t in tokens if t in searchable_text)

            if matched_count > 0:
                # TF score normalized by token count
                score = matched_count / len(tokens)
                # Boost if token appears in title or section
                title_matches = sum(1 for t in tokens if t in chunk.title.lower() or t in chunk.section.lower())
                score += title_matches * 0.25

                if score >= min_score:
                    scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_chunks[:top_k]

        return [
            {
                "doc_id": c.doc_id,
                "citation_key": c.citation_key,
                "source_title": c.title,
                "section": c.section,
                "snippet": c.content,
                "source_url": c.source_url,
                "relevance_score": round(score, 3),
            }
            for score, c in top_results
        ]
