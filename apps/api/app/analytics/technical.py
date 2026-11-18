"""
Technical Analysis Indicators Engine for QuantWeave.

Implements pure, deterministic, and independently testable indicator calculations:
- SMA 20, 50, 200
- EMA 12, 26
- RSI 14 (J. Welles Wilder Jr. smoothing convention: alpha = 1 / period)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2.0)

All calculations operate on chronologically ordered daily bars (oldest to newest).
Look-ahead bias is strictly prevented: indicator values before window periods are None.
Zero-division and flat-price edge cases are handled safely without exceptions.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class IndicatorPoint:
    trade_date: str
    close: float
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_bandwidth: Optional[float] = None
    bb_percent_b: Optional[float] = None


@dataclass
class TechnicalSummary:
    trend: str  # "Bullish", "Bearish", "Neutral"
    trend_description: str
    rsi_state: str  # "Overbought", "Oversold", "Neutral"
    rsi_value: Optional[float]
    macd_state: str  # "Bullish Crossover", "Bearish Crossover", "Bullish", "Bearish", "Neutral"
    macd_histogram: Optional[float]
    bb_state: str  # "Upper Band Breakout", "Lower Band Breakout", "Band Squeeze", "Normal"
    golden_cross: Optional[bool]  # SMA 50 > SMA 200


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """
    Calculates Simple Moving Average over `window` periods.
    Returns NaN for the first `window - 1` periods.
    """
    if window <= 0:
        raise ValueError(f"SMA window must be positive, got {window}")
    return series.rolling(window=window, min_periods=window).mean()


def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """
    Calculates Exponential Moving Average with smoothing factor alpha = 2 / (span + 1).
    Initial value is the SMA of the first `span` periods.
    Returns NaN for the first `span - 1` periods.
    """
    if span <= 0:
        raise ValueError(f"EMA span must be positive, got {span}")
    if len(series) < span:
        return pd.Series(np.nan, index=series.index, dtype=float)

    # Standard pandas ewm with adjust=False matches the textbook recursion:
    # EMA_t = alpha * Price_t + (1 - alpha) * EMA_{t-1}
    ema = series.ewm(span=span, adjust=False, min_periods=span).mean()
    # Ensure values strictly before `span` observations are NaN
    ema.iloc[: span - 1] = np.nan
    return ema


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI) using J. Welles Wilder Jr.'s smoothing convention (1978).
    
    Methodology:
    1. delta = Close_t - Close_{t-1}
    2. Gain = max(delta, 0), Loss = max(-delta, 0)
    3. Initial average gain/loss at t=period is the arithmetic mean of the first `period` gains/losses.
    4. Subsequent average gain/loss uses Wilder's recursive smoothing (alpha = 1 / period):
       AvgGain_t = (AvgGain_{t-1} * (period - 1) + Gain_t) / period
       AvgLoss_t = (AvgLoss_{t-1} * (period - 1) + Loss_t) / period
    5. RS = AvgGain / AvgLoss
    6. RSI = 100 - (100 / (1 + RS))
    
    Edge cases:
    - If AvgLoss == 0 and AvgGain == 0: RSI = 50.0 (completely flat price)
    - If AvgLoss == 0 and AvgGain > 0: RSI = 100.0 (strictly positive price changes)
    - Returns NaN for the first `period` observations.
    """
    if period <= 0:
        raise ValueError(f"RSI period must be positive, got {period}")

    n = len(series)
    rsi_series = pd.Series(np.nan, index=series.index, dtype=float)

    if n <= period:
        return rsi_series

    # Convert to float numpy array for exact deterministic recursion
    prices = series.to_numpy(dtype=float)
    deltas = np.diff(prices)

    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # Initial average over the first `period` changes (indices 0 to period - 1 in deltas, which corresponds to prices up to index period)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    # First RSI value occurs at price index `period`
    if avg_loss == 0.0:
        rsi_series.iloc[period] = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi_series.iloc[period] = 100.0 - (100.0 / (1.0 + rs))

    # Wilder recursive smoothing for remaining periods
    for i in range(period, len(deltas)):
        price_idx = i + 1
        gain = gains[i]
        loss = losses[i]

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0.0:
            rsi_series.iloc[price_idx] = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi_series.iloc[price_idx] = 100.0 - (100.0 / (1.0 + rs))

    return rsi_series


