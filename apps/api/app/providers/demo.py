from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import random
from typing import Dict, List, Optional
from app.providers.base import BaseMarketDataProvider
from app.schemas.market_data import InstrumentCreate, PriceBar

# Baseline reference instruments (NSE focus)
DEMO_INSTRUMENTS = [
    {
        "exchange": "NSE",
        "symbol": "RELIANCE",
        "isin": "INE002A01018",
        "company_name": "Reliance Industries Limited",
        "instrument_type": "equity",
        "sector": "Energy",
        "industry": "Oil & Gas Refining & Marketing",
        "currency": "INR",
        "base_price": Decimal("2850.00"),
        "volatility": 0.015,
        "drift": 0.0003,
    },
    {
        "exchange": "NSE",
        "symbol": "TCS",
        "isin": "INE467B01029",
        "company_name": "Tata Consultancy Services Limited",
        "instrument_type": "equity",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "currency": "INR",
        "base_price": Decimal("3920.00"),
        "volatility": 0.014,
        "drift": 0.0002,
    },
    {
        "exchange": "NSE",
        "symbol": "INFY",
        "isin": "INE009A01021",
        "company_name": "Infosys Limited",
        "instrument_type": "equity",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "currency": "INR",
        "base_price": Decimal("1780.00"),
        "volatility": 0.016,
        "drift": 0.0002,
    },
    {
        "exchange": "NSE",
        "symbol": "HDFCBANK",
        "isin": "INE040A01034",
        "company_name": "HDFC Bank Limited",
        "instrument_type": "equity",
        "sector": "Financial Services",
        "industry": "Private Sector Bank",
        "currency": "INR",
        "base_price": Decimal("1650.00"),
        "volatility": 0.013,
        "drift": 0.00025,
    },
    {
        "exchange": "NSE",
        "symbol": "ICICIBANK",
        "isin": "INE090A01021",
        "company_name": "ICICI Bank Limited",
        "instrument_type": "equity",
        "sector": "Financial Services",
        "industry": "Private Sector Bank",
        "currency": "INR",
        "base_price": Decimal("1210.00"),
        "volatility": 0.015,
        "drift": 0.00035,
    },
    {
        "exchange": "NSE",
        "symbol": "BHARTIARTL",
        "isin": "INE397D01024",
        "company_name": "Bharti Airtel Limited",
        "instrument_type": "equity",
        "sector": "Telecommunication",
        "industry": "Telecom Services",
        "currency": "INR",
        "base_price": Decimal("1540.00"),
        "volatility": 0.014,
        "drift": 0.0004,
    },
    {
        "exchange": "NSE",
        "symbol": "ITC",
        "isin": "INE154A01025",
        "company_name": "ITC Limited",
        "instrument_type": "equity",
        "sector": "Consumer Goods",
        "industry": "Diversified FMCG",
        "currency": "INR",
        "base_price": Decimal("480.00"),
        "volatility": 0.011,
        "drift": 0.0002,
    },
    {
        "exchange": "NSE",
        "symbol": "SBIN",
        "isin": "INE062A01020",
        "company_name": "State Bank of India",
        "instrument_type": "equity",
        "sector": "Financial Services",
        "industry": "Public Sector Bank",
        "currency": "INR",
        "base_price": Decimal("810.00"),
        "volatility": 0.017,
        "drift": 0.0003,
    },
    {
        "exchange": "NSE",
        "symbol": "LT",
        "isin": "INE018A01030",
        "company_name": "Larsen & Toubro Limited",
        "instrument_type": "equity",
        "sector": "Construction",
        "industry": "Civil Construction & Engineering",
        "currency": "INR",
        "base_price": Decimal("3620.00"),
        "volatility": 0.015,
        "drift": 0.0003,
    },
    {
        "exchange": "NSE",
        "symbol": "HINDUNILVR",
        "isin": "INE030A01027",
        "company_name": "Hindustan Unilever Limited",
        "instrument_type": "equity",
        "sector": "Consumer Goods",
        "industry": "Personal Care & Household Products",
        "currency": "INR",
        "base_price": Decimal("2430.00"),
        "volatility": 0.012,
        "drift": 0.00015,
    },
]


