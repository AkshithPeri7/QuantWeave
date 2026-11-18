"""
Macroeconomic Intelligence Series and Historical Observations Fixtures for QuantWeave.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List
import uuid

from sqlalchemy.orm import Session

from app.models.market import MacroEconomicObservation, MacroEconomicSeries


MACRO_SERIES_DEFINITIONS = [
    {
        "series_id": "IN_REPO_RATE",
        "name": "RBI Policy Repo Rate",
        "unit": "%",
        "source": "Reserve Bank of India (RBI)",
        "description": "Benchmark lending rate at which the Reserve Bank of India lends money to commercial banks in the event of any shortfall of funds.",
        "frequency": "POLICY_MEETING",
        "is_demo": True,
        "observations": [
            ("2023-02-08", Decimal("6.50")),
            ("2023-04-06", Decimal("6.50")),
            ("2023-06-08", Decimal("6.50")),
            ("2023-08-10", Decimal("6.50")),
            ("2023-10-06", Decimal("6.50")),
            ("2023-12-08", Decimal("6.50")),
            ("2024-02-08", Decimal("6.50")),
            ("2024-04-05", Decimal("6.50")),
            ("2024-06-07", Decimal("6.50")),
            ("2024-08-08", Decimal("6.50")),
            ("2024-10-09", Decimal("6.50")),
            ("2024-12-06", Decimal("6.50")),
            ("2025-02-07", Decimal("6.50")),
        ],
    },
    {
        "series_id": "IN_CPI_INFLATION",
        "name": "India Headline CPI Inflation (YoY)",
        "unit": "%",
        "source": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "description": "Year-on-year percentage change in the Consumer Price Index (Combined) reflecting retail price inflation in Indian goods and services.",
        "frequency": "MONTHLY",
        "is_demo": True,
        "observations": [
            ("2023-01-31", Decimal("6.52")),
            ("2023-02-28", Decimal("6.44")),
            ("2023-03-31", Decimal("5.66")),
            ("2023-04-30", Decimal("4.70")),
            ("2023-05-31", Decimal("4.25")),
            ("2023-06-30", Decimal("4.81")),
            ("2023-07-31", Decimal("7.44")),
            ("2023-08-31", Decimal("6.83")),
            ("2023-09-30", Decimal("5.02")),
            ("2023-10-31", Decimal("4.87")),
            ("2023-11-30", Decimal("5.55")),
            ("2023-12-31", Decimal("5.69")),
            ("2024-01-31", Decimal("5.10")),
            ("2024-02-29", Decimal("5.09")),
            ("2024-03-31", Decimal("4.85")),
            ("2024-04-30", Decimal("4.83")),
            ("2024-05-31", Decimal("4.75")),
            ("2024-06-30", Decimal("5.08")),
            ("2024-07-31", Decimal("3.54")),
            ("2024-08-31", Decimal("3.65")),
            ("2024-09-30", Decimal("5.49")),
            ("2024-10-31", Decimal("6.21")),
            ("2024-11-30", Decimal("5.48")),
            ("2024-12-31", Decimal("5.22")),
            ("2025-01-31", Decimal("4.85")),
        ],
    },
    {
        "series_id": "IN_10Y_BOND_YIELD",
        "name": "India 10-Year Benchmark G-Sec Sovereign Yield",
        "unit": "%",
        "source": "Clearing Corporation of India (CCIL) / RBI",
        "description": "Yield on the 10-year sovereign government bond of the Republic of India, serving as the benchmark risk-free rate for domestic financial markets.",
        "frequency": "MONTHLY",
        "is_demo": True,
        "observations": [
            ("2023-01-31", Decimal("7.34")),
            ("2023-02-28", Decimal("7.42")),
            ("2023-03-31", Decimal("7.31")),
            ("2023-04-30", Decimal("7.12")),
            ("2023-05-31", Decimal("7.01")),
            ("2023-06-30", Decimal("7.11")),
            ("2023-07-31", Decimal("7.16")),
            ("2023-08-31", Decimal("7.18")),
            ("2023-09-30", Decimal("7.22")),
            ("2023-10-31", Decimal("7.36")),
            ("2023-11-30", Decimal("7.28")),
            ("2023-12-31", Decimal("7.18")),
            ("2024-01-31", Decimal("7.14")),
            ("2024-02-29", Decimal("7.07")),
            ("2024-03-31", Decimal("7.06")),
            ("2024-04-30", Decimal("7.19")),
            ("2024-05-31", Decimal("7.04")),
            ("2024-06-30", Decimal("7.00")),
            ("2024-07-31", Decimal("6.93")),
            ("2024-08-31", Decimal("6.86")),
            ("2024-09-30", Decimal("6.75")),
            ("2024-10-31", Decimal("6.84")),
            ("2024-11-30", Decimal("6.81")),
            ("2024-12-31", Decimal("6.78")),
            ("2025-01-31", Decimal("6.72")),
            ("2025-02-14", Decimal("6.68")),
        ],
    },
    {
        "series_id": "IN_GDP_GROWTH",
        "name": "India Real GDP Growth (YoY)",
        "unit": "%",
        "source": "National Statistical Office (NSO)",
        "description": "Year-on-year real quarterly economic expansion at constant prices.",
        "frequency": "QUARTERLY",
        "is_demo": True,
        "observations": [
            ("2023-03-31", Decimal("6.10")),
            ("2023-06-30", Decimal("7.80")),
            ("2023-09-30", Decimal("7.60")),
            ("2023-12-31", Decimal("8.40")),
            ("2024-03-31", Decimal("7.80")),
            ("2024-06-30", Decimal("6.70")),
            ("2024-09-30", Decimal("5.40")),
            ("2024-12-31", Decimal("6.20")),
        ],
    },
]


def seed_demo_macroeconomic_data(db: Session) -> Dict[str, int]:
    """Seeds macroeconomic series definitions and historical observations."""
    series_created = 0
    obs_created = 0

    for item in MACRO_SERIES_DEFINITIONS:
        series = db.query(MacroEconomicSeries).filter(MacroEconomicSeries.series_id == item["series_id"]).first()
        if not series:
            series = MacroEconomicSeries(
                series_id=item["series_id"],
                name=item["name"],
                unit=item["unit"],
                source=item["source"],
                description=item["description"],
                frequency=item["frequency"],
                is_demo=True,
            )
            db.add(series)
            db.flush()
            series_created += 1

        for d_str, val in item["observations"]:
            obs_date = date.fromisoformat(d_str)
            existing_obs = (
                db.query(MacroEconomicObservation)
                .filter(
                    MacroEconomicObservation.series_id == series.series_id,
                    MacroEconomicObservation.observation_date == obs_date,
                )
                .first()
            )
            if not existing_obs:
                obs = MacroEconomicObservation(
                    id=uuid.uuid4(),
                    series_id=series.series_id,
                    observation_date=obs_date,
                    value=val,
                    release_timestamp=datetime(obs_date.year, obs_date.month, obs_date.day, 12, 0, tzinfo=timezone.utc),
                    is_demo=True,
                )
                db.add(obs)
                obs_created += 1

    db.commit()
    return {
        "series_created": series_created,
        "observations_created": obs_created,
    }
