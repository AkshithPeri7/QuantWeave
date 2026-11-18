"""
Portfolio Analytics and Performance Engine for QuantWeave.

Implements:
- Current portfolio valuation (cash + market value of active holdings)
- Weighted-average cost basis (WACB) & unrealized/realized P&L
- Asset and sector allocation breakdowns
- Daily portfolio valuation timeline (strictly avoiding look-ahead bias)
- Time-Weighted Return (TWR) using end-of-day cash flow convention
- Money-Weighted Return / XIRR with numerical solver
- Annualized portfolio volatility (sigma * sqrt(252))
- Sharpe ratio (with configurable risk-free rate assumption Rf=6.0%)
- Maximum drawdown
"""

from bisect import bisect_right
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.models.portfolio_transaction import PortfolioTransaction
from app.models.price_history import PriceHistory
from app.services.portfolio import PortfolioService

# Default Indian sovereign/repo benchmark risk-free rate
DEFAULT_RISK_FREE_RATE = Decimal("0.06")  # 6.0%


def quantize_currency(val: Decimal) -> Decimal:
    """Quantize to 2 decimal places for financial reporting."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize_qty(val: Decimal) -> Decimal:
    """Quantize share quantity to 4 decimal places."""
    return val.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def quantize_pct(val: Decimal) -> Decimal:
    """Quantize percentage to 2 decimal places."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_xirr(
    cash_flows: List[Tuple[date, Decimal]],
    guess: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> Optional[Decimal]:
    """
    Calculates Money-Weighted Return (XIRR) using the Newton-Raphson method
    with fallback to bisection.

    Cash flow convention from investor's perspective:
    - Capital deposit / investment: negative cash flow (-CF)
    - Capital withdrawal: positive cash flow (+CF)
    - Terminal valuation: positive cash flow (+CF)

    Formula:
    f(r) = sum( CF_i / (1 + r)^((d_i - d_0) / 365.0) ) = 0

    Returns:
        Annualized return as Decimal percentage (e.g. 15.5 for 15.5%),
        or None if cash flows lack sign changes or solver fails to converge.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None

    # Filter out zero cash flows
    valid_cfs = [(d, float(cf)) for d, cf in cash_flows if abs(float(cf)) > 1e-8]
    if len(valid_cfs) < 2:
        return None

    has_positive = any(cf > 0 for _, cf in valid_cfs)
    has_negative = any(cf < 0 for _, cf in valid_cfs)
    if not (has_positive and has_negative):
        return None

    # Sort chronologically
    valid_cfs.sort(key=lambda x: x[0])
    d0 = valid_cfs[0][0]

    # Precalculate year fractions: (d_i - d0) / 365.0
    year_fracs = [((d - d0).days) / 365.0 for d, _ in valid_cfs]
    amounts = [cf for _, cf in valid_cfs]

    # Check if total period is 0 days
    if year_fracs[-1] == 0:
        return None

    def xnpv(rate: float) -> float:
        if rate <= -0.999999:
            return float("inf")
        val = 0.0
        for yf, cf in zip(year_fracs, amounts):
            try:
                denom = (1.0 + rate) ** yf
                if abs(denom) < 1e-12:
                    return float("inf")
                val += cf / denom
            except (OverflowError, ZeroDivisionError):
                return float("inf")
        return val

    def xnpv_prime(rate: float) -> float:
        if rate <= -0.999999:
            return float("inf")
        val = 0.0
        for yf, cf in zip(year_fracs, amounts):
            try:
                denom = (1.0 + rate) ** (yf + 1.0)
                if abs(denom) < 1e-12:
                    return float("inf")
                val -= (yf * cf) / denom
            except (OverflowError, ZeroDivisionError):
                return float("inf")
        return val

    # Attempt Newton-Raphson
    r = guess
    for _ in range(max_iterations):
        npv = xnpv(r)
        if math.isnan(npv) or math.isinf(npv):
            break
        if abs(npv) < tolerance:
            pct = Decimal(str(r * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return pct

        deriv = xnpv_prime(r)
        if math.isnan(deriv) or abs(deriv) < 1e-10:
            break

        step = npv / deriv
        r_new = r - step

        # Guard against wild jumps outside plausible boundaries
        if r_new <= -0.99 or r_new > 50.0:
            break

        if abs(r_new - r) < tolerance:
            pct = Decimal(str(r_new * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return pct

        r = r_new

    # Bisection fallback over range [-0.95, 10.0]
    low = -0.95
    high = 10.0
    f_low = xnpv(low)
    f_high = xnpv(high)

    if not math.isnan(f_low) and not math.isnan(f_high) and (f_low * f_high < 0):
        for _ in range(120):
            mid = (low + high) / 2.0
            f_mid = xnpv(mid)
            if abs(f_mid) < tolerance or (high - low) < tolerance:
                pct = Decimal(str(mid * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return pct
            if f_low * f_mid < 0:
                high = mid
                f_high = f_mid
            else:
                low = mid
                f_low = f_mid

    return None


class PortfolioAnalyticsService:
    """Computes comprehensive portfolio valuation, historical equity curves, and performance/risk metrics."""

    @classmethod
    def get_portfolio_valuation(
        cls,
        db: Session,
        portfolio: Portfolio,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Calculates current or as-of-date valuation for a portfolio, including:
        - Cash and position balances (WACB)
        - Market value of active holdings
        - Unrealized and realized P&L
        - Allocation breakdown by asset and sector
        """
        if as_of_date is None:
            as_of_date = date.today()

        cash_balance, holdings_data = PortfolioService.calculate_current_balances(
            db, portfolio.id, as_of_date=as_of_date
        )

        # Collect instruments
        instrument_ids = list(holdings_data.keys())
        instruments = {}
        if instrument_ids:
            inst_records = (
                db.query(Instrument)
                .filter(Instrument.id.in_(instrument_ids))
                .all()
            )
            instruments = {inst.id: inst for inst in inst_records}

        holdings_list: List[Dict[str, Any]] = []
        total_holdings_market_value = Decimal("0.00")
        total_cost_basis = Decimal("0.00")
        total_unrealized_pnl = Decimal("0.00")
        total_realized_pnl = Decimal("0.00")

        for inst_id, h in holdings_data.items():
            inst = instruments.get(inst_id)
            if not inst:
                continue

            qty = h["quantity"]
            avg_price = h["avg_price"]
            total_invested = h["total_invested"]
            realized_pnl = h["realized_pnl"]
            total_realized_pnl += realized_pnl

            # If closed position (qty == 0), don't include in active holdings list
            if qty <= Decimal("0.00000000"):
                continue

            # Query most recent price on or before as_of_date (strictly NO look-ahead)
            latest_price_record = (
                db.query(PriceHistory)
                .filter(
                    PriceHistory.instrument_id == inst_id,
                    PriceHistory.trade_date <= as_of_date,
                )
                .order_by(PriceHistory.trade_date.desc())
                .first()
            )

            current_price: Optional[Decimal] = None
            price_date: Optional[date] = None
            is_demo = inst.is_demo
            is_stale = False

            if latest_price_record:
                current_price = latest_price_record.close
                price_date = latest_price_record.trade_date
                is_demo = latest_price_record.is_demo or is_demo
                if (as_of_date - price_date).days > 7:
                    is_stale = True
                market_val = (qty * current_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                # Price is unavailable: report market_val as invested cost without inventing prices
                is_stale = True
                market_val = total_invested.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            unrealized_pnl = market_val - total_invested
            unrealized_pnl_pct = (
                ((unrealized_pnl / total_invested) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if total_invested > Decimal("0")
                else Decimal("0.00")
            )

            total_holdings_market_value += market_val
            total_cost_basis += total_invested
            total_unrealized_pnl += unrealized_pnl

            holdings_list.append({
                "instrument_id": str(inst.id),
                "symbol": inst.symbol,
                "exchange": inst.exchange,
                "company_name": inst.company_name,
                "sector": inst.sector or "Unclassified",
                "quantity": quantize_qty(qty),
                "average_buy_price": quantize_currency(avg_price),
                "current_price": quantize_currency(current_price) if current_price else None,
                "cost_basis": quantize_currency(total_invested),
                "market_value": quantize_currency(market_val),
                "unrealized_pnl": quantize_currency(unrealized_pnl),
                "unrealized_pnl_percent": unrealized_pnl_pct,
                "realized_pnl": quantize_currency(realized_pnl),
                "price_date": price_date.isoformat() if price_date else None,
                "is_stale": is_stale,
                "is_demo": is_demo,
            })

        total_portfolio_value = (cash_balance + total_holdings_market_value).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_pnl = total_unrealized_pnl + total_realized_pnl

        # Calculate allocations
        asset_allocations: List[Dict[str, Any]] = []
        sector_totals: Dict[str, Decimal] = {}

        if total_portfolio_value > Decimal("0"):
            # Cash allocation
            cash_pct = ((cash_balance / total_portfolio_value) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            asset_allocations.append({
                "name": "Cash",
                "symbol": "CASH",
                "value": quantize_currency(cash_balance),
                "percentage": cash_pct,
                "type": "cash",
            })

            # Instruments allocation
            for h_item in holdings_list:
                m_val = Decimal(str(h_item["market_value"]))
                alloc_pct = ((m_val / total_portfolio_value) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                h_item["allocation_percent"] = alloc_pct
                asset_allocations.append({
                    "name": h_item["company_name"],
                    "symbol": h_item["symbol"],
                    "value": m_val,
                    "percentage": alloc_pct,
                    "type": "equity",
                })

                sec = h_item["sector"]
                sector_totals[sec] = sector_totals.get(sec, Decimal("0.00")) + m_val
        else:
            for h_item in holdings_list:
                h_item["allocation_percent"] = Decimal("0.00")

        # Sector breakdown
        sector_allocations: List[Dict[str, Any]] = []
        if total_portfolio_value > Decimal("0"):
            if cash_balance > Decimal("0"):
                sector_allocations.append({
                    "sector": "Cash",
                    "value": quantize_currency(cash_balance),
                    "percentage": ((cash_balance / total_portfolio_value) * Decimal("100")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ),
                })
            for sec_name, sec_val in sector_totals.items():
                sec_pct = ((sec_val / total_portfolio_value) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                sector_allocations.append({
                    "sector": sec_name,
                    "value": quantize_currency(sec_val),
                    "percentage": sec_pct,
                })

        # Sort allocations descending
        asset_allocations.sort(key=lambda x: x["value"], reverse=True)
        sector_allocations.sort(key=lambda x: x["value"], reverse=True)

        return {
            "portfolio_id": str(portfolio.id),
            "portfolio_name": portfolio.name,
            "base_currency": portfolio.base_currency,
            "as_of_date": as_of_date.isoformat(),
            "total_value": quantize_currency(total_portfolio_value),
            "cash_balance": quantize_currency(cash_balance),
            "holdings_market_value": quantize_currency(total_holdings_market_value),
            "cost_basis": quantize_currency(total_cost_basis),
            "unrealized_pnl": quantize_currency(total_unrealized_pnl),
            "unrealized_pnl_percent": (
                ((total_unrealized_pnl / total_cost_basis) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if total_cost_basis > Decimal("0")
                else Decimal("0.00")
            ),
            "realized_pnl": quantize_currency(total_realized_pnl),
            "total_pnl": quantize_currency(total_pnl),
            "holdings": holdings_list,
            "asset_allocations": asset_allocations,
            "sector_allocations": sector_allocations,
        }

    @classmethod
    def get_historical_equity_curve(
        cls,
        db: Session,
        portfolio: Portfolio,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Reconstructs the daily portfolio valuation series from the first transaction to as_of_date.
        Strictly observes chronological pricing with zero lookahead bias.
        
        Returns:
            List of daily snapshots:
            [{ "date": "YYYY-MM-DD", "total_value": 10500.0, "cash": 500.0, "holdings_value": 10000.0, "net_external_flow": 10000.0 }, ...]
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Fetch all transactions ordered chronologically
        txs = (
            db.query(PortfolioTransaction)
            .filter(
                PortfolioTransaction.portfolio_id == portfolio.id,
                PortfolioTransaction.trade_date <= as_of_date,
            )
            .order_by(
                PortfolioTransaction.trade_date.asc(),
                PortfolioTransaction.created_at.asc(),
            )
            .all()
        )

        if not txs:
            return []

        start_date = txs[0].trade_date
        end_date = as_of_date
        if start_date > end_date:
            return []

        # Find all instruments ever held
        instrument_ids = {tx.instrument_id for tx in txs if tx.instrument_id}

        # Preload price history for these instruments up to as_of_date
        # price_map: inst_id -> (sorted_dates, sorted_prices)
        price_map: Dict[uuid.UUID, Tuple[List[date], List[Decimal]]] = {}
        if instrument_ids:
            all_prices = (
                db.query(PriceHistory)
                .filter(
                    PriceHistory.instrument_id.in_(instrument_ids),
                    PriceHistory.trade_date <= as_of_date,
                )
                .order_by(PriceHistory.trade_date.asc())
                .all()
            )
            temp_prices: Dict[uuid.UUID, Dict[date, Decimal]] = {inst_id: {} for inst_id in instrument_ids}
            for p in all_prices:
                temp_prices[p.instrument_id][p.trade_date] = p.close

            for inst_id, d_map in temp_prices.items():
                s_dates = sorted(d_map.keys())
                s_prices = [d_map[d] for d in s_dates]
                price_map[inst_id] = (s_dates, s_prices)

        # Helper to get latest price on or before day d
        def get_price(inst_id: uuid.UUID, cur_d: date) -> Optional[Decimal]:
            if inst_id not in price_map:
                return None
            s_dates, s_prices = price_map[inst_id]
            idx = bisect_right(s_dates, cur_d) - 1
            if idx >= 0:
                return s_prices[idx]
            return None

        # Group transactions by date
        txs_by_date: Dict[date, List[PortfolioTransaction]] = {}
        for tx in txs:
            txs_by_date.setdefault(tx.trade_date, []).append(tx)

        # Running ledger state
        running_cash = Decimal("0.00")
        running_shares: Dict[uuid.UUID, Decimal] = {}
        running_cost_basis: Dict[uuid.UUID, Decimal] = {}

        timeline: List[Dict[str, Any]] = []

        # Iterate every day from start_date to end_date
        # Note: To avoid excessive points for long timelines, we step day by day
        curr = start_date
        one_day = timedelta(days=1)

        while curr <= end_date:
            net_external_flow = Decimal("0.00")

            # Process day's transactions if any
            if curr in txs_by_date:
                for tx in txs_by_date[curr]:
                    running_cash += tx.cash_amount
                    inst_id = tx.instrument_id

                    if tx.transaction_type == "CASH_DEPOSIT":
                        net_external_flow += (tx.price_per_unit - tx.fees)
                    elif tx.transaction_type == "CASH_WITHDRAWAL":
                        net_external_flow -= (tx.price_per_unit + tx.fees)
                    elif tx.transaction_type == "BUY":
                        if inst_id:
                            running_shares[inst_id] = running_shares.get(inst_id, Decimal("0")) + tx.quantity
                            running_cost_basis[inst_id] = running_cost_basis.get(inst_id, Decimal("0")) + (tx.quantity * tx.price_per_unit + tx.fees)
                    elif tx.transaction_type == "SELL":
                        if inst_id:
                            old_qty = running_shares.get(inst_id, Decimal("0"))
                            old_cost = running_cost_basis.get(inst_id, Decimal("0"))
                            avg_cost = (old_cost / old_qty) if old_qty > Decimal("0") else Decimal("0")
                            new_qty = max(Decimal("0"), old_qty - tx.quantity)
                            running_shares[inst_id] = new_qty
                            running_cost_basis[inst_id] = new_qty * avg_cost

            # Calculate valuation for the day
            holdings_val = Decimal("0.00")
            for inst_id, qty in running_shares.items():
                if qty > Decimal("0"):
                    p = get_price(inst_id, curr)
                    if p is not None:
                        holdings_val += qty * p
                    else:
                        # Fallback to cost basis if market price not yet available
                        holdings_val += running_cost_basis.get(inst_id, Decimal("0"))

            total_val = running_cash + holdings_val

            timeline.append({
                "date": curr.isoformat(),
                "total_value": float(total_val),
                "cash": float(running_cash),
                "holdings_value": float(holdings_val),
                "net_external_flow": float(net_external_flow),
            })

            curr += one_day

        return timeline

    @classmethod
    def calculate_performance_and_risk(
        cls,
        db: Session,
        portfolio: Portfolio,
        as_of_date: Optional[date] = None,
        risk_free_rate: Decimal = DEFAULT_RISK_FREE_RATE,
    ) -> Dict[str, Any]:
        """
        Calculates:
        - Time-Weighted Return (TWR)
        - Money-Weighted Return / XIRR
        - Annualized Volatility
        - Sharpe Ratio
        - Maximum Drawdown
        """
        if as_of_date is None:
            as_of_date = date.today()

        timeline = cls.get_historical_equity_curve(db, portfolio, as_of_date)
        if not timeline:
            return {
                "twr_percent": None,
                "xirr_percent": None,
                "annualized_volatility_percent": None,
                "sharpe_ratio": None,
                "max_drawdown_percent": 0.0,
                "risk_free_rate_percent": float(risk_free_rate * Decimal("100")),
                "timeline_days": 0,
            }

        # 1. TWR Calculation (End-of-day convention)
        # R_k = (V_k - C_k - V_{k-1}) / V_{k-1}
        daily_returns: List[float] = []
        cumulative_twr_factor = 1.0

        for i in range(1, len(timeline)):
            v_prev = timeline[i - 1]["total_value"]
            v_curr = timeline[i]["total_value"]
            c_curr = timeline[i]["net_external_flow"]

            if v_prev > 1e-4:
                # Return on capital present prior to today's external cash flow
                r_k = (v_curr - c_curr - v_prev) / v_prev
                daily_returns.append(r_k)
                cumulative_twr_factor *= (1.0 + r_k)
            else:
                daily_returns.append(0.0)

        twr_percent = round((cumulative_twr_factor - 1.0) * 100.0, 2)

        # 2. XIRR Calculation
        txs = (
            db.query(PortfolioTransaction)
            .filter(
                PortfolioTransaction.portfolio_id == portfolio.id,
                PortfolioTransaction.trade_date <= as_of_date,
            )
            .order_by(PortfolioTransaction.trade_date.asc())
            .all()
        )

        cash_flows: List[Tuple[date, Decimal]] = []
        for tx in txs:
            if tx.transaction_type == "CASH_DEPOSIT":
                # Investor gave cash to portfolio => negative cash flow
                deposit_amt = tx.price_per_unit - tx.fees
                cash_flows.append((tx.trade_date, -deposit_amt))
            elif tx.transaction_type == "CASH_WITHDRAWAL":
                # Investor withdrew cash from portfolio => positive cash flow
                withdraw_amt = tx.price_per_unit + tx.fees
                cash_flows.append((tx.trade_date, withdraw_amt))

        # Terminal valuation at as_of_date => positive cash flow
        terminal_value = Decimal(str(timeline[-1]["total_value"]))
        if terminal_value > Decimal("0"):
            cash_flows.append((as_of_date, terminal_value))

        xirr_result = calculate_xirr(cash_flows)
        xirr_percent = float(xirr_result) if xirr_result is not None else None

        # 3. Maximum Drawdown
        # DD_t = (Peak_t - V_t) / Peak_t
        peak = 0.0
        max_dd = 0.0
        for pt in timeline:
            val = pt["total_value"]
            if val > peak:
                peak = val
            if peak > 0:
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd

        max_drawdown_percent = round(max_dd * 100.0, 2)

        # 4. Annualized Volatility
        # sigma_annual = stdev(daily_returns) * sqrt(252)
        annualized_volatility_percent: Optional[float] = None
        sharpe_ratio: Optional[float] = None

        if len(daily_returns) >= 2:
            mean_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            daily_vol = math.sqrt(variance)
            annual_vol = daily_vol * math.sqrt(252)
            annualized_volatility_percent = round(annual_vol * 100.0, 2)

            # 5. Sharpe Ratio
            # (Annualized Return - Rf) / Annualized Volatility
            # Annualized Return from TWR over N days
            days = len(timeline)
            if days > 1 and annual_vol > 1e-6:
                try:
                    # Annualized compound return
                    ann_factor = 365.0 / days
                    ann_return = ((1.0 + (twr_percent / 100.0)) ** ann_factor) - 1.0
                    rf = float(risk_free_rate)
                    sharpe = (ann_return - rf) / annual_vol
                    sharpe_ratio = round(sharpe, 2)
                except (OverflowError, ValueError):
                    sharpe_ratio = None

        return {
            "twr_percent": twr_percent,
            "xirr_percent": xirr_percent,
            "annualized_volatility_percent": annualized_volatility_percent,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_percent": max_drawdown_percent,
            "risk_free_rate_percent": float(risk_free_rate * Decimal("100")),
            "timeline_days": len(timeline),
        }
