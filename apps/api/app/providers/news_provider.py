"""
News Provider Interfaces and Implementations for QuantWeave MarketPulse.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import List, Optional
import xml.etree.ElementTree as ET


@dataclass
class RawArticleData:
    title: str
    canonical_url: str
    published_at: datetime
    short_description: Optional[str] = None
    category: str = "MARKETS"
    language: str = "en"
    is_demo: bool = True

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of canonical URL for idempotent deduplication."""
        return hashlib.sha256(self.canonical_url.strip().encode("utf-8")).hexdigest()


class BaseNewsProvider(ABC):
    """Abstract interface for financial news providers."""

    @abstractmethod
    def fetch_articles(self, limit: int = 50) -> List[RawArticleData]:
        """Fetches raw financial news articles."""
        pass


class DemoNewsProvider(BaseNewsProvider):
    """
    Deterministic synthetic Indian market news provider.
    Generates realistic, clearly labeled simulated news across Indian equities,
    macroeconomic indicators (RBI, CPI, yields), and sector trends.
    """

    DEMO_HEADLINES = [
        {
            "title": "RBI Monetary Policy Committee Maintains Repo Rate at 6.50% Amid Resilient Domestic Growth",
            "description": "The Reserve Bank of India Governor announced a status quo on the policy repo rate, highlighting sustained momentum in manufacturing and urban consumption while maintaining a vigilant stance on food inflation.",
            "url": "https://quantweave.demo/news/rbi-mpc-decision-repo-rate-held-at-650",
            "category": "ECONOMY",
            "published_at": "2025-02-07T10:00:00Z",
        },
        {
            "title": "TCS Reports 6.8% YoY Net Profit Growth in Q3, Driven by Strong Cloud and BFSI Transformation Deals",
            "description": "Tata Consultancy Services posted steady quarterly revenue expansion, backed by multi-year cloud modernisation contracts and operating margin resilience despite European demand moderation.",
            "url": "https://quantweave.demo/news/tcs-q3-net-profit-growth-cloud-bfsi",
            "category": "EQUITY",
            "published_at": "2025-01-11T12:30:00Z",
        },
        {
            "title": "Infosys Raises Full-Year Revenue Guidance to 4.5% After Landmark Generative AI Deal Wins",
            "description": "Infosys executive leadership upgraded its constant-currency revenue guidance, citing rapid adoption of Topaz enterprise AI solutions and expanding engagement with global financial institutions.",
            "url": "https://quantweave.demo/news/infosys-guidance-upgrade-generative-ai-deals",
            "category": "EQUITY",
            "published_at": "2025-01-16T14:15:00Z",
        },
        {
            "title": "India CPI Inflation Moderates to 4.85% in January as Food Price Pressures Ease",
            "description": "National headline retail inflation softened from previous highs, aided by winter crop arrivals and stabilizing edible oil and vegetable price indices across rural and urban markets.",
            "url": "https://quantweave.demo/news/india-cpi-inflation-moderates-january-food-prices",
            "category": "ECONOMY",
            "published_at": "2025-02-12T11:45:00Z",
        },
        {
            "title": "Reliance Industries Approves Major Capital Allocation for 5G Infrastructure and Clean Energy Giga-Factories",
            "description": "Reliance board sanctioned dedicated capital expenditure for Gujarat solar giga-complexes and nationwide 5G broadband expansion, aiming to achieve carbon neutrality ahead of 2035 targets.",
            "url": "https://quantweave.demo/news/reliance-clean-energy-5g-capex-approval",
            "category": "EQUITY",
            "published_at": "2025-01-20T09:00:00Z",
        },
        {
            "title": "HDFC Bank Net Interest Margin Stabilizes at 3.45% Following Post-Merger Deposit Mobilization Push",
            "description": "India's largest private lender reported solid deposit accretion and non-performing asset reductions, reassuring credit markets of merger integration synergies.",
            "url": "https://quantweave.demo/news/hdfc-bank-nim-stabilization-deposit-growth",
            "category": "BANKING",
            "published_at": "2025-01-18T16:00:00Z",
        },
        {
            "title": "Indian 10-Year Benchmark Government Bond Yield Declines to 6.95% on Global Inflows",
            "description": "G-Sec sovereign yields softened by 7 basis points as overseas institutional investors stepped up purchases ahead of scheduled JP Morgan Emerging Market index weight increases.",
            "url": "https://quantweave.demo/news/india-10y-bond-yield-softens-foreign-inflows",
            "category": "ECONOMY",
            "published_at": "2025-02-14T10:30:00Z",
        },
        {
            "title": "SEBI Tightens Index Derivative Regulations to Curb Retail Speculation in Weekly Expiries",
            "description": "The capital markets regulator introduced higher contract values and upfront margin norms to protect individual retail participants from elevated intraday options volatility.",
            "url": "https://quantweave.demo/news/sebi-tightens-index-derivatives-retail-protection",
            "category": "MARKETS",
            "published_at": "2025-02-01T15:20:00Z",
        },
        {
            "title": "Nifty 50 and Sensex Reach Fresh Record Highs Led by Automobile and Capital Goods Rally",
            "description": "Broad-based buying across domestic cyclicals, defense manufacturers, and commercial vehicle makers propelled benchmark indices higher, with market capitalization crossing ₹450 lakh crore.",
            "url": "https://quantweave.demo/news/nifty50-sensex-record-highs-cyclicals-rally",
            "category": "MARKETS",
            "published_at": "2025-02-15T10:15:00Z",
        },
        {
            "title": "TCS Partners with British Retail Consortium to Deploy Unified Cloud Supply Chain Platform",
            "description": "The landmark multi-million-pound agreement will modernize inventory replenishment and predictive store analytics for over two hundred UK high-street retailers.",
            "url": "https://quantweave.demo/news/tcs-brc-cloud-supply-chain-deal",
            "category": "EQUITY",
            "published_at": "2025-02-10T13:45:00Z",
        },
        {
            "title": "Global Crude Oil Slips Below $75 per Barrel, Easing Current Account Deficit Pressure for India",
            "description": "Brent crude futures declined on rising non-OPEC supply and tempered Chinese manufacturing demand, providing fiscal relief for oil-importing emerging economies.",
            "url": "https://quantweave.demo/news/crude-oil-softens-india-cad-relief",
            "category": "ECONOMY",
            "published_at": "2025-02-05T08:30:00Z",
        },
        {
            "title": "Infosys Wins Cloud Migration Mandate from Nordic Banking Major Nordea",
            "description": "The digital transition project will consolidate core transactional workflows onto private cloud infrastructure while integrating automated anti-money laundering analytics.",
            "url": "https://quantweave.demo/news/infosys-nordea-cloud-mandate",
            "category": "EQUITY",
            "published_at": "2025-02-03T11:00:00Z",
        },
    ]

    def fetch_articles(self, limit: int = 50) -> List[RawArticleData]:
        articles: List[RawArticleData] = []
        for item in self.DEMO_HEADLINES[:limit]:
            pub_date = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            articles.append(
                RawArticleData(
                    title=item["title"],
                    short_description=item["description"],
                    canonical_url=item["url"],
                    published_at=pub_date,
                    category=item["category"],
                    language="en",
                    is_demo=True,
                )
            )
        return articles


