"""
Mutual Fund Intelligence (FundScope) API Endpoints for QuantWeave.

Implements:
- Fund discovery, search, filtering by category, subcategory, and AMC
- Detailed fund profiles with latest NAV and performance metrics
- Historical NAV time series retrieval
- Deep analytics: Trailing returns (1M to 5Y), Rolling returns (1Y, 3Y), Volatility, Drawdown
- Interactive SIP Calculator with dated cash flows, units, and true XIRR
- Lump-sum investment growth calculator
- Multi-fund comparison with normalized base-100 chart
- Secure admin/dev seeding and CSV ingestion
"""

from datetime import date
from math import ceil
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.fund_analytics import FundAnalyticsService
from app.analytics.fund_comparison import compare_mutual_funds
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.mutual_fund import MutualFund, FundNAVHistory
from app.models.user import User
from app.providers.fund_fixtures import seed_demo_mutual_funds
from app.schemas.mutual_fund import (
    FundAnalyticsResponse,
    FundComparisonResponse,
    FundNAVHistoryResponse,
    FundNAVPoint,
    LumpSumCalculatorRequest,
    LumpSumCalculatorResponse,
    MutualFundDetailResponse,
    MutualFundResponse,
    PaginatedMutualFunds,
    SIPCalculatorRequest,
    SIPCalculatorResponse,
)
from app.services.fund_ingestion import FundCSVIngestionService

router = APIRouter(prefix="/api/v1/funds", tags=["funds"])


def _verify_admin_access(current_user: User) -> None:
    """Verifies that the user has admin role or environment is dev/testing."""
    if current_user.role == "admin":
        return
    if settings.environment in ["development", "testing"]:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only platform administrators can perform data ingestion or seeding operations.",
    )


