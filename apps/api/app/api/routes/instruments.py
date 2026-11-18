from datetime import date
from math import ceil
from typing import List, Optional
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.comparison import compare_equities
from app.analytics.fundamentals import calculate_statement_ratios
from app.analytics.technical import calculate_all_technicals
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.data_source import DataSource
from app.models.financial_statement import FinancialStatement
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory
from app.models.user import User
from app.providers.financial_fixtures import seed_demo_financial_statements
from app.schemas.equity_intelligence import (
    CompanyFundamentalsResponse,
    EquityComparisonResponse,
    FinancialStatementSchema,
    FundamentalRatiosSchema,
    IndicatorPointSchema,
    InstrumentComparisonMetricsSchema,
    NormalizedChartPointSchema,
    TechnicalAnalysisResponse,
    TechnicalSummarySchema,
)
from app.schemas.market_data import (
    IngestionRunResponse,
    InstrumentDetailResponse,
    InstrumentResponse,
    PaginatedInstruments,
    PriceBar,
    PriceHistoryResponse,
)
from app.services.ingestion import CsvMarketDataIngestionService, seed_demo_market_data

router = APIRouter(prefix="/api/v1/instruments", tags=["instruments"])


@router.get("", response_model=PaginatedInstruments)
async def list_instruments(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange, e.g. NSE"),
    sector: Optional[str] = Query(None, description="Filter by sector, e.g. Information Technology"),
    instrument_type: Optional[str] = Query(None, description="Filter by instrument type, e.g. equity"),
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    db: Session = Depends(get_db),
) -> PaginatedInstruments:
    """Returns paginated list of instruments with optional domain filters."""
    query = db.query(Instrument)

    if exchange:
        query = query.filter(Instrument.exchange == exchange.upper().strip())
    if sector:
        query = query.filter(Instrument.sector == sector.strip())
    if instrument_type:
        query = query.filter(Instrument.instrument_type == instrument_type.lower().strip())
    if is_active is not None:
        query = query.filter(Instrument.is_active == is_active)

    total = query.count()
    pages = max(1, ceil(total / size)) if total > 0 else 1
    offset = (page - 1) * size

    items = query.order_by(Instrument.symbol.asc()).offset(offset).limit(size).all()

    return PaginatedInstruments(
        items=[InstrumentResponse.model_validate(inst) for inst in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/search", response_model=List[InstrumentResponse])
async def search_instruments(
    q: str = Query(..., min_length=1, description="Search query matching ticker symbol or company name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of matches to return"),
    db: Session = Depends(get_db),
) -> List[InstrumentResponse]:
    """Searches instruments by ticker symbol or company name."""
    search_term = f"%{q.strip()}%"
    results = (
        db.query(Instrument)
        .filter(
            or_(
                Instrument.symbol.ilike(search_term),
                Instrument.company_name.ilike(search_term),
            )
        )
        .order_by(Instrument.symbol.asc())
        .limit(limit)
        .all()
    )
    return [InstrumentResponse.model_validate(inst) for inst in results]


@router.get("/compare", response_model=EquityComparisonResponse)
async def compare_instruments_endpoint(
    ids: str = Query(..., description="Comma-separated instrument UUIDs (between 1 and 4 instruments)"),
    period: str = Query("1Y", description="Evaluation time horizon (1M, 3M, 6M, 1Y, ALL)"),
    db: Session = Depends(get_db),
) -> EquityComparisonResponse:
    """
    Compares 1 to 4 instruments: normalized price performance, returns, volatility,
    drawdown, technical indicators, and fundamental ratios.
    """
    raw_ids = [s.strip() for s in ids.split(",") if s.strip()]
    if not raw_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one instrument ID must be specified for comparison.",
        )
    if len(raw_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A maximum of 4 instruments can be compared at one time.",
        )

    parsed_uuids = []
    for raw_id in raw_ids:
        try:
            parsed_uuids.append(uuid.UUID(raw_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: '{raw_id}'",
            )

    try:
        res = compare_equities(db=db, instrument_ids=parsed_uuids, period=period)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return EquityComparisonResponse(
        period=res.period,
        start_date=res.start_date,
        end_date=res.end_date,
        instruments=[
            InstrumentComparisonMetricsSchema(
                instrument_id=m.instrument_id,
                symbol=m.symbol,
                company_name=m.company_name,
                exchange=m.exchange,
                sector=m.sector,
                currency=m.currency,
                latest_price=m.latest_price,
                period_return_pct=m.period_return_pct,
                annualized_volatility_pct=m.annualized_volatility_pct,
                max_drawdown_pct=m.max_drawdown_pct,
                sma_20=m.sma_20,
                sma_50=m.sma_50,
                sma_200=m.sma_200,
                rsi_14=m.rsi_14,
                macd_signal_state=m.macd_signal_state,
                ma_cross_state=m.ma_cross_state,
                pe_ratio=m.pe_ratio,
                pb_ratio=m.pb_ratio,
                roe_pct=m.roe_pct,
                net_margin_pct=m.net_margin_pct,
                operating_margin_pct=m.operating_margin_pct,
                debt_to_equity=m.debt_to_equity,
                current_ratio=m.current_ratio,
                has_fundamentals=m.has_fundamentals,
            )
            for m in res.instruments
        ],
        normalized_chart=[
            NormalizedChartPointSchema(trade_date=p.trade_date, prices=p.prices)
            for p in res.normalized_chart
        ],
    )


@router.get("/{id}", response_model=InstrumentDetailResponse)
async def get_instrument(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> InstrumentDetailResponse:
    """Returns detailed instrument profile with latest price and data source attribution."""
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{id}' not found",
        )

    # Fetch latest price bar
    latest_price_rec = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.desc())
        .first()
    )

    latest_bar: Optional[PriceBar] = None
    data_source_name: Optional[str] = None
    as_of: Optional[date] = None

    if latest_price_rec:
        latest_bar = PriceBar.model_validate(latest_price_rec)
        as_of = latest_price_rec.trade_date
        if latest_price_rec.provider_id:
            ds = db.query(DataSource).filter(DataSource.id == latest_price_rec.provider_id).first()
            if ds:
                data_source_name = f"{ds.provider_name} ({ds.dataset})"

    return InstrumentDetailResponse(
        id=inst.id,
        exchange=inst.exchange,
        symbol=inst.symbol,
        company_name=inst.company_name,
        isin=inst.isin,
        instrument_type=inst.instrument_type,
        sector=inst.sector,
        industry=inst.industry,
        currency=inst.currency,
        is_active=inst.is_active,
        is_demo=inst.is_demo,
        created_at=inst.created_at,
        latest_price=latest_bar,
        data_source=data_source_name,
        as_of=as_of,
    )


