"""
Mutual Fund Analytics Engine for QuantWeave FundScope.

Implements:
- Absolute returns and CAGR (Compound Annual Growth Rate)
- Trailing returns (1M, 3M, 6M, 1Y, 3Y, 5Y, Inception)
- Rolling returns analysis (1Y, 3Y rolling windows with min, max, average, and distribution)
- Annualized NAV volatility (sigma * sqrt(252))
- Maximum drawdown from peak NAV
- Lump-sum investment growth simulation
- Systematic Investment Plan (SIP) calculator with dated historical cash flows,
  accumulated units, final wealth, and true XIRR (Money-Weighted Return)
"""

from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Tuple

from app.analytics.portfolio_analytics import calculate_xirr


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Quantizes decimal to specified decimal places."""
    fmt = Decimal("10") ** -places
    return val.quantize(fmt, rounding=ROUND_HALF_UP)


def calculate_absolute_return(start_nav: Decimal, end_nav: Decimal) -> Decimal:
    """Calculates simple percentage return: ((end / start) - 1) * 100."""
    if start_nav <= Decimal("0"):
        return Decimal("0.00")
    ret = ((end_nav - start_nav) / start_nav) * Decimal("100")
    return quantize_dec(ret, 2)


def calculate_cagr(start_nav: Decimal, end_nav: Decimal, days: int) -> Optional[Decimal]:
    """
    Calculates Compound Annual Growth Rate (CAGR) as percentage:
    CAGR = ( (end / start) ^ (365 / days) - 1 ) * 100

    Returns None if days < 365 or if inputs are non-positive.
    """
    if days < 365 or start_nav <= Decimal("0") or end_nav <= Decimal("0"):
        return None

    try:
        ratio = float(end_nav / start_nav)
        if ratio <= 0:
            return None
        years = days / 365.0
        cagr_val = (ratio ** (1.0 / years)) - 1.0
        return quantize_dec(Decimal(str(cagr_val * 100.0)), 2)
    except (OverflowError, ZeroDivisionError, ValueError):
        return None


class FundAnalyticsService:
    """High-performance quantitative engine for mutual fund analytics and SIP simulation."""

    @staticmethod
    def _find_closest_nav_on_or_after(
        dates: List[date],
        navs: List[Decimal],
        target_date: date,
        max_lookforward_days: int = 7,
    ) -> Optional[Tuple[date, Decimal]]:
        """Finds earliest NAV on or after target_date (useful for SIP execution on non-trading days)."""
        idx = bisect_left(dates, target_date)
        if idx < len(dates):
            d = dates[idx]
            if (d - target_date).days <= max_lookforward_days:
                return d, navs[idx]
        return None

    @staticmethod
    def _find_closest_nav_on_or_before(
        dates: List[date],
        navs: List[Decimal],
        target_date: date,
        max_lookback_days: int = 7,
    ) -> Optional[Tuple[date, Decimal]]:
        """Finds latest NAV on or before target_date (strictly NO look-ahead bias)."""
        idx = bisect_right(dates, target_date) - 1
        if idx >= 0:
            d = dates[idx]
            if (target_date - d).days <= max_lookback_days:
                return d, navs[idx]
        return None

    @classmethod
    def calculate_trailing_returns(
        cls,
        nav_series: List[Tuple[date, Decimal]],
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Calculates trailing performance:
        - 1M, 3M, 6M (reported as absolute returns %)
        - 1Y, 3Y, 5Y (reported as annualized CAGR %)
        - Since Inception CAGR %
        """
        if not nav_series or len(nav_series) < 2:
            return {
                "return_1m_pct": None,
                "return_3m_pct": None,
                "return_6m_pct": None,
                "return_1y_cagr_pct": None,
                "return_3y_cagr_pct": None,
                "return_5y_cagr_pct": None,
                "return_inception_cagr_pct": None,
                "as_of_date": as_of_date.isoformat() if as_of_date else None,
                "latest_nav": None,
            }

        # Chronologically sort series: [(date, nav), ...]
        sorted_series = sorted(nav_series, key=lambda x: x[0])
        dates = [item[0] for item in sorted_series]
        navs = [item[1] for item in sorted_series]

        if as_of_date is None:
            as_of_date = dates[-1]

        # Latest NAV on or before as_of_date
        latest_match = cls._find_closest_nav_on_or_before(dates, navs, as_of_date)
        if not latest_match:
            return {
                "return_1m_pct": None,
                "return_3m_pct": None,
                "return_6m_pct": None,
                "return_1y_cagr_pct": None,
                "return_3y_cagr_pct": None,
                "return_5y_cagr_pct": None,
                "return_inception_cagr_pct": None,
                "as_of_date": as_of_date.isoformat(),
                "latest_nav": None,
            }

        end_date, end_nav = latest_match

        periods = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
            "3y": 1095,
            "5y": 1825,
        }

        results: Dict[str, Any] = {
            "as_of_date": end_date.isoformat(),
            "latest_nav": float(end_nav),
        }

        for period_key, day_count in periods.items():
            start_target = end_date - timedelta(days=day_count)
            # Find earliest available date on or before start_target
            match = cls._find_closest_nav_on_or_before(dates, navs, start_target, max_lookback_days=10)

            if match:
                s_date, s_nav = match
                actual_days = (end_date - s_date).days
                if period_key in ["1m", "3m", "6m"]:
                    abs_ret = calculate_absolute_return(s_nav, end_nav)
                    results[f"return_{period_key}_pct"] = float(abs_ret)
                    results[period_key.upper()] = float(abs_ret)
                else:
                    cagr_val = calculate_cagr(s_nav, end_nav, actual_days)
                    cagr_float = float(cagr_val) if cagr_val is not None else None
                    results[f"return_{period_key}_cagr_pct"] = cagr_float
                    results[period_key.upper()] = cagr_float
            else:
                if period_key in ["1m", "3m", "6m"]:
                    results[f"return_{period_key}_pct"] = None
                    results[period_key.upper()] = None
                else:
                    results[f"return_{period_key}_cagr_pct"] = None
                    results[period_key.upper()] = None

        # Since Inception
        first_date, first_nav = sorted_series[0]
        total_days = (end_date - first_date).days
        if total_days >= 365:
            inc_cagr = calculate_cagr(first_nav, end_nav, total_days)
            inc_val = float(inc_cagr) if inc_cagr is not None else None
            results["return_inception_cagr_pct"] = inc_val
            results["Inception"] = inc_val
        else:
            inc_abs = calculate_absolute_return(first_nav, end_nav)
            inc_val = float(inc_abs)
            results["return_inception_cagr_pct"] = inc_val
            results["Inception"] = inc_val

        return results

    @classmethod
    def calculate_rolling_returns(
        cls,
        nav_series: List[Tuple[date, Decimal]],
        window_days: int = 365,
        step_days: int = 5,
    ) -> Dict[str, Any]:
        """
        Calculates rolling window CAGR performance:
        Slides a window of `window_days` (default 365 for 1-Year rolling) day-by-day.
        """
        if not nav_series or len(nav_series) < 20:
            return {
                "window_days": window_days,
                "observation_count": 0,
                "mean_cagr_pct": None,
                "median_cagr_pct": None,
                "min_cagr_pct": None,
                "max_cagr_pct": None,
                "positive_periods_pct": None,
                "timeline": [],
            }

        sorted_series = sorted(nav_series, key=lambda x: x[0])
        dates = [item[0] for item in sorted_series]
        navs = [item[1] for item in sorted_series]

        start_date = dates[0]
        end_date = dates[-1]
        total_span = (end_date - start_date).days

        if total_span < window_days:
            return {
                "window_days": window_days,
                "observation_count": 0,
                "mean_cagr_pct": None,
                "median_cagr_pct": None,
                "min_cagr_pct": None,
                "max_cagr_pct": None,
                "positive_periods_pct": None,
                "timeline": [],
            }

        rolling_results: List[float] = []
        timeline: List[Dict[str, Any]] = []

        curr_end_target = start_date + timedelta(days=window_days)
        while curr_end_target <= end_date:
            curr_start_target = curr_end_target - timedelta(days=window_days)

            start_match = cls._find_closest_nav_on_or_before(dates, navs, curr_start_target, max_lookback_days=5)
            end_match = cls._find_closest_nav_on_or_before(dates, navs, curr_end_target, max_lookback_days=5)

            if start_match and end_match:
                s_d, s_n = start_match
                e_d, e_n = end_match
                actual_days = (e_d - s_d).days
                if actual_days >= window_days - 10:
                    cagr = calculate_cagr(s_n, e_n, actual_days)
                    if cagr is not None:
                        val = float(cagr)
                        rolling_results.append(val)
                        timeline.append({
                            "date": e_d.isoformat(),
                            "cagr_pct": val,
                        })

            curr_end_target += timedelta(days=step_days)

        if not rolling_results:
            return {
                "window_days": window_days,
                "observation_count": 0,
                "mean_cagr_pct": None,
                "median_cagr_pct": None,
                "min_cagr_pct": None,
                "max_cagr_pct": None,
                "positive_periods_pct": None,
                "timeline": [],
            }

        rolling_results.sort()
        n = len(rolling_results)
        mean_val = round(sum(rolling_results) / n, 2)
        median_val = round(rolling_results[n // 2] if n % 2 != 0 else (rolling_results[n // 2 - 1] + rolling_results[n // 2]) / 2.0, 2)
        min_val = round(rolling_results[0], 2)
        max_val = round(rolling_results[-1], 2)
        positive_pct = round((sum(1 for r in rolling_results if r > 0) / n) * 100.0, 1)

        return {
            "window_days": window_days,
            "observation_count": n,
            "mean_cagr_pct": mean_val,
            "median_cagr_pct": median_val,
            "min_cagr_pct": min_val,
            "max_cagr_pct": max_val,
            "positive_periods_pct": positive_pct,
            "timeline": timeline,
        }

    @classmethod
    def calculate_risk_metrics(
        cls,
        nav_series: List[Tuple[date, Decimal]],
    ) -> Dict[str, Any]:
        """Calculates annualized volatility and maximum peak-to-trough drawdown."""
        if not nav_series or len(nav_series) < 5:
            return {
                "annualized_volatility_pct": None,
                "max_drawdown_pct": 0.0,
            }

        sorted_series = sorted(nav_series, key=lambda x: x[0])
        navs = [float(item[1]) for item in sorted_series]

        # 1. Daily returns
        daily_returns: List[float] = []
        for i in range(1, len(navs)):
            if navs[i - 1] > 0:
                ret = (navs[i] - navs[i - 1]) / navs[i - 1]
                daily_returns.append(ret)

        annualized_vol: Optional[float] = None
        if len(daily_returns) >= 2:
            mean_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            daily_vol = math.sqrt(variance)
            annualized_vol = round(daily_vol * math.sqrt(252) * 100.0, 2)

        # 2. Max Drawdown
        peak = 0.0
        max_dd = 0.0
        for val in navs:
            if val > peak:
                peak = val
            if peak > 0:
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd

        max_dd_pct = round(max_dd * 100.0, 2)

        return {
            "annualized_volatility_pct": annualized_vol,
            "max_drawdown_pct": max_dd_pct,
        }

    @classmethod
    def calculate_lump_sum_growth(
        cls,
        nav_series: List[Tuple[date, Decimal]],
        amount: Decimal,
        start_date: date,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Simulates lump-sum investment growth from start_date to end_date using historical NAVs.
        """
        if not nav_series:
            raise ValueError("No NAV data available for this scheme.")

        sorted_series = sorted(nav_series, key=lambda x: x[0])
        dates = [item[0] for item in sorted_series]
        navs = [item[1] for item in sorted_series]

        if end_date is None:
            end_date = dates[-1]

        start_match = cls._find_closest_nav_on_or_after(dates, navs, start_date)
        if not start_match:
            raise ValueError(f"No NAV data found on or after requested start date {start_date}.")

        actual_start_date, start_nav = start_match

        end_match = cls._find_closest_nav_on_or_before(dates, navs, end_date)
        if not end_match or end_match[0] <= actual_start_date:
            raise ValueError(f"No valid NAV history between {actual_start_date} and {end_date}.")

        actual_end_date, end_nav = end_match

        units = (amount / start_nav).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        final_value = (units * end_nav).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_profit = final_value - amount
        abs_return = calculate_absolute_return(amount, final_value)

        days = (actual_end_date - actual_start_date).days
        cagr = calculate_cagr(amount, final_value, days)

        # Timeline for chart (downsampled to ~60 points max if long)
        timeline: List[Dict[str, Any]] = []
        filtered_points = [
            (d, n) for d, n in sorted_series if actual_start_date <= d <= actual_end_date
        ]
        step = max(1, len(filtered_points) // 60)
        for i in range(0, len(filtered_points), step):
            d, n = filtered_points[i]
            val = float((units * n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            timeline.append({
                "date": d.isoformat(),
                "invested_amount": float(amount),
                "portfolio_value": val,
                "nav": float(n),
            })
        # Ensure last point is included
        if filtered_points and timeline[-1]["date"] != actual_end_date.isoformat():
            d, n = filtered_points[-1]
            timeline.append({
                "date": d.isoformat(),
                "invested_amount": float(amount),
                "portfolio_value": float(final_value),
                "nav": float(n),
            })

        return {
            "initial_investment": float(amount),
            "start_date": actual_start_date.isoformat(),
            "end_date": actual_end_date.isoformat(),
            "start_nav": float(start_nav),
            "end_nav": float(end_nav),
            "units_accumulated": float(units),
            "final_value": float(final_value),
            "total_profit": float(total_profit),
            "absolute_return_pct": float(abs_return),
            "cagr_pct": float(cagr) if cagr is not None else None,
            "duration_days": days,
            "timeline": timeline,
        }

    @classmethod
    def calculate_sip(
        cls,
        nav_series: List[Tuple[date, Decimal]],
        monthly_amount: Decimal,
        start_date: date,
        end_date: Optional[date] = None,
        sip_day: int = 5,
    ) -> Dict[str, Any]:
        """
        Calculates realistic historical SIP (Systematic Investment Plan):
        - Executes monthly installments on the specified sip_day of each month
        - Resolves next trading day's NAV if market was closed on sip_day
        - Accumulates precise units
        - Solves exact Money-Weighted Return (XIRR) from actual dated cash flows
        """
        if not nav_series:
            raise ValueError("No NAV data available for this scheme.")

        sorted_series = sorted(nav_series, key=lambda x: x[0])
        dates = [item[0] for item in sorted_series]
        navs = [item[1] for item in sorted_series]

        if end_date is None:
            end_date = dates[-1]

        if start_date >= end_date:
            raise ValueError(f"Start date {start_date} must be earlier than end date {end_date}.")

        # Generate candidate monthly SIP dates
        installments: List[Dict[str, Any]] = []
        cash_flows: List[Tuple[date, Decimal]] = []

        curr_year = start_date.year
        curr_month = start_date.month

        total_units = Decimal("0.0000")
        total_invested = Decimal("0.00")
        timeline: List[Dict[str, Any]] = []

        while True:
            # Construct candidate SIP date
            try:
                candidate_date = date(curr_year, curr_month, sip_day)
            except ValueError:
                # E.g. Feb 30 -> pick 28
                candidate_date = date(curr_year, curr_month, 28)

            if candidate_date > end_date:
                break

            if candidate_date >= start_date:
                # Find closest NAV on or after candidate_date
                match = cls._find_closest_nav_on_or_after(dates, navs, candidate_date)
                if match and match[0] <= end_date:
                    actual_tx_date, tx_nav = match
                    units = (monthly_amount / tx_nav).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                    total_units += units
                    total_invested += monthly_amount

                    installments.append({
                        "installment_number": len(installments) + 1,
                        "scheduled_date": candidate_date.isoformat(),
                        "executed_date": actual_tx_date.isoformat(),
                        "nav": float(tx_nav),
                        "amount": float(monthly_amount),
                        "units": float(units),
                        "total_units": float(total_units),
                        "cumulative_invested": float(total_invested),
                    })

                    # Cash outflow from investor perspective (-CF)
                    cash_flows.append((actual_tx_date, -monthly_amount))

                    # Snapshot for timeline
                    current_val = (total_units * tx_nav).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    timeline.append({
                        "date": actual_tx_date.isoformat(),
                        "invested_amount": float(total_invested),
                        "portfolio_value": float(current_val),
                        "nav": float(tx_nav),
                    })

            # Advance to next month
            if curr_month == 12:
                curr_month = 1
                curr_year += 1
            else:
                curr_month += 1

        if not installments:
            raise ValueError(f"No installments could be executed between {start_date} and {end_date}.")

        # Ending valuation on end_date
        end_match = cls._find_closest_nav_on_or_before(dates, navs, end_date)
        if not end_match:
            end_match = (dates[-1], navs[-1])

        final_date, final_nav = end_match
        final_value = (total_units * final_nav).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_profit = final_value - total_invested
        abs_return = calculate_absolute_return(total_invested, final_value)

        # Terminal cash inflow to investor for XIRR (+CF)
        cash_flows.append((final_date, final_value))

        xirr_result = calculate_xirr(cash_flows)
        xirr_pct = float(xirr_result) if xirr_result is not None else None

        # Append final terminal point to timeline if not present
        if timeline and timeline[-1]["date"] != final_date.isoformat():
            timeline.append({
                "date": final_date.isoformat(),
                "invested_amount": float(total_invested),
                "portfolio_value": float(final_value),
                "nav": float(final_nav),
            })

        return {
            "monthly_amount": float(monthly_amount),
            "start_date": installments[0]["executed_date"],
            "end_date": final_date.isoformat(),
            "installments_count": len(installments),
            "total_invested": float(total_invested),
            "final_value": float(final_value),
            "total_profit": float(total_profit),
            "absolute_return_pct": float(abs_return),
            "xirr_pct": xirr_pct,
            "units_accumulated": float(total_units),
            "latest_nav": float(final_nav),
            "installments": installments,
            "timeline": timeline,
        }