def calculate_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Moving Average Convergence Divergence (MACD).
    
    Formula:
    - MACD Line = EMA(fast) - EMA(slow)
    - Signal Line = EMA(signal) of MACD Line
    - MACD Histogram = MACD Line - Signal Line
    
    Returns:
    (macd_line, signal_line, histogram)
    """
    if fast >= slow:
        raise ValueError(f"Fast period ({fast}) must be less than slow period ({slow})")

    ema_fast = calculate_ema(series, span=fast)
    ema_slow = calculate_ema(series, span=slow)

    macd_line = ema_fast - ema_slow

    # The signal line is the 9-period EMA of the valid MACD line
    # Drop initial NaNs for EMA calculation, then align back to original index
    valid_macd = macd_line.dropna()
    if len(valid_macd) >= signal:
        signal_line_valid = valid_macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
        signal_line = signal_line_valid.reindex(series.index)
        signal_line.iloc[: slow + signal - 2] = np.nan
    else:
        signal_line = pd.Series(np.nan, index=series.index, dtype=float)

    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Calculates Bollinger Bands:
    - Middle Band = SMA(window)
    - Upper Band = Middle Band + num_std * std_dev
    - Lower Band = Middle Band - num_std * std_dev
    - Bandwidth = ((Upper - Lower) / Middle) * 100
    - %B = (Close - Lower) / (Upper - Lower)
    
    Returns:
    (upper, middle, lower, bandwidth, percent_b)
    """
    if window <= 0:
        raise ValueError(f"Bollinger window must be positive, got {window}")

    middle = calculate_sma(series, window=window)
    # Use population standard deviation (ddof=0) standard in TA systems
    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=0)

    upper = middle + (num_std * rolling_std)
    lower = middle - (num_std * rolling_std)

    # Bandwidth with zero-division guard
    bandwidth = pd.Series(np.nan, index=series.index, dtype=float)
    valid_mid = (middle != 0.0) & middle.notna()
    bandwidth[valid_mid] = ((upper[valid_mid] - lower[valid_mid]) / middle[valid_mid]) * 100.0

    # %B with zero-division guard
    percent_b = pd.Series(np.nan, index=series.index, dtype=float)
    band_range = upper - lower
    valid_range = (band_range != 0.0) & band_range.notna()
    percent_b[valid_range] = (series[valid_range] - lower[valid_range]) / band_range[valid_range]
    # When range is 0 (flat price exactly equal to upper/lower), %B is centered at 0.5
    zero_range = (band_range == 0.0) & upper.notna()
    percent_b[zero_range] = 0.5

    return upper, middle, lower, bandwidth, percent_b


