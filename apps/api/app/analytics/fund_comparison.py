"""
Mutual Fund Comparison Engine for QuantWeave FundScope.

Compares up to 4 mutual funds with:
- Normalized NAV time series (base 100 at common starting date)
- Side-by-side quantitative metrics (CAGR, Volatility, Max Drawdown, Expense Ratio, AUM, CRISIL Rating)
- Safe handling of non-overlapping trading dates
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.analytics.fund_analytics import (
    calculate_absolute_return,
    calculate_cagr,
    FundAnalyticsService,
)
from app.models.mutual_fund import MutualFund, FundNAVHistory


def compare_mutual_funds(
    db: Session,
    fund_ids: List[uuid.UUID],
    period: str = "1Y",
) -> Dict[str, Any]:
    """
    Compares up to 4 mutual funds over a historical time window.
    Rebases NAVs to 100 on start date for visual comparison.
    """
    if not fund_ids:
        raise ValueError("At least one mutual fund ID must be provided.")
    if len(fund_ids) > 4:
        raise ValueError("A maximum of 4 mutual funds can be compared simultaneously.")

    # 1. Fetch fund records
    funds = db.query(MutualFund).filter(MutualFund.id.in_(fund_ids)).all()
    if not funds:
        raise ValueError("None of the specified mutual funds were found.")

    found_ids = {f.id for f in funds}
    fund_map = {f.id: f for f in funds}

    # 2. Determine date cutoff based on period
    period = period.upper().strip()
    end_date = date.today()
    period_days_map = {
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365,
        "3Y": 1095,
        "5Y": 1825,
        "ALL": 3650,
    }
    days = period_days_map.get(period, 365)
    start_target = end_date - timedelta(days=days)

    # 3. Preload NAV histories for all funds within period
    nav_histories = (
        db.query(FundNAVHistory)
        .filter(
            FundNAVHistory.fund_id.in_(found_ids),
            FundNAVHistory.nav_date >= start_target - timedelta(days=10),
        )
        .order_by(FundNAVHistory.nav_date.asc())
        .all()
    )

    fund_nav_map: Dict[uuid.UUID, List[Tuple[date, Decimal]]] = {f_id: [] for f_id in found_ids}
    for row in nav_histories:
        fund_nav_map[row.fund_id].append((row.nav_date, row.nav))

    # 4. Compute metrics and normalized series for each fund
    metrics_list: List[Dict[str, Any]] = []
    normalized_series_by_fund: Dict[uuid.UUID, Dict[date, float]] = {}

    all_dates_set = set()

    for fund in funds:
        f_id = fund.id
        series = fund_nav_map.get(f_id, [])

        if not series or len(series) < 2:
            metrics_list.append({
                "fund_id": str(fund.id),
                "scheme_code": fund.scheme_code,
                "scheme_name": fund.scheme_name,
                "amc_name": fund.amc_name,
                "category": fund.category,
                "subcategory": fund.subcategory,
                "plan_type": fund.plan_type,
                "option_type": fund.option_type,
                "crisil_rating": fund.crisil_rating,
                "expense_ratio": float(fund.expense_ratio) if fund.expense_ratio else None,
                "aum_crores": float(fund.aum_crores) if fund.aum_crores else None,
                "latest_nav": None,
                "period_return_pct": None,
                "cagr_pct": None,
                "annualized_volatility_pct": None,
                "max_drawdown_pct": 0.0,
                "observation_count": len(series),
            })
            continue

        start_pt = series[0]
        end_pt = series[-1]
        base_nav = float(start_pt[1])

        # Normalized values
        norm_dict: Dict[date, float] = {}
        for d, n in series:
            norm_val = round((float(n) / base_nav) * 100.0, 2)
            norm_dict[d] = norm_val
            all_dates_set.add(d)
        normalized_series_by_fund[f_id] = norm_dict

        # Return & Risk calculations
        period_days = (end_pt[0] - start_pt[0]).days
        abs_ret = calculate_absolute_return(start_pt[1], end_pt[1])
        cagr_val = calculate_cagr(start_pt[1], end_pt[1], period_days)
        risk = FundAnalyticsService.calculate_risk_metrics(series)

        metrics_list.append({
            "fund_id": str(fund.id),
            "scheme_code": fund.scheme_code,
            "scheme_name": fund.scheme_name,
            "amc_name": fund.amc_name,
            "category": fund.category,
            "subcategory": fund.subcategory,
            "plan_type": fund.plan_type,
            "option_type": fund.option_type,
            "crisil_rating": fund.crisil_rating,
            "expense_ratio": float(fund.expense_ratio) if fund.expense_ratio else None,
            "aum_crores": float(fund.aum_crores) if fund.aum_crores else None,
            "latest_nav": float(end_pt[1]),
            "period_return_pct": float(abs_ret),
            "cagr_pct": float(cagr_val) if cagr_val is not None else None,
            "annualized_volatility_pct": risk["annualized_volatility_pct"],
            "max_drawdown_pct": risk["max_drawdown_pct"],
            "observation_count": len(series),
        })

    # 5. Build multi-line normalized chart points
    sorted_dates = sorted(all_dates_set)
    chart_points: List[Dict[str, Any]] = []

    # Downsample if too many points for chart performance
    step = max(1, len(sorted_dates) // 80)
    sampled_dates = [sorted_dates[i] for i in range(0, len(sorted_dates), step)]
    if sorted_dates and (not sampled_dates or sampled_dates[-1] != sorted_dates[-1]):
        sampled_dates.append(sorted_dates[-1])

    for cur_d in sampled_dates:
        pt: Dict[str, Any] = {
            "date": cur_d.isoformat(),
            "values": {},
        }
        for f_id in found_ids:
            norm_dict = normalized_series_by_fund.get(f_id, {})
            # Look up exact or latest known normalized value
            val = norm_dict.get(cur_d)
            pt["values"][str(f_id)] = val
        chart_points.append(pt)

    return {
        "period": period,
        "start_date": sorted_dates[0].isoformat() if sorted_dates else None,
        "end_date": sorted_dates[-1].isoformat() if sorted_dates else None,
        "funds": metrics_list,
        "normalized_chart": chart_points,
        "is_demo": any(f.is_demo for f in funds),
        "disclaimer": "DEMO DATA: Comparison metrics and normalized NAVs are simulated for educational evaluation.",
    }
