from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from app.schemas.market_data import InstrumentCreate, PriceBar


class BaseMarketDataProvider(ABC):
    """Abstract interface for financial market data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier, e.g. 'demo_synthetic', 'tej_hq'."""
        pass

    @property
    @abstractmethod
    def dataset(self) -> str:
        """Dataset identifier, e.g. 'nse_daily_equities'."""
        pass

    @property
    def terms_url(self) -> Optional[str]:
        """URL or reference to data license/terms."""
        return None

    @abstractmethod
    def fetch_instruments(self) -> List[InstrumentCreate]:
        """Retrieves reference instruments supported by this provider."""
        pass

    @abstractmethod
    def fetch_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[PriceBar]:
        """Retrieves historical daily price bars for a given symbol."""
        pass