@router.get("/{id}/prices", response_model=PriceHistoryResponse)
async def get_instrument_prices(
    id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date filter (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date filter (inclusive)"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum observations to return"),
    db: Session = Depends(get_db),
) -> PriceHistoryResponse:
    """Returns historical daily price observations with provenance and freshness."""
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{id}' not found",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    query = db.query(PriceHistory).filter(PriceHistory.instrument_id == inst.id)

    if start_date:
        query = query.filter(PriceHistory.trade_date >= start_date)
    if end_date:
        query = query.filter(PriceHistory.trade_date <= end_date)

    price_records = query.order_by(PriceHistory.trade_date.asc()).limit(limit).all()

    data_source_name: Optional[str] = None
    if price_records and price_records[0].provider_id:
        ds = db.query(DataSource).filter(DataSource.id == price_records[0].provider_id).first()
        if ds:
            data_source_name = f"{ds.provider_name}:{ds.dataset}"

    prices = [PriceBar.model_validate(p) for p in price_records]

    return PriceHistoryResponse(
        instrument_id=inst.id,
        symbol=inst.symbol,
        exchange=inst.exchange,
        company_name=inst.company_name,
        currency=inst.currency,
        is_demo=inst.is_demo,
        data_source=data_source_name,
        count=len(prices),
        start_date=prices[0].trade_date if prices else None,
        end_date=prices[-1].trade_date if prices else None,
        prices=prices,
    )


@router.get("/{id}/technicals", response_model=TechnicalAnalysisResponse)
async def get_instrument_technicals(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TechnicalAnalysisResponse:
    """
    Calculates technical indicators (SMA 20/50/200, EMA 12/26, RSI 14, MACD, Bollinger Bands)
    and generates an automated technical analysis summary for the instrument.
    """
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{id}' not found",
        )

    price_records = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.asc())
        .all()
    )

    points, summary = calculate_all_technicals(price_records)

    return TechnicalAnalysisResponse(
        instrument_id=inst.id,
        symbol=inst.symbol,
        exchange=inst.exchange,
        company_name=inst.company_name,
        count=len(points),
        summary=TechnicalSummarySchema(
            trend=summary.trend,
            trend_description=summary.trend_description,
            rsi_state=summary.rsi_state,
            rsi_value=summary.rsi_value,
            macd_state=summary.macd_state,
            macd_histogram=summary.macd_histogram,
            bb_state=summary.bb_state,
            golden_cross=summary.golden_cross,
        ),
        points=[
            IndicatorPointSchema(
                trade_date=p.trade_date,
                close=p.close,
                sma_20=p.sma_20,
                sma_50=p.sma_50,
                sma_200=p.sma_200,
                ema_12=p.ema_12,
                ema_26=p.ema_26,
                rsi_14=p.rsi_14,
                macd_line=p.macd_line,
                macd_signal=p.macd_signal,
                macd_hist=p.macd_hist,
                bb_upper=p.bb_upper,
                bb_middle=p.bb_middle,
                bb_lower=p.bb_lower,
                bb_bandwidth=p.bb_bandwidth,
                bb_percent_b=p.bb_percent_b,
            )
            for p in points
        ],
    )