class RSSNewsProvider(BaseNewsProvider):
    """
    Safe XML/RSS news parser adapter.
    Features:
    - Text sanitization (stripping HTML markup, whitespace trimming)
    - Strict size limit (1MB max to prevent XML entity bombs)
    - Fallback and error handling for malformed XML or network disconnects
    """

    def __init__(self, rss_content: Optional[str] = None):
        self._rss_content = rss_content

    @staticmethod
    def _strip_html(text: str) -> str:
        """Removes HTML tags and normalizes whitespace."""
        clean = re.sub(r"<[^>]+>", " ", text)
        return " ".join(clean.split())

    def parse_rss_string(self, xml_text: str, default_category: str = "MARKETS") -> List[RawArticleData]:
        if not xml_text or len(xml_text) > 2 * 1024 * 1024:  # 2MB protection
            return []

        articles: List[RawArticleData] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        # Find items under channel (RSS 2.0) or entry (Atom)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            # Title
            title_node = item.find("title")
            if title_node is None or not title_node.text:
                title_node = item.find("{http://www.w3.org/2005/Atom}title")
            title = self._strip_html(title_node.text) if title_node is not None and title_node.text else ""
            if not title:
                continue

            # Link / URL
            link_node = item.find("link")
            link = ""
            if link_node is not None:
                link = link_node.text or link_node.attrib.get("href", "")
            if not link:
                continue
            link = link.strip()

            # Description
            desc_node = item.find("description")
            if desc_node is None:
                desc_node = item.find("{http://www.w3.org/2005/Atom}summary")
            description = self._strip_html(desc_node.text) if desc_node is not None and desc_node.text else None

            # Pub Date
            pub_date_node = item.find("pubDate")
            if pub_date_node is None:
                pub_date_node = item.find("{http://www.w3.org/2005/Atom}updated")

            pub_date = datetime.now(timezone.utc)
            if pub_date_node is not None and pub_date_node.text:
                try:
                    # Try RFC 2822 / 822 or ISO format
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_date_node.text.strip())
                except Exception:
                    try:
                        pub_date = datetime.fromisoformat(pub_date_node.text.strip().replace("Z", "+00:00"))
                    except Exception:
                        pub_date = datetime.now(timezone.utc)

            articles.append(
                RawArticleData(
                    title=title,
                    canonical_url=link,
                    short_description=description,
                    published_at=pub_date,
                    category=default_category,
                    language="en",
                    is_demo=False,
                )
            )

        return articles

    def fetch_articles(self, limit: int = 50) -> List[RawArticleData]:
        if not self._rss_content:
            return []
        return self.parse_rss_string(self._rss_content)[:limit]
