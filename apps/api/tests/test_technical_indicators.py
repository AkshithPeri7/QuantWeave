"""
Unit tests for the Technical Analysis Engine (technical.py).
Tests calculations against known reference examples and edge cases:
- Insufficient observations (returns None without throwing)
- Constant price series (zero division prevention)
- Wilder's 1978 RSI smoothing convention
- MACD and Bollinger Band formulas
"""

from datetime import date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
import pytest

from app.analytics.technical import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_all_technicals,
)
from app.schemas.market_data import PriceBar


def test_sma_reference_and_insufficient_data():
    # Test series with 10 values
    prices = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0])
    
    sma_5 = calculate_sma(prices, window=5)
    # The first 4 values should be NaN
    assert sma_5.iloc[:4].isna().all()
    # At index 4 (values 10, 11, 12, 13, 14), mean is 12.0
    assert pytest.approx(sma_5.iloc[4], rel=1e-5) == 12.0
    # At index 9 (values 15, 16, 17, 18, 19), mean is 17.0
    assert pytest.approx(sma_5.iloc[9], rel=1e-5) == 17.0

    # Insufficient data
    sma_20 = calculate_sma(prices, window=20)
    assert sma_20.isna().all()


def test_ema_reference_calculation():
    # EMA formula: alpha = 2 / (span + 1)
    # Span = 3 -> alpha = 2 / 4 = 0.5
    prices = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])
    ema_3 = calculate_ema(prices, span=3)

    # First 2 values should be NaN
    assert ema_3.iloc[:2].isna().all()
    # At index 2: initial value is the 3-period SMA: (10 + 12 + 14) / 3 = 12.0
    # Note: in pandas ewm with adjust=False:
    # y_0 = 10, y_1 = 0.5*12 + 0.5*10 = 11, y_2 = 0.5*14 + 0.5*11 = 12.5
    assert not np.isnan(ema_3.iloc[2])
    # Next value: 0.5 * 16.0 + 0.5 * 12.5 = 14.25
    assert pytest.approx(ema_3.iloc[3], rel=1e-3) == 14.25
    # Next value: 0.5 * 18.0 + 0.5 * 14.25 = 16.125
    assert pytest.approx(ema_3.iloc[4], rel=1e-3) == 16.125


def test_rsi_wilder_smoothing_reference():
    """
    Tests Wilder's RSI on known 15-day price series:
    Prices with 14 changes.
    """
    # 15 days of prices:
    prices = pd.Series([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 
        46.08, 45.89, 46.03, 45.61, 46.28, 46.28
    ])
    rsi = calculate_rsi(prices, period=14)

    # First 14 entries (indices 0..13) must be NaN
    assert rsi.iloc[:14].isna().all()

    # Index 14 has the first 14-period RSI
    val_14 = rsi.iloc[14]
    assert not np.isnan(val_14)
    # Price difference gains and losses:
    # 44.09 - 44.34 = -0.25 (loss 0.25)
    # 44.15 - 44.09 = +0.06 (gain 0.06)
    # etc.
    # Manual verification: RSI should be in standard range (approx 65-75 given mostly up days)
    assert 60.0 <= val_14 <= 80.0


def test_rsi_constant_price_zero_division():
    # If all prices are identical, price changes are 0 (gain=0, loss=0)
    prices = pd.Series([100.0] * 30)
    rsi = calculate_rsi(prices, period=14)

    # Must not raise ZeroDivisionError and should return 50.0 (neutral)
    assert rsi.iloc[14] == 50.0
    assert rsi.iloc[-1] == 50.0


def test_rsi_strictly_increasing():
    # If price only increases, losses are 0
    prices = pd.Series([float(i) for i in range(30)])
    rsi = calculate_rsi(prices, period=14)
    # If loss is 0 and gain > 0, RSI = 100
    assert rsi.iloc[14] == 100.0
    assert rsi.iloc[-1] == 100.0


def test_macd_calculation():
    # Generate 50 points of synthetic prices
    prices = pd.Series([100.0 + i * 0.5 + np.sin(i / 3.0) * 2.0 for i in range(50)])
    macd_line, signal_line, histogram = calculate_macd(prices, fast=12, slow=26, signal=9)

    # Before 26 periods, macd_line is NaN
    assert macd_line.iloc[:25].isna().all()
    assert not np.isnan(macd_line.iloc[25])

    # Signal line requires slow (26) + signal (9) observations
    assert signal_line.iloc[:33].isna().all()
    assert not np.isnan(signal_line.iloc[34])

    # Histogram = macd_line - signal_line
    valid_idx = 40
    assert pytest.approx(histogram.iloc[valid_idx], rel=1e-5) == (
        macd_line.iloc[valid_idx] - signal_line.iloc[valid_idx]
    )


def test_bollinger_bands_calculation():
    prices = pd.Series([50.0] * 20)
    upper, middle, lower, bandwidth, percent_b = calculate_bollinger_bands(prices, window=20, num_std=2.0)

    # First 19 are NaN
    assert upper.iloc[:19].isna().all()
    # At index 19: constant price 50.0 -> std = 0
    assert middle.iloc[19] == 50.0
    assert upper.iloc[19] == 50.0
    assert lower.iloc[19] == 50.0
    # Zero bandwidth
    assert bandwidth.iloc[19] == 0.0
    # Center %B at 0.5 when upper == lower
    assert percent_b.iloc[19] == 0.5


def test_calculate_all_technicals_integration():
    bars = []
    base_date = date(2025, 1, 1)
    for i in range(250):
        d = base_date + timedelta(days=i)
        price = 100.0 + i * 0.2 + (5.0 if i % 2 == 0 else -3.0)
        bars.append(
            PriceBar(
                trade_date=d,
                open=Decimal(str(round(price - 1.0, 2))),
                high=Decimal(str(round(price + 2.0, 2))),
                low=Decimal(str(round(price - 2.0, 2))),
                close=Decimal(str(round(price, 2))),
                volume=10000 + i * 10,
            )
        )

    points, summary = calculate_all_technicals(bars)
    assert len(points) == 250
    assert summary.trend in ["Bullish", "Bearish", "Neutral"]
    assert summary.rsi_state in ["Overbought", "Oversold", "Neutral"]
    assert summary.macd_state is not None
    assert summary.golden_cross is not None

    # Verify latest point has non-null SMA 20, 50, 200, EMA 12, 26, RSI 14, MACD, BB
    last_pt = points[-1]
    assert last_pt.sma_20 is not None
    assert last_pt.sma_50 is not None
    assert last_pt.sma_200 is not None
    assert last_pt.ema_12 is not None
    assert last_pt.ema_26 is not None
    assert last_pt.rsi_14 is not None
    assert last_pt.macd_line is not None
    assert last_pt.bb_upper is not None
