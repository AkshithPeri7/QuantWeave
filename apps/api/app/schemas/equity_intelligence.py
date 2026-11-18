"""
Pydantic schemas for Advanced Equity Intelligence (Technicals, Fundamentals, and Comparison).
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class IndicatorPointSchema(BaseModel):
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


class TechnicalSummarySchema(BaseModel):
    trend: str
    trend_description: str
    rsi_state: str
    rsi_value: Optional[float] = None
    macd_state: str
    macd_histogram: Optional[float] = None
    bb_state: str
    golden_cross: Optional[bool] = None


class TechnicalAnalysisResponse(BaseModel):
    instrument_id: uuid.UUID
    symbol: str
    exchange: str
    company_name: str
    count: int
    summary: TechnicalSummarySchema
    points: List[IndicatorPointSchema]


class FinancialStatementSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period_type: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    period_start_date: Optional[date] = None
    period_end_date: date
    filing_date: Optional[date] = None
    currency: str
    is_synthetic: bool

    # Income Statement
    revenue: Optional[Decimal] = None
    cost_of_goods_sold: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    tax_expense: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    eps: Optional[Decimal] = None
    diluted_shares: Optional[Decimal] = None

    # Balance Sheet
    cash_and_equivalents: Optional[Decimal] = None
    total_current_assets: Optional[Decimal] = None
    total_non_current_assets: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    total_current_liabilities: Optional[Decimal] = None
    total_long_term_debt: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    shareholder_equity: Optional[Decimal] = None
    book_value_per_share: Optional[Decimal] = None

    # Cash Flow
    operating_cash_flow: Optional[Decimal] = None
    capital_expenditures: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    net_change_in_cash: Optional[Decimal] = None


class FundamentalRatiosSchema(BaseModel):
    period_type: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    period_end_date: str
    currency: str
    is_synthetic: bool
    price: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    operating_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    roe_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    operating_income: Optional[float] = None
    eps: Optional[float] = None
    total_assets: Optional[float] = None
    total_debt: Optional[float] = None
    shareholder_equity: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None


class CompanyFundamentalsResponse(BaseModel):
    instrument_id: uuid.UUID
    symbol: str
    exchange: str
    company_name: str
    currency: str
    is_synthetic: bool
    disclaimer: str
    statements: List[FinancialStatementSchema]
    latest_ratios: Optional[FundamentalRatiosSchema] = None


class InstrumentComparisonMetricsSchema(BaseModel):
    instrument_id: str
    symbol: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    currency: str
    latest_price: Optional[float] = None
    period_return_pct: Optional[float] = None
    annualized_volatility_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_signal_state: str
    ma_cross_state: Optional[str] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    operating_margin_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    has_fundamentals: bool


class NormalizedChartPointSchema(BaseModel):
    trade_date: str
    prices: Dict[str, Optional[float]]


class EquityComparisonResponse(BaseModel):
    period: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instruments: List[InstrumentComparisonMetricsSchema]
    normalized_chart: List[NormalizedChartPointSchema]
    is_demo: bool = True
    disclaimer: str = (
        "Educational comparison analytics. Historical returns, technical indicators, "
        "and synthetic demo statements do not constitute investment advice."
    )
