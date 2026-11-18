"""
Pydantic Schemas for Mutual Fund Intelligence (FundScope).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class FundNAVPoint(BaseModel):
    nav_date: date
    nav: Decimal = Field(..., gt=0, description="NAV must be strictly positive")
    repurchase_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    is_demo: bool = True

    model_config = ConfigDict(from_attributes=True)


class MutualFundBase(BaseModel):
    scheme_code: str = Field(..., min_length=1, max_length=50)
    isin: Optional[str] = Field(default=None, max_length=20)
    scheme_name: str = Field(..., min_length=1, max_length=255)
    amc_name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=50)
    subcategory: str = Field(..., min_length=1, max_length=100)
    plan_type: str = Field(default="Direct", max_length=20)
    option_type: str = Field(default="Growth", max_length=20)
    benchmark_name: Optional[str] = Field(default=None, max_length=150)
    expense_ratio: Optional[Decimal] = Field(default=None, ge=0)
    aum_crores: Optional[Decimal] = Field(default=None, ge=0)
    fund_manager: Optional[str] = Field(default=None, max_length=200)
    crisil_rating: Optional[int] = Field(default=None, ge=1, le=5)
    is_active: bool = True
    is_demo: bool = True


class MutualFundCreate(MutualFundBase):
    pass


class MutualFundResponse(MutualFundBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MutualFundDetailResponse(MutualFundResponse):
    latest_nav: Optional[FundNAVPoint] = None
    trailing_returns: Optional[Dict[str, Any]] = None


class PaginatedMutualFunds(BaseModel):
    items: List[MutualFundResponse]
    total: int
    page: int
    size: int
    pages: int


class FundNAVHistoryResponse(BaseModel):
    fund_id: uuid.UUID
    scheme_code: str
    scheme_name: str
    amc_name: str
    category: str
    subcategory: str
    is_demo: bool
    count: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    navs: List[FundNAVPoint]


class FundAnalyticsResponse(BaseModel):
    fund_id: str
    scheme_code: str
    scheme_name: str
    amc_name: str
    category: str
    subcategory: str
    trailing_returns: Dict[str, Any]
    rolling_returns_1y: Dict[str, Any]
    rolling_returns_3y: Dict[str, Any]
    volatility_pct: Optional[float] = None
    max_drawdown_pct: float = 0.0
    is_demo: bool = True
    disclaimer: str = "DEMO DATA: Indicators calculated on synthetic NAV history for educational analysis."


class SIPCalculatorRequest(BaseModel):
    monthly_amount: Decimal = Field(..., gt=0, description="Monthly installment in INR, e.g. 5000.00")
    start_date: date
    end_date: Optional[date] = None
    sip_day: int = Field(default=5, ge=1, le=28, description="Day of month for installment")


class SIPInstallmentPoint(BaseModel):
    installment_number: int
    scheduled_date: str
    executed_date: str
    nav: float
    amount: float
    units: float
    total_units: float
    cumulative_invested: float


class SIPCalculatorResponse(BaseModel):
    fund_id: str
    scheme_name: str
    monthly_amount: float
    start_date: str
    end_date: str
    installments_count: int
    total_invested: float
    final_value: float
    total_profit: float
    absolute_return_pct: float
    xirr_pct: Optional[float] = None
    units_accumulated: float
    latest_nav: float
    installments: List[SIPInstallmentPoint]
    timeline: List[Dict[str, Any]]
    is_demo: bool = True
    disclaimer: str = "Historical simulation based on synthetic NAV series. Not guaranteed future returns."


class LumpSumCalculatorRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Initial one-time investment in INR")
    start_date: date
    end_date: Optional[date] = None


class LumpSumCalculatorResponse(BaseModel):
    fund_id: str
    scheme_name: str
    initial_investment: float
    start_date: str
    end_date: str
    start_nav: float
    end_nav: float
    units_accumulated: float
    final_value: float
    total_profit: float
    absolute_return_pct: float
    cagr_pct: Optional[float] = None
    duration_days: int
    timeline: List[Dict[str, Any]]
    is_demo: bool = True
    disclaimer: str = "Historical simulation based on synthetic NAV series. Not guaranteed future returns."


class FundComparisonItem(BaseModel):
    fund_id: str
    scheme_code: str
    scheme_name: str
    amc_name: str
    category: str
    subcategory: str
    plan_type: str
    option_type: str
    crisil_rating: Optional[int] = None
    expense_ratio: Optional[float] = None
    aum_crores: Optional[float] = None
    latest_nav: Optional[float] = None
    period_return_pct: Optional[float] = None
    cagr_pct: Optional[float] = None
    annualized_volatility_pct: Optional[float] = None
    max_drawdown_pct: float
    observation_count: int


class FundComparisonResponse(BaseModel):
    period: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    funds: List[FundComparisonItem]
    normalized_chart: List[Dict[str, Any]]
    is_demo: bool = True
    disclaimer: str