def _generate_trading_days(end_date: date, count: int = 250) -> List[date]:
    """Generates consecutive weekdays backwards from end_date (skipping weekends)."""
    days: List[date] = []
    current = end_date
    while len(days) < count:
        # Monday=0, Sunday=6
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    days.reverse()
    return days


class DemoMarketDataProvider(BaseMarketDataProvider):
    """
    Deterministic synthetic market data provider for Indian equities.
    All data is marked as synthetic demo data with no live market claims.
    """

    @property
    def provider_name(self) -> str:
        return "demo_synthetic"

    @property
    def dataset(self) -> str:
        return "nse_reference_daily"

    @property
    def terms_url(self) -> Optional[str]:
        return "https://quantweave.local/legal/synthetic-demo-data"

    def fetch_instruments(self) -> List[InstrumentCreate]:
        return [
            InstrumentCreate(
                exchange=item["exchange"],
                symbol=item["symbol"],
                isin=item["isin"],
                company_name=item["company_name"],
                instrument_type=item["instrument_type"],
                sector=item["sector"],
                industry=item["industry"],
                currency=item["currency"],
                is_active=True,
                is_demo=True,
            )
            for item in DEMO_INSTRUMENTS
        ]

    def fetch_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[PriceBar]:
        instrument_meta = next(
            (item for item in DEMO_INSTRUMENTS if item["symbol"].upper() == symbol.upper()),
            None,
        )
        if not instrument_meta:
            return []

        # Fixed target end date (e.g. today or reference anchor date)
        ref_end_date = end_date or date(2026, 11, 16)
        trading_days = _generate_trading_days(ref_end_date, count=250)

        # Seed random with symbol hash for deterministic, reproducible price walks
        seed_value = sum(ord(c) for c in symbol) * 10007
        rng = random.Random(seed_value)

        current_price = float(instrument_meta["base_price"])
        volatility = instrument_meta["volatility"]
        drift = instrument_meta["drift"]

        prices: List[PriceBar] = []

        for trade_day in trading_days:
            # Geometric Brownian Motion daily step
            return_pct = rng.gauss(drift, volatility)
            new_close = current_price * (1.0 + return_pct)
            new_close = max(new_close, 1.0)  # Bound to positive

            # Intraday fluctuation
            intraday_range = current_price * volatility * rng.uniform(0.8, 2.2)
            open_price = current_price + rng.uniform(-intraday_range * 0.3, intraday_range * 0.3)
            open_price = max(open_price, 0.5)

            high_price = max(open_price, new_close) + abs(rng.gauss(0, intraday_range * 0.5))
            low_price = min(open_price, new_close) - abs(rng.gauss(0, intraday_range * 0.5))
            low_price = max(low_price, 0.1)

            # Volume simulation: base + volatility spike
            base_vol = rng.randint(200_000, 3_000_000)
            volume = int(base_vol * (1.0 + abs(return_pct) * 20.0))

            # Quantize to 2 decimal places using Decimal
            q = Decimal("0.01")
            d_open = Decimal(str(round(open_price, 2))).quantize(q, rounding=ROUND_HALF_UP)
            d_high = Decimal(str(round(high_price, 2))).quantize(q, rounding=ROUND_HALF_UP)
            d_low = Decimal(str(round(low_price, 2))).quantize(q, rounding=ROUND_HALF_UP)
            d_close = Decimal(str(round(new_close, 2))).quantize(q, rounding=ROUND_HALF_UP)

            # Strict sanity check
            d_high = max(d_high, d_open, d_close)
            d_low = min(d_low, d_open, d_close)

            bar = PriceBar(
                trade_date=trade_day,
                open=d_open,
                high=d_high,
                low=d_low,
                close=d_close,
                adjusted_close=d_close,
                volume=volume,
                currency="INR",
                is_demo=True,
            )
            prices.append(bar)
            current_price = new_close

        # Filter by requested date range if provided
        if start_date:
            prices = [p for p in prices if p.trade_date >= start_date]
        if end_date:
            prices = [p for p in prices if p.trade_date <= end_date]

        return prices
