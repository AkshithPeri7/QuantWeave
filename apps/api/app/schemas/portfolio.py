"""
Pydantic Schemas for Portfolio Intelligence MVP.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description")
    base_currency: str = Field(default="INR", max_length=3, description="Base currency (MVP supports INR only)")


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    transaction_type: str = Field(..., description="BUY, SELL, DIVIDEND, CASH_DEPOSIT, CASH_WITHDRAWAL")
    trade_date: date
    quantity: Decimal = Field(default=Decimal("0.00000000"), ge=0)
    price_per_unit: Decimal = Field(default=Decimal("0.000000"), ge=0)
    fees: Decimal = Field(default=Decimal("0.000000"), ge=0)
    instrument_id: Optional[uuid.UUID] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    idempotency_key: Optional[str] = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_type_fields(self) -> "TransactionCreate":
        tt = self.transaction_type.upper().strip()
        self.transaction_type = tt
        if tt in {"BUY", "SELL"}:
            if not self.instrument_id:
                raise ValueError(f"instrument_id is required for {tt} transactions")
            if self.quantity <= 0:
                raise ValueError(f"Quantity must be greater than zero for {tt}")
            if self.price_per_unit <= 0:
                raise ValueError(f"Price per unit must be greater than zero for {tt}")
        elif tt in {"CASH_DEPOSIT", "CASH_WITHDRAWAL"}:
            amt = self.price_per_unit if self.price_per_unit > 0 else self.quantity
            if amt <= 0:
                raise ValueError(f"Amount must be greater than zero for {tt}")
        elif tt == "DIVIDEND":
            if not self.instrument_id:
                raise ValueError("instrument_id is required for DIVIDEND transactions")
            amt = self.price_per_unit if self.price_per_unit > 0 else self.quantity
            if amt <= 0:
                raise ValueError("Dividend amount must be greater than zero")
        else:
            raise ValueError(
                f"Invalid transaction type '{tt}'. Allowed: BUY, SELL, DIVIDEND, CASH_DEPOSIT, CASH_WITHDRAWAL"
            )
        return self


class TransactionResponse(BaseModel):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    instrument_id: Optional[uuid.UUID] = None
    instrument_symbol: Optional[str] = None
    instrument_name: Optional[str] = None
    transaction_type: str
    trade_date: date
    trade_timestamp: datetime
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal
    cash_amount: Decimal
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HoldingResponse(BaseModel):
    instrument_id: str
    symbol: str
    exchange: str
    company_name: str
    sector: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Optional[Decimal] = None
    cost_basis: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal
    allocation_percent: Decimal
    price_date: Optional[str] = None
    is_stale: bool = False
    is_demo: bool = False


class AllocationItem(BaseModel):
    name: str
    symbol: Optional[str] = None
    value: Decimal
    percentage: Decimal
    type: Optional[str] = None


class SectorAllocationItem(BaseModel):
    sector: str
    value: Decimal
    percentage: Decimal


class PortfolioValuationResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    base_currency: str
    as_of_date: str
    total_value: Decimal
    cash_balance: Decimal
    holdings_market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    holdings: List[HoldingResponse]
    asset_allocations: List[AllocationItem]
    sector_allocations: List[SectorAllocationItem]


class PortfolioPerformanceResponse(BaseModel):
    twr_percent: Optional[float] = None
    xirr_percent: Optional[float] = None
    annualized_volatility_percent: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_percent: float
    risk_free_rate_percent: float
    timeline_days: int


class EquityPointResponse(BaseModel):
    date: str
    total_value: float
    cash: float
    holdings_value: float
    net_external_flow: float