def calculate_all_technicals(
    price_bars: List[Any],
) -> Tuple[List[IndicatorPoint], TechnicalSummary]:
    """
    Processes a list of price records (with trade_date and close attributes)
    and computes the full technical analysis suite.
    """
    if not price_bars:
        empty_summary = TechnicalSummary(
            trend="Neutral",
            trend_description="Insufficient data for technical analysis.",
            rsi_state="Neutral",
            rsi_value=None,
            macd_state="Neutral",
            macd_histogram=None,
            bb_state="Normal",
            golden_cross=None,
        )
        return [], empty_summary

    # Ensure chronological sort ascending
    sorted_bars = sorted(price_bars, key=lambda b: getattr(b, "trade_date"))

    dates = [str(getattr(b, "trade_date")) for b in sorted_bars]
    closes = [float(getattr(b, "close")) for b in sorted_bars]
    close_series = pd.Series(closes)

    # Calculate indicators
    sma_20 = calculate_sma(close_series, 20)
    sma_50 = calculate_sma(close_series, 50)
    sma_200 = calculate_sma(close_series, 200)

    ema_12 = calculate_ema(close_series, 12)
    ema_26 = calculate_ema(close_series, 26)

    rsi_14 = calculate_rsi(close_series, 14)

    macd_line, macd_signal, macd_hist = calculate_macd(close_series, 12, 26, 9)

    bb_upper, bb_mid, bb_lower, bb_bw, bb_pb = calculate_bollinger_bands(close_series, 20, 2.0)

    # Build indicator points
    points: List[IndicatorPoint] = []
    for i in range(len(sorted_bars)):
        def clean_val(val: Any) -> Optional[float]:
            if pd.isna(val) or np.isnan(val):
                return None
            return round(float(val), 4)

        points.append(
            IndicatorPoint(
                trade_date=dates[i],
                close=round(closes[i], 4),
                sma_20=clean_val(sma_20.iloc[i]),
                sma_50=clean_val(sma_50.iloc[i]),
                sma_200=clean_val(sma_200.iloc[i]),
                ema_12=clean_val(ema_12.iloc[i]),
                ema_26=clean_val(ema_26.iloc[i]),
                rsi_14=clean_val(rsi_14.iloc[i]),
                macd_line=clean_val(macd_line.iloc[i]),
                macd_signal=clean_val(macd_signal.iloc[i]),
                macd_hist=clean_val(macd_hist.iloc[i]),
                bb_upper=clean_val(bb_upper.iloc[i]),
                bb_middle=clean_val(bb_mid.iloc[i]),
                bb_lower=clean_val(bb_lower.iloc[i]),
                bb_bandwidth=clean_val(bb_bw.iloc[i]),
                bb_percent_b=clean_val(bb_pb.iloc[i]),
            )
        )

    # Generate summary based on latest available metrics
    latest_close = closes[-1]
    latest_sma20 = clean_val(sma_20.iloc[-1])
    latest_sma50 = clean_val(sma_50.iloc[-1])
    latest_sma200 = clean_val(sma_200.iloc[-1])
    latest_rsi = clean_val(rsi_14.iloc[-1])
    latest_macd = clean_val(macd_line.iloc[-1])
    latest_signal = clean_val(macd_signal.iloc[-1])
    latest_hist = clean_val(macd_hist.iloc[-1])
    prev_hist = clean_val(macd_hist.iloc[-2]) if len(sorted_bars) > 1 else None
    latest_bb_upper = clean_val(bb_upper.iloc[-1])
    latest_bb_lower = clean_val(bb_lower.iloc[-1])

    # Trend logic
    bullish_signals = 0
    bearish_signals = 0

    if latest_sma50 is not None:
        if latest_close > latest_sma50:
            bullish_signals += 1
        else:
            bearish_signals += 1

    if latest_sma200 is not None:
        if latest_close > latest_sma200:
            bullish_signals += 1
        else:
            bearish_signals += 1

    if latest_sma20 is not None and latest_sma50 is not None:
        if latest_sma20 > latest_sma50:
            bullish_signals += 1
        else:
            bearish_signals += 1

    if bullish_signals >= 2:
        trend = "Bullish"
        trend_desc = "Price is trading above key moving averages with upward momentum."
    elif bearish_signals >= 2:
        trend = "Bearish"
        trend_desc = "Price is trading below key moving averages with downward pressure."
    else:
        trend = "Neutral"
        trend_desc = "Price is consolidating near primary moving averages."

    # RSI state
    if latest_rsi is not None:
        if latest_rsi >= 70.0:
            rsi_state = "Overbought"
        elif latest_rsi <= 30.0:
            rsi_state = "Oversold"
        else:
            rsi_state = "Neutral"
    else:
        rsi_state = "Neutral"

    # MACD state
    if latest_macd is not None and latest_signal is not None and latest_hist is not None:
        if prev_hist is not None:
            if prev_hist <= 0 and latest_hist > 0:
                macd_state = "Bullish Crossover"
            elif prev_hist >= 0 and latest_hist < 0:
                macd_state = "Bearish Crossover"
            elif latest_macd > latest_signal:
                macd_state = "Bullish"
            else:
                macd_state = "Bearish"
        else:
            macd_state = "Bullish" if latest_macd > latest_signal else "Bearish"
    else:
        macd_state = "Neutral"

    # Bollinger state
    if latest_bb_upper is not None and latest_bb_lower is not None:
        if latest_close > latest_bb_upper:
            bb_state = "Upper Band Breakout"
        elif latest_close < latest_bb_lower:
            bb_state = "Lower Band Breakout"
        else:
            bb_state = "Normal"
    else:
        bb_state = "Normal"

    golden_cross = None
    if latest_sma50 is not None and latest_sma200 is not None:
        golden_cross = bool(latest_sma50 > latest_sma200)

    summary = TechnicalSummary(
        trend=trend,
        trend_description=trend_desc,
        rsi_state=rsi_state,
        rsi_value=latest_rsi,
        macd_state=macd_state,
        macd_histogram=latest_hist,
        bb_state=bb_state,
        golden_cross=golden_cross,
    )

    return points, summary
