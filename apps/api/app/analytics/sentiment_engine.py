"""
Finance-Domain Sentiment Analysis Engine for QuantWeave MarketPulse.

Implements a deterministic, domain-weighted financial sentiment analyzer
tailored to Indian and global financial reporting, earnings announcements,
and macroeconomic releases.
"""

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SentimentResult:
    label: str  # POSITIVE, NEGATIVE, NEUTRAL
    positive_score: float
    negative_score: float
    neutral_score: float
    confidence: float
    model_name: str = "quantweave-fin-lexicon-v1"

    @property
    def net_score(self) -> float:
        """Net sentiment between -1.0 (bearish) and +1.0 (bullish)."""
        return round(self.positive_score - self.negative_score, 4)


class FinancialSentimentEngine:
    """
    High-speed, deterministic financial lexicon and rule-based sentiment model.
    Calibrated on financial terminology with phrase-level idioms and negation handling.
    """

    MODEL_VERSION = "quantweave-fin-lexicon-v1"

    # Multi-word finance idioms with weighted sentiment
    PHRASE_SCORES = {
        "record highs": 2.5,
        "record high": 2.5,
        "net profit growth": 2.0,
        "guidance upgrade": 2.0,
        "raises guidance": 2.0,
        "margin expansion": 2.0,
        "strong cloud": 1.5,
        "status quo": 0.5,
        "inflation moderates": 1.5,
        "pressures ease": 1.5,
        "sovereign yields softened": 1.0,
        "easing current account deficit": 1.5,
        "fiscal relief": 1.5,
        "beat estimates": 2.0,
        "above expectations": 1.8,
        "landmark deal": 1.8,
        "deal wins": 1.5,
        "profit surge": 2.5,
        # Negative phrases
        "guidance downgrade": -2.5,
        "cuts guidance": -2.5,
        "margin contraction": -2.0,
        "misses estimates": -2.0,
        "below expectations": -1.8,
        "regulatory penalty": -2.0,
        "credit downgrade": -2.5,
        "widening deficit": -1.8,
        "inflation surges": -2.0,
        "demand moderation": -1.2,
        "growth slows": -1.5,
        "steep losses": -2.5,
        "fraud investigation": -3.0,
    }

    POSITIVE_WORDS = {
        "growth": 1.0, "profit": 1.2, "surge": 1.5, "gain": 1.0, "rally": 1.4,
        "upgrade": 1.5, "expansion": 1.2, "resilience": 1.0, "resilient": 1.0,
        "inflows": 1.2, "inflow": 1.2, "outperform": 1.5, "outperformance": 1.5,
        "optimistic": 1.0, "bullish": 1.5, "soars": 1.5, "soared": 1.5,
        "dividend": 1.0, "highs": 1.2, "eases": 1.0, "moderates": 0.8,
        "rebound": 1.2, "recovery": 1.2, "synergies": 1.2, "steady": 0.8,
    }

    NEGATIVE_WORDS = {
        "decline": 1.2, "declines": 1.2, "declined": 1.2, "drop": 1.2, "drops": 1.2,
        "slump": 1.6, "loss": 1.4, "losses": 1.5, "downgrade": 1.8, "deficit": 1.4,
        "contraction": 1.4, "pressure": 1.0, "pressures": 1.0, "debt": 0.8,
        "default": 2.0, "penalty": 1.8, "warning": 1.4, "bearish": 1.5,
        "curb": 1.0, "tightens": 0.8, "speculation": 0.8, "volatility": 0.8,
        "weak": 1.2, "weakness": 1.2, "pessimistic": 1.2, "inflation": 0.8,
    }

    NEGATION_WORDS = {"not", "no", "never", "failed", "fails", "failing", "neither", "hardly", "barely"}

    @classmethod
    def analyze_text(cls, text: str) -> SentimentResult:
        """
        Analyzes a financial text and returns probability distribution
        (positive, negative, neutral) with final classification and confidence.
        """
        if not text or not text.strip():
            return SentimentResult(
                label="NEUTRAL",
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                confidence=0.5,
                model_name=cls.MODEL_VERSION,
            )

        clean_text = text.lower().strip()

        pos_accum = 0.0
        neg_accum = 0.0

        # 1. Match multi-word phrases first
        matched_phrases = set()
        for phrase, weight in cls.PHRASE_SCORES.items():
            if phrase in clean_text:
                if weight > 0:
                    pos_accum += weight
                else:
                    neg_accum += abs(weight)
                matched_phrases.add(phrase)

        # 2. Tokenize words for unigram evaluation
        tokens = re.findall(r"\b[a-z]{2,}\b", clean_text)
        negation_window = 0

        for i, token in enumerate(tokens):
            if token in cls.NEGATION_WORDS:
                negation_window = 4
                continue

            is_negated = negation_window > 0

            # Check positive words
            if token in cls.POSITIVE_WORDS:
                weight = cls.POSITIVE_WORDS[token]
                if is_negated:
                    neg_accum += weight * 1.5
                    negation_window = 0
                else:
                    pos_accum += weight

            # Check negative words
            elif token in cls.NEGATIVE_WORDS:
                weight = cls.NEGATIVE_WORDS[token]
                if is_negated:
                    pos_accum += weight * 0.8
                    negation_window = 0
                else:
                    neg_accum += weight

            if negation_window > 0:
                negation_window -= 1

        total_signal = pos_accum + neg_accum

        if total_signal < 0.8:
            # Largely factual or neutral context
            p_neu = round(0.70 + (0.8 - total_signal) * 0.25, 4)
            rem = max(0.0, 1.0 - p_neu)
            if pos_accum > neg_accum:
                p_pos = round(rem * 0.7, 4)
                p_neg = round(rem * 0.3, 4)
            elif neg_accum > pos_accum:
                p_pos = round(rem * 0.3, 4)
                p_neg = round(rem * 0.7, 4)
            else:
                p_pos = round(rem / 2, 4)
                p_neg = round(rem / 2, 4)
            label = "NEUTRAL"
            confidence = round(p_neu, 4)
        else:
            diff = pos_accum - neg_accum
            ratio_pos = pos_accum / total_signal
            ratio_neg = neg_accum / total_signal

            p_neu = round(max(0.10, 0.40 - total_signal * 0.05), 4)
            rem = 1.0 - p_neu

            p_pos = round(rem * ratio_pos, 4)
            p_neg = round(rem * ratio_neg, 4)

            # Ensure sum is 1.0
            sum_scores = p_pos + p_neg + p_neu
            if sum_scores > 0:
                p_pos = round(p_pos / sum_scores, 4)
                p_neg = round(p_neg / sum_scores, 4)
                p_neu = round(1.0 - (p_pos + p_neg), 4)

            if diff >= 0.8:
                label = "POSITIVE"
                confidence = round(p_pos, 4)
            elif diff <= -0.8:
                label = "NEGATIVE"
                confidence = round(p_neg, 4)
            else:
                label = "NEUTRAL"
                confidence = round(max(p_neu, 0.50), 4)

        return SentimentResult(
            label=label,
            positive_score=p_pos,
            negative_score=p_neg,
            neutral_score=p_neu,
            confidence=confidence,
            model_name=cls.MODEL_VERSION,
        )

    @classmethod
    def aggregate_sentiments(cls, sentiment_list: List[SentimentResult]) -> Dict[str, Any]:
        """
        Aggregates a collection of sentiment results over a time window.
        Produces counts, percentages, average scores, and overall market pulse.
        """
        total = len(sentiment_list)
        if total == 0:
            return {
                "total_articles": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_pct": 0.0,
                "negative_pct": 0.0,
                "neutral_pct": 0.0,
                "net_sentiment_score": 0.0,
                "overall_classification": "NEUTRAL",
                "average_confidence": 0.0,
            }

        pos_count = sum(1 for s in sentiment_list if s.label == "POSITIVE")
        neg_count = sum(1 for s in sentiment_list if s.label == "NEGATIVE")
        neu_count = sum(1 for s in sentiment_list if s.label == "NEUTRAL")

        avg_pos = sum(s.positive_score for s in sentiment_list) / total
        avg_neg = sum(s.negative_score for s in sentiment_list) / total
        avg_conf = sum(s.confidence for s in sentiment_list) / total

        net_score = round(avg_pos - avg_neg, 4)

        if net_score >= 0.15:
            overall = "BULLISH"
        elif net_score <= -0.15:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return {
            "total_articles": total,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "positive_pct": round((pos_count / total) * 100, 2),
            "negative_pct": round((neg_count / total) * 100, 2),
            "neutral_pct": round((neu_count / total) * 100, 2),
            "net_sentiment_score": net_score,
            "overall_classification": overall,
            "average_confidence": round(avg_conf, 4),
        }
