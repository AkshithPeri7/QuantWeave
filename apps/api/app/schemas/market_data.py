from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PriceBar(BaseModel):
    trade_date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Decimal = Field(..., gt=0, description="Closing price must be greater than 0")
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = Field(default=None, ge=0, description="Volume must be non-negative")
    currency: str = "INR"
    is_demo: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_ohlc_relationships(self) -> "PriceBar":
        o, h, l, c = self.open, self.high, self.low, self.close

        if h is not None and l is not None and h < l:
            raise ValueError(f"High price ({h}) cannot be less than low price ({l})")

        if h is not None:
            if o is not None and h < o:
                raise ValueError(f"High price ({h}) cannot be less than open price ({o})")
            if h < c:
                raise ValueError(f"High price ({h}) cannot be less than close price ({c})")

        if l is not None:
            if o is not None and l > o:
                raise ValueError(f"Low price ({l}) cannot be greater than open price ({o})")
            if l > c:
                raise ValueError(f"Low price ({l}) cannot be greater than close price ({c})")

        if o is not None and o <= 0:
            raise ValueError(f"Open price ({o}) must be positive")
        if l is not None and l <= 0:
            raise ValueError(f"Low price ({l}) must be positive")

        return self


class InstrumentBase(BaseModel):
    exchange: str = Field(..., min_length=1, max_length=20, description="Exchange code, e.g. NSE, BSE")
    symbol: str = Field(..., min_length=1, max_length=80, description="Trading ticker, e.g. RELIANCE, TCS")
    company_name: str = Field(..., min_length=1, max_length=255)
    isin: Optional[str] = Field(default=None, max_length=20)
    instrument_type: str = Field(default="equity", max_length=30)
    sector: Optional[str] = Field(default=None, max_length=120)
    industry: Optional[str] = Field(default=None, max_length=120)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    is_active: bool = True
    is_demo: bool = False


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentResponse(InstrumentBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstrumentDetailResponse(InstrumentResponse):
    latest_price: Optional[PriceBar] = None
    data_source: Optional[str] = None
    as_of: Optional[date] = None


class PaginatedInstruments(BaseModel):
    items: List[InstrumentResponse]
    total: int
    page: int
    size: int
    pages: int


class PriceHistoryResponse(BaseModel):
    instrument_id: uuid.UUID
    symbol: str
    exchange: str
    company_name: str
    currency: str
    is_demo: bool
    data_source: Optional[str] = None
    count: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prices: List[PriceBar]


class IngestionRunResponse(BaseModel):
    id: uuid.UUID
    provider_name: str
    dataset: str
    status: str
    rows_processed: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
