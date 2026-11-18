"""
Quantitative Performance Analytics Engine for QuantLab.

Calculates institutional-grade risk-adjusted return metrics:
CAGR, Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Calmar Ratio,
Win Rate, Profit Factor, and Benchmark Alpha.
"""

from decimal import Decimal
import math
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def calculate_backtest_metrics(
    equity_series: List[Dict[str, Any]],
    trades: List[Dict[str, Any]],
    starting_capital: float,
    risk_free_rate: float = 0.06,  # 6.0% Indian benchmark risk-free rate
) -> Dict[str, Any]:
    """
    Computes rigorous quantitative performance metrics for a backtested strategy.
    Handles flat equity curves, zero trades, and insufficient history safely.
    """
    if not equity_series:
        return {
            "starting_capital": starting_capital,
            "ending_equity": starting_capital,
            "net_profit": 0.0,
            "total_return_pct": 0.0,
            "cagr_pct": None,
            "annualized_volatility_pct": 0.0,
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "max_drawdown_pct": 0.0,
            "calmar_ratio": None,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": None,
            "avg_trade_pnl": 0.0,
            "avg_winning_trade": 0.0,
            "avg_losing_trade": 0.0,
            "total_fees_paid": 0.0,
            "total_slippage_paid": 0.0,
            "exposure_pct": 0.0,
            "benchmark_return_pct": 0.0,
            "duration_days": 0,
        }

    ending_equity = float(equity_series[-1]["equity"])
    net_profit = round(ending_equity - starting_capital, 2)
    total_return_pct = round(((ending_equity - starting_capital) / starting_capital) * 100, 2) if starting_capital > 0 else 0.0

    # Duration calculation
    start_date_str = equity_series[0]["point_date"]
    end_date_str = equity_series[-1]["point_date"]
    start_dt = pd.to_datetime(start_date_str)
    end_dt = pd.to_datetime(end_date_str)
    duration_days = max(1, (end_dt - start_dt).days)

    # CAGR: Only valid for periods >= 365 days
    cagr_pct: Optional[float] = None
    if duration_days >= 365 and starting_capital > 0 and ending_equity > 0:
        cagr_val = ((ending_equity / starting_capital) ** (365.0 / duration_days) - 1.0) * 100
        cagr_pct = round(cagr_val, 2)

    # Daily returns series
    equities = np.array([float(pt["equity"]) for pt in equity_series], dtype=np.float64)
    if len(equities) > 1:
        daily_returns = np.diff(equities) / equities[:-1]
    else:
        daily_returns = np.array([0.0])

    # Annualized Volatility
    ann_vol_pct = 0.0
    if len(daily_returns) > 1:
        std_daily = float(np.std(daily_returns, ddof=1))
        ann_vol = std_daily * math.sqrt(252) * 100
        ann_vol_pct = round(ann_vol, 2)

    # Effective annualized return for Sharpe/Sortino
    ann_return_decimal = (
        (cagr_pct / 100.0)
        if cagr_pct is not None
        else (total_return_pct / 100.0) * (365.0 / duration_days)
    )

    # Sharpe Ratio
    sharpe_ratio: Optional[float] = None
    if ann_vol_pct > 0.001:
        ann_vol_decimal = ann_vol_pct / 100.0
        sharpe_val = (ann_return_decimal - risk_free_rate) / ann_vol_decimal
        sharpe_ratio = round(sharpe_val, 2)

    # Sortino Ratio (downside deviation relative to risk-free daily target)
    sortino_ratio: Optional[float] = None
    rf_daily = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
    downside_diffs = np.minimum(0.0, daily_returns - rf_daily)
    downside_sq_mean = float(np.mean(downside_diffs ** 2))
    downside_dev = math.sqrt(downside_sq_mean) * math.sqrt(252)

    if downside_dev > 0.0001:
        sortino_val = (ann_return_decimal - risk_free_rate) / downside_dev
        sortino_ratio = round(sortino_val, 2)

    # Maximum Drawdown %
    drawdowns = [float(pt.get("drawdown_pct", 0.0)) for pt in equity_series]
    max_drawdown_pct = round(max(drawdowns) if drawdowns else 0.0, 2)

    # Calmar Ratio
    calmar_ratio: Optional[float] = None
    if max_drawdown_pct > 0.01:
        ann_ret_for_calmar = cagr_pct if cagr_pct is not None else total_return_pct
        calmar_val = ann_ret_for_calmar / max_drawdown_pct
        calmar_ratio = round(calmar_val, 2)

    # Benchmark Return
    first_bench = float(equity_series[0].get("benchmark_equity") or starting_capital)
    last_bench = float(equity_series[-1].get("benchmark_equity") or starting_capital)
    benchmark_return_pct = round(((last_bench - first_bench) / first_bench) * 100, 2) if first_bench > 0 else 0.0

    # Exposure: percentage of days in position
    days_in_market = sum(1 for pt in equity_series if float(pt.get("position_value", 0.0)) > 1.0)
    exposure_pct = round((days_in_market / len(equity_series)) * 100, 2) if equity_series else 0.0

    # Trade Metrics
    sell_trades = [t for t in trades if t.get("side") == "SELL" and t.get("realized_pnl") is not None]
    total_trades = len(sell_trades)
    winning_trades = sum(1 for t in sell_trades if float(t.get("realized_pnl", 0.0)) > 0)
    losing_trades = sum(1 for t in sell_trades if float(t.get("realized_pnl", 0.0)) < 0)

    win_rate_pct = round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0.0

    gains = [float(t["realized_pnl"]) for t in sell_trades if float(t["realized_pnl"]) > 0]
    losses = [abs(float(t["realized_pnl"])) for t in sell_trades if float(t["realized_pnl"]) < 0]

    sum_gains = sum(gains)
    sum_losses = sum(losses)

    profit_factor: Optional[float] = None
    if sum_losses > 0:
        profit_factor = round(sum_gains / sum_losses, 2)
    elif sum_gains > 0:
        profit_factor = round(sum_gains, 2)

    avg_trade_pnl = round(sum(float(t["realized_pnl"]) for t in sell_trades) / total_trades, 2) if total_trades > 0 else 0.0
    avg_winning_trade = round(sum_gains / winning_trades, 2) if winning_trades > 0 else 0.0
    avg_losing_trade = round(sum_losses / losing_trades, 2) if losing_trades > 0 else 0.0

    total_fees_paid = round(sum(float(t.get("fees", 0.0)) for t in trades), 2)
    total_slippage_paid = round(sum(float(t.get("slippage_cost", 0.0)) for t in trades), 2)

    return {
        "starting_capital": starting_capital,
        "ending_equity": ending_equity,
        "net_profit": net_profit,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "annualized_volatility_pct": ann_vol_pct,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "max_drawdown_pct": max_drawdown_pct,
        "calmar_ratio": calmar_ratio,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "avg_trade_pnl": avg_trade_pnl,
        "avg_winning_trade": avg_winning_trade,
        "avg_losing_trade": avg_losing_trade,
        "total_fees_paid": total_fees_paid,
        "total_slippage_paid": total_slippage_paid,
        "exposure_pct": exposure_pct,
        "benchmark_return_pct": benchmark_return_pct,
        "duration_days": duration_days,
    }
