"""
Deterministic Synthetic Fixtures for Mutual Fund Intelligence (FundScope).

All fixtures and generated historical NAV records are synthetic test data,
clearly tagged with is_demo = True for educational research.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import random
from typing import List, Dict, Any
import uuid

from sqlalchemy.orm import Session

from app.models.mutual_fund import MutualFund, FundNAVHistory


DEMO_FUNDS: List[Dict[str, Any]] = [
    {
        "scheme_code": "122639",
        "isin": "INF879O01027",
        "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
        "amc_name": "PPFAS Mutual Fund",
        "category": "Equity",
        "subcategory": "Flexi Cap Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "NIFTY 500 TRI",
        "expense_ratio": Decimal("0.6300"),
        "aum_crores": Decimal("68500.00"),
        "fund_manager": "Rajeev Thakkar",
        "crisil_rating": 5,
        "base_nav": Decimal("44.5000"),
        "drift": 0.00065,  # ~17.5% annualized drift
        "volatility": 0.009,
        "seed": 101,
    },
    {
        "scheme_code": "118834",
        "isin": "INF769K01EZ1",
        "scheme_name": "Mirae Asset Large Cap Fund - Direct Plan - Growth",
        "amc_name": "Mirae Asset Mutual Fund",
        "category": "Equity",
        "subcategory": "Large Cap Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "NIFTY 50 TRI",
        "expense_ratio": Decimal("0.5400"),
        "aum_crores": Decimal("37200.00"),
        "fund_manager": "Gaurav Misra",
        "crisil_rating": 4,
        "base_nav": Decimal("72.0000"),
        "drift": 0.00055,  # ~14.5% annualized drift
        "volatility": 0.0085,
        "seed": 202,
    },
    {
        "scheme_code": "118989",
        "isin": "INF179K01BE2",
        "scheme_name": "HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth",
        "amc_name": "HDFC Mutual Fund",
        "category": "Equity",
        "subcategory": "Mid Cap Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "NIFTY Midcap 150 TRI",
        "expense_ratio": Decimal("0.7200"),
        "aum_crores": Decimal("58000.00"),
        "fund_manager": "Chirag Setalvad",
        "crisil_rating": 5,
        "base_nav": Decimal("82.0000"),
        "drift": 0.00085,  # ~23.5% annualized drift
        "volatility": 0.0125,
        "seed": 303,
    },
    {
        "scheme_code": "119841",
        "isin": "INF200K01T44",
        "scheme_name": "SBI Small Cap Fund - Direct Plan - Growth",
        "amc_name": "SBI Mutual Fund",
        "category": "Equity",
        "subcategory": "Small Cap Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "NIFTY Smallcap 250 TRI",
        "expense_ratio": Decimal("0.7400"),
        "aum_crores": Decimal("24500.00"),
        "fund_manager": "R. Srinivasan",
        "crisil_rating": 4,
        "base_nav": Decimal("90.0000"),
        "drift": 0.00090,  # ~25% annualized drift
        "volatility": 0.0145,
        "seed": 404,
    },
    {
        "scheme_code": "119551",
        "isin": "INF109K01912",
        "scheme_name": "ICICI Prudential Liquid Fund - Direct Plan - Growth",
        "amc_name": "ICICI Prudential Mutual Fund",
        "category": "Debt",
        "subcategory": "Liquid Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "CRISIL Liquid Debt Index",
        "expense_ratio": Decimal("0.2000"),
        "aum_crores": Decimal("48900.00"),
        "fund_manager": "Rohan Maru",
        "crisil_rating": 5,
        "base_nav": Decimal("310.0000"),
        "drift": 0.00025,  # ~6.8% steady annualized yield
        "volatility": 0.0003,
        "seed": 505,
    },
    {
        "scheme_code": "120152",
        "isin": "INF174K01LS2",
        "scheme_name": "Kotak Equity Hybrid Fund - Direct Plan - Growth",
        "amc_name": "Kotak Mahindra Mutual Fund",
        "category": "Hybrid",
        "subcategory": "Aggressive Hybrid Fund",
        "plan_type": "Direct",
        "option_type": "Growth",
        "benchmark_name": "CRISIL Hybrid 35+65 Aggressive Index",
        "expense_ratio": Decimal("0.6800"),
        "aum_crores": Decimal("19800.00"),
        "fund_manager": "Pankaj Tibrewal",
        "crisil_rating": 4,
        "base_nav": Decimal("36.0000"),
        "drift": 0.00050,  # ~13% annualized drift
        "volatility": 0.007,
        "seed": 606,
    },
]


def seed_demo_mutual_funds(db: Session, trading_days: int = 504) -> Dict[str, int]:
    """
    Idempotently seeds demo mutual fund schemes and deterministic historical NAV series.
    Generates ~2 calendar years of weekday NAV data.
    """
    funds_created = 0
    nav_rows_created = 0

    end_date = date.today()
    # Work backwards weekdays only
    current_date = end_date
    dates: List[date] = []
    while len(dates) < trading_days:
        if current_date.weekday() < 5:  # Monday to Friday
            dates.append(current_date)
        current_date -= timedelta(days=1)
    dates.reverse()

    for item in DEMO_FUNDS:
        fund = (
            db.query(MutualFund)
            .filter(MutualFund.scheme_code == item["scheme_code"])
            .first()
        )
        if not fund:
            fund = MutualFund(
                id=uuid.uuid4(),
                scheme_code=item["scheme_code"],
                isin=item["isin"],
                scheme_name=item["scheme_name"],
                amc_name=item["amc_name"],
                category=item["category"],
                subcategory=item["subcategory"],
                plan_type=item["plan_type"],
                option_type=item["option_type"],
                benchmark_name=item["benchmark_name"],
                expense_ratio=item["expense_ratio"],
                aum_crores=item["aum_crores"],
                fund_manager=item["fund_manager"],
                crisil_rating=item["crisil_rating"],
                is_active=True,
                is_demo=True,
            )
            db.add(fund)
            db.commit()
            db.refresh(fund)
            funds_created += 1

        # Check existing NAV count
        existing_navs = (
            db.query(FundNAVHistory)
            .filter(FundNAVHistory.fund_id == fund.id)
            .count()
        )
        if existing_navs >= len(dates):
            continue

        # Generate deterministic NAV path
        rng = random.Random(item["seed"])
        nav = float(item["base_nav"])
        drift = item["drift"]
        vol = item["volatility"]

        nav_objects: List[FundNAVHistory] = []
        for d in dates:
            # Check if record for fund and date already exists
            existing = (
                db.query(FundNAVHistory)
                .filter(FundNAVHistory.fund_id == fund.id, FundNAVHistory.nav_date == d)
                .first()
            )
            if existing:
                nav = float(existing.nav)
                continue

            # Deterministic geometric Brownian motion step
            ret = rng.gauss(drift, vol)
            nav = max(1.0, nav * (1.0 + ret))
            nav_dec = Decimal(str(nav)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

            nav_objects.append(
                FundNAVHistory(
                    fund_id=fund.id,
                    nav_date=d,
                    nav=nav_dec,
                    repurchase_price=nav_dec,
                    sale_price=nav_dec,
                    is_demo=True,
                )
            )

        if nav_objects:
            db.bulk_save_objects(nav_objects)
            db.commit()
            nav_rows_created += len(nav_objects)

    return {
        "funds_created": funds_created,
        "nav_rows_created": nav_rows_created,
    }
