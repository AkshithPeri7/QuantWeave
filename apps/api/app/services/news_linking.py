"""
Company and Sector News Linking Engine for QuantWeave MarketPulse.
"""

from decimal import Decimal
import re
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.market import ArticleInstrumentLink, NewsArticle


class NewsLinkingService:
    """
    Intelligent entity extraction and ticker mapping service.
    Maps financial headlines and descriptions to registered instruments while
    preventing false matches from ambiguous short acronyms.
    """

    # Common short words that must not be matched as bare tickers without company context
    AMBIGUOUS_TICKERS = {"IT", "ON", "AT", "IN", "BE", "AI", "OR", "SO", "AM", "IS", "AN", "AS"}

    # Common corporate suffixes stripped for fuzzy name matching
    CORP_SUFFIXES = re.compile(
        r"\b(ltd|limited|corp|corporation|inc|incorporated|plc|holdings|industries|technologies)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _clean_company_name(cls, name: str) -> str:
        clean = cls.CORP_SUFFIXES.sub("", name)
        return " ".join(clean.split()).strip()

    @classmethod
    def link_article_to_instruments(
        cls,
        db: Session,
        article: NewsArticle,
        instruments: Optional[List[Instrument]] = None,
    ) -> List[ArticleInstrumentLink]:
        """
        Analyzes article title and short description, matching against registered instruments.
        Returns newly created ArticleInstrumentLink objects (does not commit).
        """
        if instruments is None:
            instruments = db.query(Instrument).filter(Instrument.is_active == True).all()

        text = f"{article.title} {article.short_description or ''}"
        created_links: List[ArticleInstrumentLink] = []

        existing_links = {
            link.instrument_id
            for link in db.query(ArticleInstrumentLink.instrument_id)
            .filter(ArticleInstrumentLink.article_id == article.id)
            .all()
        }

        for inst in instruments:
            if inst.id in existing_links:
                continue

            match_method: Optional[str] = None
            confidence = Decimal("0.00")

            symbol = inst.symbol.upper().strip()
            name_clean = cls._clean_company_name(inst.company_name)

            # 1. Company Name Matching (High confidence)
            name_pattern = r"\b" + re.escape(name_clean) + r"\b"
            has_name_match = bool(re.search(name_pattern, text, re.IGNORECASE)) if len(name_clean) >= 4 else False

            # 2. Ticker Matching with boundary check
            has_ticker_match = False
            if symbol not in cls.AMBIGUOUS_TICKERS and len(symbol) >= 2:
                ticker_pattern = r"\b" + re.escape(symbol) + r"\b"
                has_ticker_match = bool(re.search(ticker_pattern, text, re.IGNORECASE))

            # 3. Determine method & confidence
            if has_name_match and has_ticker_match:
                match_method = "NAME_AND_TICKER"
                confidence = Decimal("0.99")
            elif has_name_match:
                match_method = "NAME"
                confidence = Decimal("0.95")
            elif has_ticker_match:
                match_method = "TICKER"
                confidence = Decimal("0.85")

            if match_method:
                link = ArticleInstrumentLink(
                    id=uuid.uuid4(),
                    article_id=article.id,
                    instrument_id=inst.id,
                    match_method=match_method,
                    match_confidence=confidence,
                    status="AUTO_MATCHED",
                )
                db.add(link)
                created_links.append(link)
                existing_links.add(inst.id)

        return created_links