@router.get("/{id}/fundamentals", response_model=CompanyFundamentalsResponse)
async def get_instrument_fundamentals(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CompanyFundamentalsResponse:
    """
    Retrieves multi-year financial statements (Income Statement, Balance Sheet, Cash Flow)
    and calculates current valuation and profitability ratios.
    """
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{id}' not found",
        )

    statements = (
        db.query(FinancialStatement)
        .filter(FinancialStatement.instrument_id == inst.id)
        .order_by(FinancialStatement.fiscal_year.desc(), FinancialStatement.fiscal_quarter.desc().nullsfirst())
        .all()
    )

    # Fetch latest closing price for P/E and P/B calculation
    latest_price_rec = (
        db.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .order_by(PriceHistory.trade_date.desc())
        .first()
    )
    latest_close = float(latest_price_rec.close) if latest_price_rec else None

    # Calculate ratios based on the most recent annual statement if available
    latest_ratios_schema: Optional[FundamentalRatiosSchema] = None
    annual_stmt = next((s for s in statements if s.period_type == "annual"), None)
    if annual_stmt:
        ratios = calculate_statement_ratios(annual_stmt, latest_price=latest_close)
        latest_ratios_schema = FundamentalRatiosSchema(
            period_type=ratios.period_type,
            fiscal_year=ratios.fiscal_year,
            fiscal_quarter=ratios.fiscal_quarter,
            period_end_date=ratios.period_end_date,
            currency=ratios.currency,
            is_synthetic=ratios.is_synthetic,
            price=ratios.price,
            pe_ratio=ratios.pe_ratio,
            pb_ratio=ratios.pb_ratio,
            gross_margin_pct=ratios.gross_margin_pct,
            operating_margin_pct=ratios.operating_margin_pct,
            net_margin_pct=ratios.net_margin_pct,
            roe_pct=ratios.roe_pct,
            debt_to_equity=ratios.debt_to_equity,
            current_ratio=ratios.current_ratio,
            revenue=ratios.revenue,
            net_income=ratios.net_income,
            operating_income=ratios.operating_income,
            eps=ratios.eps,
            total_assets=ratios.total_assets,
            total_debt=ratios.total_debt,
            shareholder_equity=ratios.shareholder_equity,
            operating_cash_flow=ratios.operating_cash_flow,
            free_cash_flow=ratios.free_cash_flow,
        )

    return CompanyFundamentalsResponse(
        instrument_id=inst.id,
        symbol=inst.symbol,
        exchange=inst.exchange,
        company_name=inst.company_name,
        currency=inst.currency,
        is_synthetic=True,
        disclaimer=(
            "DEMO SYNTHETIC FINANCIALS: Financial statement line items and ratios are "
            "synthetic fixtures generated for financial modeling and education. "
            "They do not represent audited corporate filings."
        ),
        statements=[FinancialStatementSchema.model_validate(s) for s in statements],
        latest_ratios=latest_ratios_schema,
    )


@router.post("/{id}/ingest/csv", response_model=IngestionRunResponse)
async def ingest_csv_prices(
    id: uuid.UUID,
    csv_content: str = Body(..., media_type="text/plain", description="CSV string content"),
    provider_name: str = Query("user_upload_csv", description="Attributed provider name"),
    dataset: str = Query("custom_upload", description="Attributed dataset name"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> IngestionRunResponse:
    """
    Ingests historical prices from raw CSV text with size constraints, content verification,
    and authentication safeguards.
    """
    MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB max payload
    if len(csv_content.encode("utf-8")) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV payload exceeds maximum allowed size of 5 MB",
        )

    if not csv_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV payload cannot be empty",
        )

    if "\x00" in csv_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV payload contains prohibited binary null characters",
        )

    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{id}' not found",
        )

    # Restricted to admin or development/testing environment
    if settings.environment not in ["development", "testing"] and (not current_user or current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for manual CSV data ingestion outside development environment",
        )

    run = CsvMarketDataIngestionService.ingest_csv(
        db=db,
        instrument_id=inst.id,
        csv_content=csv_content,
        provider_name=provider_name,
        dataset=dataset,
    )
    return IngestionRunResponse.model_validate(run)


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_market_data_endpoint(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
) -> dict:
    """
    Seeds default synthetic demo market data and financial statements for Indian equities.
    Guarded in production environments to prevent unauthorized database modifications.
    """
    # Guarded to prevent unauthorized database modifications outside development
    if settings.environment not in ["development", "testing"] and (not current_user or current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to trigger demo database seeding outside development environment",
        )

    instruments_count, prices_count = seed_demo_market_data(db)
    statements_count = seed_demo_financial_statements(db)
    return {
        "status": "success",
        "message": "Seeded demo market data and synthetic financial statements",
        "instruments_created": instruments_count,
        "prices_created": prices_count,
        "financial_statements_created": statements_count,
    }
