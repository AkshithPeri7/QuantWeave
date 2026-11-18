"""
Deterministic Strategy Simulation and Backtesting Engine for QuantLab.

Guarantees:
- Chronological bar processing without look-ahead bias
- Next-bar execution at Open price with modeled fees and slippage
- Strictly long-only equity accounting (no negative cash, no unauthorized shorting)
- Bounded parameter grid search with in-sample / out-of-sample splits
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import itertools
import math
from typing import Any, Dict, List, Optional, Tuple, Type
import numpy as np
import pandas as pd

from app.analytics.quant_metrics import calculate_backtest_metrics


# ==========================================
# 1. Base Strategy Interface & Strategies
# ==========================================


class BaseStrategy(ABC):
    """Abstract quantitative strategy."""

    strategy_type: str = "BASE"

    @classmethod
    @abstractmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validates parameter types, bounds, and mutual consistency."""
        pass

    @classmethod
    @abstractmethod
    def generate_signals(cls, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """
        Generates trading signals ('BUY', 'SELL', 'HOLD') for each bar chronologically.
        Signal at index t MUST depend strictly on data available up to row t.
        """
        pass


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy:
    - BUY when fast SMA crosses above slow SMA (golden cross).
    - SELL when fast SMA crosses below slow SMA (death cross).
    """

    strategy_type = "SMA_CROSSOVER"

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        fast = int(params.get("fast_period", 20))
        slow = int(params.get("slow_period", 50))
        if fast < 2 or fast > 500:
            raise ValueError(f"fast_period must be between 2 and 500. Got {fast}")
        if slow < 3 or slow > 1000:
            raise ValueError(f"slow_period must be between 3 and 1000. Got {slow}")
        if fast >= slow:
            raise ValueError(f"fast_period ({fast}) must be strictly less than slow_period ({slow})")
        return {"fast_period": fast, "slow_period": slow}

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        p = cls.validate_parameters(params)
        fast = p["fast_period"]
        slow = p["slow_period"]

        close = df["close"].astype(float)
        sma_fast = close.rolling(window=fast).mean()
        sma_slow = close.rolling(window=slow).mean()

        signals = pd.Series("HOLD", index=df.index)

        # Cross above: fast was <= slow on previous bar, now > slow on current bar
        cross_above = (sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))
        # Cross below: fast was >= slow on previous bar, now < slow on current bar
        cross_below = (sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))

        signals[cross_above] = "BUY"
        signals[cross_below] = "SELL"
        return signals


class EMACrossoverStrategy(BaseStrategy):
    """
    Exponential Moving Average Crossover Strategy:
    - Faster response than SMA with exponential recency weighting.
    - BUY when fast EMA crosses above slow EMA.
    - SELL when fast EMA crosses below slow EMA.
    """

    strategy_type = "EMA_CROSSOVER"

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        fast = int(params.get("fast_period", 12))
        slow = int(params.get("slow_period", 26))
        if fast < 2 or fast > 500:
            raise ValueError(f"fast_period must be between 2 and 500. Got {fast}")
        if slow < 3 or slow > 1000:
            raise ValueError(f"slow_period must be between 3 and 1000. Got {slow}")
        if fast >= slow:
            raise ValueError(f"fast_period ({fast}) must be strictly less than slow_period ({slow})")
        return {"fast_period": fast, "slow_period": slow}

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        p = cls.validate_parameters(params)
        fast = p["fast_period"]
        slow = p["slow_period"]

        close = df["close"].astype(float)
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()

        signals = pd.Series("HOLD", index=df.index)

        cross_above = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        cross_below = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

        signals[cross_above] = "BUY"
        signals[cross_below] = "SELL"
        return signals


class RSIThresholdStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) Threshold Strategy:
    - BUY when RSI crosses above the oversold boundary (recovery from oversold conditions).
    - SELL when RSI crosses above the overbought boundary (taking profits on overextended rallies).
    """

    strategy_type = "RSI_THRESHOLD"

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        period = int(params.get("rsi_period", 14))
        oversold = float(params.get("oversold_threshold", 30.0))
        overbought = float(params.get("overbought_threshold", 70.0))

        if period < 2 or period > 100:
            raise ValueError(f"rsi_period must be between 2 and 100. Got {period}")
        if oversold <= 0 or oversold >= 100:
            raise ValueError(f"oversold_threshold must be between 0 and 100. Got {oversold}")
        if overbought <= 0 or overbought >= 100:
            raise ValueError(f"overbought_threshold must be between 0 and 100. Got {overbought}")
        if oversold >= overbought:
            raise ValueError(f"oversold_threshold ({oversold}) must be less than overbought_threshold ({overbought})")

        return {
            "rsi_period": period,
            "oversold_threshold": oversold,
            "overbought_threshold": overbought,
        }

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        p = cls.validate_parameters(params)
        period = p["rsi_period"]
        oversold = p["oversold_threshold"]
        overbought = p["overbought_threshold"]

        close = df["close"].astype(float)
        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi = rsi.fillna(50.0)

        signals = pd.Series("HOLD", index=df.index)

        # Buy condition: crosses above oversold or drops below oversold
        buy_cond = (rsi < oversold) & (rsi.shift(1) >= oversold) | ((rsi >= oversold) & (rsi.shift(1) < oversold))
        # Sell condition: crosses above overbought
        sell_cond = (rsi > overbought) & (rsi.shift(1) <= overbought)

        signals[buy_cond] = "BUY"
        signals[sell_cond] = "SELL"
        return signals


class BuyAndHoldStrategy(BaseStrategy):
    """Benchmark strategy: Buys on the very first bar and holds through the backtest."""

    strategy_type = "BUY_AND_HOLD"

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        signals = pd.Series("HOLD", index=df.index)
        if len(signals) > 0:
            signals.iloc[0] = "BUY"
        return signals


STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {
    "SMA_CROSSOVER": SMACrossoverStrategy,
    "EMA_CROSSOVER": EMACrossoverStrategy,
    "RSI_THRESHOLD": RSIThresholdStrategy,
    "BUY_AND_HOLD": BuyAndHoldStrategy,
}


# ==========================================
# 2. Chronological Backtesting Execution Engine
# ==========================================


def _as_date(d: Any) -> date:
    if isinstance(d, date):
        return d
    if hasattr(d, "date") and callable(getattr(d, "date")):
        return d.date()
    if isinstance(d, str):
        from datetime import datetime
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    return pd.to_datetime(d).date()


class BacktestEngine:
    """
    Deterministic chronological execution simulator.
    Simulates long-only equity trading with realistic fees and slippage.
    """

    @classmethod
    def run_backtest(
        cls,
        df: pd.DataFrame,
        strategy_class: Optional[Type[BaseStrategy]] = None,
        params: Optional[Dict[str, Any]] = None,
        starting_capital: float = 100000.0,
        fee_rate: float = 0.0010,  # 0.10% transaction fee per trade
        slippage_bps: float = 5.0,  # 5 bps = 0.05% execution slippage
        strategy_cls: Optional[Type[BaseStrategy]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a backtest on chronological DataFrame `df`.
        Columns required: ['trade_date', 'open', 'high', 'low', 'close', 'volume'].
        """
        strat_class = strategy_class or strategy_cls
        if strat_class is None:
            raise ValueError("strategy_class (or strategy_cls) is required.")
        strat_params = params if params is not None else (parameters if parameters is not None else {})
        if df.empty or len(df) < 2:
            raise ValueError("Insufficient historical bars for backtesting (minimum 2 bars required).")

        # Ensure sorted chronologically
        df = df.sort_values("trade_date").reset_index(drop=True).copy()

        # Generate signals strictly on bar close
        signals = strat_class.generate_signals(df, strat_params)

        slippage_rate = slippage_bps / 10000.0  # e.g. 5 bps -> 0.0005

        cash = float(starting_capital)
        position = 0.0  # shares held
        avg_entry_price = 0.0
        peak_equity = float(starting_capital)

        trades: List[Dict[str, Any]] = []
        equity_series: List[Dict[str, Any]] = []

        first_close = float(df.iloc[0]["close"])

        # Iterate bar by bar
        # Order generated at end of bar i-1 executes at bar i's Open
        pending_signal: Optional[str] = None
        pending_signal_date: Optional[date] = None

        for i in range(len(df)):
            current_bar = df.iloc[i]
            bar_date = _as_date(current_bar["trade_date"])
            open_price = float(current_bar["open"])
            close_price = float(current_bar["close"])

            # 1. Execute pending signal from previous bar's close
            if pending_signal == "BUY" and cash > 10.0 and position == 0.0:
                exec_price = open_price * (1.0 + slippage_rate)
                # Max whole shares we can buy including fee
                effective_price = exec_price * (1.0 + fee_rate)
                shares_to_buy = math.floor(cash / effective_price)

                if shares_to_buy > 0:
                    gross_cost = shares_to_buy * exec_price
                    fee = gross_cost * fee_rate
                    total_outlay = gross_cost + fee
                    slippage_cost = shares_to_buy * (exec_price - open_price)

                    cash -= total_outlay
                    position = float(shares_to_buy)
                    avg_entry_price = exec_price

                    trades.append({
                        "side": "BUY",
                        "signal_date": pending_signal_date,
                        "execution_date": bar_date,
                        "quantity": shares_to_buy,
                        "execution_price": round(exec_price, 4),
                        "fees": round(fee, 2),
                        "slippage_cost": round(slippage_cost, 2),
                        "cash_after": round(cash, 2),
                        "position_after": position,
                        "realized_pnl": None,
                        "pnl_pct": None,
                    })

            elif pending_signal == "SELL" and position > 0.0:
                exec_price = open_price * (1.0 - slippage_rate)
                gross_proceeds = position * exec_price
                fee = gross_proceeds * fee_rate
                net_proceeds = gross_proceeds - fee
                slippage_cost = position * (open_price - exec_price)

                cost_basis = position * avg_entry_price
                realized_pnl = net_proceeds - cost_basis
                pnl_pct = (realized_pnl / cost_basis) * 100.0 if cost_basis > 0 else 0.0

                cash += net_proceeds

                trades.append({
                    "side": "SELL",
                    "signal_date": pending_signal_date,
                    "execution_date": bar_date,
                    "quantity": position,
                    "execution_price": round(exec_price, 4),
                    "fees": round(fee, 2),
                    "slippage_cost": round(slippage_cost, 2),
                    "cash_after": round(cash, 2),
                    "position_after": 0.0,
                    "realized_pnl": round(realized_pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                })

                position = 0.0
                avg_entry_price = 0.0

            # 2. Record End-of-Day Equity Point
            pos_value = position * close_price
            day_equity = cash + pos_value
            peak_equity = max(peak_equity, day_equity)
            drawdown_pct = ((peak_equity - day_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0

            # Benchmark Buy-and-Hold comparison
            bench_equity = starting_capital * (close_price / first_close) if first_close > 0 else starting_capital

            equity_series.append({
                "point_date": bar_date,
                "equity": round(day_equity, 2),
                "cash": round(cash, 2),
                "position_value": round(pos_value, 2),
                "drawdown_pct": round(drawdown_pct, 2),
                "benchmark_equity": round(bench_equity, 2),
            })

            # 3. Read signal generated on bar close for execution on NEXT bar
            raw_sig = str(signals.iloc[i])
            if raw_sig in ["BUY", "SELL"]:
                pending_signal = raw_sig
                pending_signal_date = bar_date
            else:
                pending_signal = None
                pending_signal_date = None

        # Calculate final metrics
        metrics = calculate_backtest_metrics(
            equity_series=equity_series,
            trades=trades,
            starting_capital=starting_capital,
        )

        return {
            "metrics": metrics,
            "trades": trades,
            "equity_curve": equity_series,
        }


# ==========================================
# 3. Bounded Parameter Grid Search
# ==========================================


def run_parameter_grid_search(
    df: pd.DataFrame,
    strategy_type: Optional[str] = None,
    param_ranges: Optional[Dict[str, List[Any]]] = None,
    starting_capital: float = 100000.0,
    fee_rate: float = 0.0010,
    slippage_bps: float = 5.0,
    train_ratio: float = 0.70,
    max_combinations: int = 25,
    strategy_cls: Optional[Any] = None,
    param_grid: Optional[Dict[str, List[Any]]] = None,
) -> Dict[str, Any]:
    """
    Runs bounded parameter grid search with in-sample / out-of-sample split.
    Prevents unbounded combinatorial explosion by capping combinations at `max_combinations`.
    """
    st_type = strategy_type
    if st_type is None and strategy_cls is not None:
        if isinstance(strategy_cls, str):
            st_type = strategy_cls
        elif hasattr(strategy_cls, "strategy_type"):
            st_type = strategy_cls.strategy_type

    if not st_type or st_type not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy type '{st_type}'.")

    grid = param_ranges if param_ranges is not None else (param_grid if param_grid is not None else {})

    # Generate parameter combinations
    keys = list(grid.keys())
    values = list(grid.values())
    combinations = [dict(zip(keys, prod)) for prod in itertools.product(*values)]

    if len(combinations) > max_combinations:
        raise ValueError(
            f"Requested {len(combinations)} combinations exceeds maximum allowed limit of {max_combinations}."
        )

    # In-Sample vs Out-of-Sample Split
    total_len = len(df)
    train_len = int(total_len * train_ratio)

    df_train = df.iloc[:train_len].copy()
    df_test = df.iloc[train_len:].copy()

    results: List[Dict[str, Any]] = []

    for params in combinations:
        try:
            validated_p = strategy_cls.validate_parameters(params)
        except ValueError:
            continue

        # In-sample backtest
        train_res = BacktestEngine.run_backtest(
            df_train,
            strategy_cls,
            validated_p,
            starting_capital=starting_capital,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
        )

        # Out-of-sample backtest
        test_res = BacktestEngine.run_backtest(
            df_test,
            strategy_cls,
            validated_p,
            starting_capital=starting_capital,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
        )

        train_ret = train_res["metrics"]["total_return_pct"]
        test_ret = test_res["metrics"]["total_return_pct"]
        train_sharpe = train_res["metrics"]["sharpe_ratio"]
        test_sharpe = test_res["metrics"]["sharpe_ratio"]
        is_overfit = (train_ret > 5.0 and test_ret < -5.0) or (train_sharpe is not None and test_sharpe is not None and train_sharpe > 1.0 and test_sharpe < 0)

        results.append({
            "params": validated_p,
            "parameters": validated_p,
            "train_metrics": train_res["metrics"],
            "test_metrics": test_res["metrics"],
            "in_sample_return_pct": train_ret,
            "out_of_sample_return_pct": test_ret,
            "total_return_train_pct": train_ret,
            "total_return_test_pct": test_ret,
            "in_sample_sharpe": train_sharpe,
            "out_of_sample_sharpe": test_sharpe,
            "sharpe_train": train_sharpe,
            "sharpe_test": test_sharpe,
            "in_sample_max_dd_pct": train_res["metrics"]["max_drawdown_pct"],
            "out_of_sample_max_dd_pct": test_res["metrics"]["max_drawdown_pct"],
            "max_drawdown_train_pct": train_res["metrics"]["max_drawdown_pct"],
            "max_drawdown_test_pct": test_res["metrics"]["max_drawdown_pct"],
            "win_rate_test_pct": test_res["metrics"]["win_rate_pct"],
            "overfitting_warning": is_overfit,
            "status": "COMPLETED",
            "error_message": None,
        })

    # Sort results by out-of-sample Sharpe or return
    results.sort(
        key=lambda r: (r["sharpe_test"] if r["sharpe_test"] is not None else -99.0, r["total_return_test_pct"]),
        reverse=True,
    )

    return {
        "strategy_type": st_type,
        "combinations_tested": len(results),
        "total_combinations_tested": len(results),
        "train_bars": len(df_train),
        "test_bars": len(df_test),
        "train_period": f"{df_train.iloc[0]['trade_date']} to {df_train.iloc[-1]['trade_date']}",
        "test_period": f"{df_test.iloc[0]['trade_date']} to {df_test.iloc[-1]['trade_date']}",
        "results": results,
        "best_params": results[0]["params"] if results else None,
        "summary": f"Tested {len(results)} parameter combinations across {len(df_train)} in-sample bars and {len(df_test)} out-of-sample bars.",
        "overfitting_warning": "High in-sample returns accompanied by declining out-of-sample metrics indicate curve-fitting. Past simulated performance does not guarantee future results.",
    }