@router.get("", response_model=PaginatedMutualFunds)
async def list_mutual_funds(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Equity, Debt, Hybrid)"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory (e.g. Flexi Cap, Large Cap)"),
    amc: Optional[str] = Query(None, description="Filter by AMC name"),
    plan_type: Optional[str] = Query(None, description="Filter by plan type (Direct, Regular)"),
    q: Optional[str] = Query(None, description="Search term matching scheme name, code or AMC"),
    db: Session = Depends(get_db),
) -> PaginatedMutualFunds:
    """Retrieves paginated list of mutual fund schemes with optional filters."""
    query = db.query(MutualFund).filter(MutualFund.is_active == True)

    if category and category != "All":
        query = query.filter(MutualFund.category == category)
    if subcategory and subcategory != "All":
        query = query.filter(MutualFund.subcategory == subcategory)
    if amc and amc != "All":
        query = query.filter(MutualFund.amc_name.ilike(f"%{amc}%"))
    if plan_type and plan_type != "All":
        query = query.filter(MutualFund.plan_type.ilike(plan_type))

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                MutualFund.scheme_name.ilike(term),
                MutualFund.scheme_code.ilike(term),
                MutualFund.amc_name.ilike(term),
            )
        )

    total = query.count()
    pages = max(1, ceil(total / size)) if total > 0 else 1
    offset = (page - 1) * size

    items = (
        query.order_by(MutualFund.aum_crores.desc().nullslast(), MutualFund.scheme_name.asc())
        .offset(offset)
        .limit(size)
        .all()
    )

    return PaginatedMutualFunds(
        items=[MutualFundResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/search", response_model=List[MutualFundResponse])
async def search_mutual_funds(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[MutualFundResponse]:
    """Quick autocomplete search for mutual fund schemes."""
    term = f"%{q.strip()}%"
    results = (
        db.query(MutualFund)
        .filter(
            MutualFund.is_active == True,
            or_(
                MutualFund.scheme_name.ilike(term),
                MutualFund.scheme_code.ilike(term),
                MutualFund.amc_name.ilike(term),
            ),
        )
        .order_by(MutualFund.aum_crores.desc().nullslast())
        .limit(limit)
        .all()
    )
    return [MutualFundResponse.model_validate(f) for f in results]


@router.get("/categories")
async def get_fund_categories(db: Session = Depends(get_db)) -> dict:
    """Returns distinct categories, subcategories, and AMCs available in the catalog."""
    funds = db.query(MutualFund).filter(MutualFund.is_active == True).all()

    categories = sorted(list({f.category for f in funds if f.category}))
    subcategories = sorted(list({f.subcategory for f in funds if f.subcategory}))
    amcs = sorted(list({f.amc_name for f in funds if f.amc_name}))

    return {
        "categories": categories,
        "subcategories": subcategories,
        "amcs": amcs,
    }


@router.get("/compare", response_model=FundComparisonResponse)
async def compare_funds_endpoint(
    ids: str = Query(..., description="Comma-separated UUIDs of funds to compare (1 to 4 funds)"),
    period: str = Query("1Y", description="Comparison period: 1M, 3M, 6M, 1Y, 3Y, 5Y, ALL"),
    db: Session = Depends(get_db),
) -> FundComparisonResponse:
    """Compares up to 4 mutual funds with normalized base-100 chart and risk metrics."""
    raw_ids = [id_str.strip() for id_str in ids.split(",") if id_str.strip()]
    if not raw_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fund IDs provided.")
    if len(raw_ids) > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 4 funds can be compared.")

    parsed_uuids = []
    for raw in raw_ids:
        try:
            parsed_uuids.append(uuid.UUID(raw))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid UUID: '{raw}'")

    try:
        comparison_data = compare_mutual_funds(db, parsed_uuids, period)
        return FundComparisonResponse(**comparison_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{fund_id}", response_model=MutualFundDetailResponse)
async def get_mutual_fund(
    fund_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> MutualFundDetailResponse:
    """Retrieves full fund details including latest NAV and trailing returns snapshot."""
    fund = db.query(MutualFund).filter(MutualFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mutual fund '{fund_id}' not found.")

    latest_nav = (
        db.query(FundNAVHistory)
        .filter(FundNAVHistory.fund_id == fund.id)
        .order_by(FundNAVHistory.nav_date.desc())
        .first()
    )

    resp = MutualFundDetailResponse.model_validate(fund)
    if latest_nav:
        resp.latest_nav = FundNAVPoint.model_validate(latest_nav)

        # Quick trailing return calculation
        all_navs = (
            db.query(FundNAVHistory.nav_date, FundNAVHistory.nav)
            .filter(FundNAVHistory.fund_id == fund.id)
            .order_by(FundNAVHistory.nav_date.asc())
            .all()
        )
        if all_navs:
            series = [(r[0], r[1]) for r in all_navs]
            resp.trailing_returns = FundAnalyticsService.calculate_trailing_returns(series, latest_nav.nav_date)

    return resp


@router.get("/{fund_id}/nav", response_model=FundNAVHistoryResponse)
async def get_fund_nav_history(
    fund_id: uuid.UUID,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(500, ge=1, le=2000, description="Max NAV bars to return"),
    db: Session = Depends(get_db),
) -> FundNAVHistoryResponse:
    """Retrieves chronological historical NAV series for charting and research."""
    fund = db.query(MutualFund).filter(MutualFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mutual fund '{fund_id}' not found.")

    query = db.query(FundNAVHistory).filter(FundNAVHistory.fund_id == fund_id)
    if start_date:
        query = query.filter(FundNAVHistory.nav_date >= start_date)
    if end_date:
        query = query.filter(FundNAVHistory.nav_date <= end_date)

    nav_rows = query.order_by(FundNAVHistory.nav_date.asc()).limit(limit).all()

    return FundNAVHistoryResponse(
        fund_id=fund.id,
        scheme_code=fund.scheme_code,
        scheme_name=fund.scheme_name,
        amc_name=fund.amc_name,
        category=fund.category,
        subcategory=fund.subcategory,
        is_demo=fund.is_demo,
        count=len(nav_rows),
        start_date=nav_rows[0].nav_date if nav_rows else None,
        end_date=nav_rows[-1].nav_date if nav_rows else None,
        navs=[FundNAVPoint.model_validate(r) for r in nav_rows],
    )


@router.get("/{fund_id}/analytics", response_model=FundAnalyticsResponse)
async def get_fund_analytics(
    fund_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FundAnalyticsResponse:
    """Calculates comprehensive fund analytics: trailing returns, rolling returns, volatility, and max drawdown."""
    fund = db.query(MutualFund).filter(MutualFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mutual fund '{fund_id}' not found.")

    all_navs = (
        db.query(FundNAVHistory.nav_date, FundNAVHistory.nav)
        .filter(FundNAVHistory.fund_id == fund.id)
        .order_by(FundNAVHistory.nav_date.asc())
        .all()
    )
    if not all_navs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No NAV history available for this scheme.")

    series = [(r[0], r[1]) for r in all_navs]

    trailing = FundAnalyticsService.calculate_trailing_returns(series)
    rolling_1y = FundAnalyticsService.calculate_rolling_returns(series, window_days=365)
    rolling_3y = FundAnalyticsService.calculate_rolling_returns(series, window_days=1095)
    risk = FundAnalyticsService.calculate_risk_metrics(series)

    return FundAnalyticsResponse(
        fund_id=str(fund.id),
        scheme_code=fund.scheme_code,
        scheme_name=fund.scheme_name,
        amc_name=fund.amc_name,
        category=fund.category,
        subcategory=fund.subcategory,
        trailing_returns=trailing,
        rolling_returns_1y=rolling_1y,
        rolling_returns_3y=rolling_3y,
        volatility_pct=risk["annualized_volatility_pct"],
        max_drawdown_pct=risk["max_drawdown_pct"],
        is_demo=fund.is_demo,
    )


@router.post("/{fund_id}/sip-calculator", response_model=SIPCalculatorResponse)
async def calculate_sip_endpoint(
    fund_id: uuid.UUID,
    sip_req: SIPCalculatorRequest,
    db: Session = Depends(get_db),
) -> SIPCalculatorResponse:
    """
    Calculates realistic historical SIP investment using actual trading day NAVs,
    exact accumulated units, and true numerical XIRR.
    """
    fund = db.query(MutualFund).filter(MutualFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mutual fund '{fund_id}' not found.")

    all_navs = (
        db.query(FundNAVHistory.nav_date, FundNAVHistory.nav)
        .filter(FundNAVHistory.fund_id == fund.id)
        .order_by(FundNAVHistory.nav_date.asc())
        .all()
    )
    if not all_navs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No NAV history available for this scheme.")

    series = [(r[0], r[1]) for r in all_navs]

    try:
        result = FundAnalyticsService.calculate_sip(
            nav_series=series,
            monthly_amount=sip_req.monthly_amount,
            start_date=sip_req.start_date,
            end_date=sip_req.end_date,
            sip_day=sip_req.sip_day,
        )
        return SIPCalculatorResponse(
            fund_id=str(fund.id),
            scheme_name=fund.scheme_name,
            **result,
            is_demo=fund.is_demo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{fund_id}/lump-sum-calculator", response_model=LumpSumCalculatorResponse)
async def calculate_lump_sum_endpoint(
    fund_id: uuid.UUID,
    req: LumpSumCalculatorRequest,
    db: Session = Depends(get_db),
) -> LumpSumCalculatorResponse:
    """Simulates lump-sum investment growth, absolute returns, and CAGR from historical NAVs."""
    fund = db.query(MutualFund).filter(MutualFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mutual fund '{fund_id}' not found.")

    all_navs = (
        db.query(FundNAVHistory.nav_date, FundNAVHistory.nav)
        .filter(FundNAVHistory.fund_id == fund.id)
        .order_by(FundNAVHistory.nav_date.asc())
        .all()
    )
    if not all_navs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No NAV history available for this scheme.")

    series = [(r[0], r[1]) for r in all_navs]

    try:
        result = FundAnalyticsService.calculate_lump_sum_growth(
            nav_series=series,
            amount=req.amount,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        return LumpSumCalculatorResponse(
            fund_id=str(fund.id),
            scheme_name=fund.scheme_name,
            **result,
            is_demo=fund.is_demo,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_funds_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Seeds synthetic demo Indian mutual funds and historical NAV data (admin/dev only)."""
    _verify_admin_access(current_user)
    stats = seed_demo_mutual_funds(db)
    return {
        "status": "success",
        "message": f"Successfully seeded {stats['funds_created']} mutual funds and {stats['nav_rows_created']} NAV history records.",
        **stats,
    }


@router.post("/ingest/csv")
async def ingest_nav_csv(
    file: UploadFile = File(...),
    fund_id: Optional[uuid.UUID] = Query(None, description="Optional default fund ID for single-fund CSVs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Imports NAV history from uploaded CSV file (admin/dev only)."""
    _verify_admin_access(current_user)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file exceeds 10MB limit.")

    try:
        csv_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UTF-8 encoded text file.")

    valid_rows, errors = FundCSVIngestionService.parse_and_validate_csv(db, csv_str, default_fund_id=fund_id)
    if not valid_rows and errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors[:20]})

    count = FundCSVIngestionService.ingest_nav_records(db, valid_rows, is_demo=False)

    return {
        "status": "success",
        "records_ingested": count,
        "warnings": errors[:10] if errors else [],
    }
