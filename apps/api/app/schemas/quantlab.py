"""
Pydantic Schemas for QuantLab: Strategy Research, Simulation & Backtesting Engine.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. Strategy Schemas
# ==========================================

class StrategyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Unique strategy name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Strategy hypothesis and notes")
    strategy_type: str = Field(..., description="SMA_CROSSOVER, EMA_CROSSOVER, RSI_THRESHOLD, BUY_AND_HOLD")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    parameters: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Backtest Execution Schemas
# ==========================================

class BacktestRequest(BaseModel):
    instrument_id: uuid.UUID = Field(..., description="Target equity instrument ID")
    start_date: date = Field(..., description="Simulation start date")
    end_date: date = Field(..., description="Simulation end date")
    starting_capital: float = Field(default=100000.0, ge=1000.0, le=100000000.0, description="Starting cash in INR")
    fee_rate: float = Field(default=0.001, ge=0.0, le=0.05, description="Proportional fee rate per trade (e.g. 0.001 = 0.1%)")
    slippage_bps: float = Field(default=5.0, ge=0.0, le=100.0, description="Slippage in basis points (e.g. 5 bps = 0.05%)")

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return v


class InstantBacktestRequest(BacktestRequest):
    strategy_type: str = Field(..., description="SMA_CROSSOVER, EMA_CROSSOVER, RSI_THRESHOLD, BUY_AND_HOLD")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the strategy")


class BacktestTradeResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    side: str
    signal_date: date
    execution_date: date
    quantity: float
    execution_price: float
    fees: float
    slippage_cost: float
    cash_after: float
    position_after: float
    realized_pnl: Optional[float] = None
    pnl_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class BacktestEquityPointResponse(BaseModel):
    point_date: date
    equity: float
    cash: float
    position_value: float
    drawdown_pct: float
    benchmark_equity: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class BacktestRunResponse(BaseModel):
    id: uuid.UUID
    strategy_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    instrument_id: uuid.UUID
    instrument_ticker: Optional[str] = None
    instrument_name: Optional[str] = None
    strategy_name: Optional[str] = None
    strategy_type: Optional[str] = None
    starting_capital: float
    start_date: date
    end_date: date
    fee_rate: float
    slippage_bps: float
    status: str
    metrics: Optional[Dict[str, Any]] = None
    dataset_fingerprint: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Parameter Grid Search Schemas
# ==========================================

class GridSearchRequest(BaseModel):
    strategy_type: str = Field(..., description="SMA_CROSSOVER, EMA_CROSSOVER, RSI_THRESHOLD")
    param_grid: Dict[str, List[Any]] = Field(..., description="Mapping of parameter names to lists of candidate values")
    instrument_id: uuid.UUID = Field(..., description="Target equity instrument ID")
    start_date: date = Field(..., description="Total backtesting period start date")
    end_date: date = Field(..., description="Total backtesting period end date")
    starting_capital: float = Field(default=100000.0, ge=1000.0, le=100000000.0)
    fee_rate: float = Field(default=0.001, ge=0.0, le=0.05)
    slippage_bps: float = Field(default=5.0, ge=0.0, le=100.0)
    train_ratio: float = Field(default=0.7, ge=0.5, le=0.9, description="Fraction of period allocated to in-sample training (e.g. 0.70)")

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return v


class GridSearchResultItem(BaseModel):
    params: Dict[str, Any]
    in_sample_return_pct: float
    in_sample_sharpe: Optional[float] = None
    in_sample_max_dd_pct: float
    out_of_sample_return_pct: float
    out_of_sample_sharpe: Optional[float] = None
    out_of_sample_max_dd_pct: float
    overfitting_warning: bool
    status: str
    error_message: Optional[str] = None


class GridSearchResponse(BaseModel):
    strategy_type: str
    instrument_id: uuid.UUID
    combinations_tested: int
    results: List[GridSearchResultItem]
    best_params: Optional[Dict[str, Any]] = None
    summary: str


# ==========================================
# 4. Run Comparison Schemas
# ==========================================

class BacktestComparisonRequest(BaseModel):
    run_ids: List[uuid.UUID] = Field(..., min_length=2, max_length=5, description="Between 2 and 5 backtest run IDs to compare")


class BacktestComparisonItem(BaseModel):
    run_id: uuid.UUID
    strategy_name: Optional[str] = None
    strategy_type: Optional[str] = None
    instrument_ticker: Optional[str] = None
    start_date: date
    end_date: date
    starting_capital: float
    fee_rate: float
    slippage_bps: float
    metrics: Optional[Dict[str, Any]] = None


class BacktestComparisonResponse(BaseModel):
    runs: List[BacktestComparisonItem]
