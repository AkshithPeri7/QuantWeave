"""
Portfolio Intelligence API Endpoints for QuantWeave.

Implements:
- Multi-portfolio management for authenticated users
- Append-only transaction entry (BUY, SELL, DIVIDEND, CASH_DEPOSIT, CASH_WITHDRAWAL)
- Strict cross-user portfolio isolation and ownership verification
- Current portfolio valuation with WACB cost basis & P&L
- Asset and sector diversification breakdown
- Performance & risk metrics (TWR, XIRR, Volatility, Sharpe, Drawdown)
- Daily historical equity curve timeline
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics.portfolio_analytics import PortfolioAnalyticsService
from app.api.deps import get_current_user, get_db
from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.models.portfolio_transaction import PortfolioTransaction
from app.models.user import User
from app.schemas.portfolio import (
    EquityPointResponse,
    PortfolioCreate,
    PortfolioPerformanceResponse,
    PortfolioResponse,
    PortfolioValuationResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.portfolio import (
    DuplicateTransactionError,
    InsufficientCashError,
    InsufficientSharesError,
    PortfolioNotFoundError,
    PortfolioService,
    UnsupportedCurrencyError,
)

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


def _verify_portfolio_access(db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Portfolio:
    """Verifies that the portfolio exists and belongs to the authenticated user."""
    portfolio = PortfolioService.get_portfolio_for_user(db, portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or access denied",
        )
    return portfolio


@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[PortfolioResponse]:
    """Retrieves all portfolios owned by the authenticated user."""
    portfolios = PortfolioService.get_user_portfolios(db, current_user.id)
    return [PortfolioResponse.model_validate(p) for p in portfolios]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    """Creates a new INR portfolio for the authenticated user."""
    try:
        portfolio = PortfolioService.create_portfolio(
            db=db,
            user_id=current_user.id,
            name=portfolio_in.name,
            description=portfolio_in.description,
            base_currency=portfolio_in.base_currency,
        )
        return PortfolioResponse.model_validate(portfolio)
    except UnsupportedCurrencyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioResponse:
    """Retrieves portfolio details by ID with ownership enforcement."""
    portfolio = _verify_portfolio_access(db, portfolio_id, current_user.id)
    return PortfolioResponse.model_validate(portfolio)


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def record_transaction(
    portfolio_id: uuid.UUID,
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Records an auditable transaction into the portfolio ledger.
    Atomically verifies cash sufficiency, prevents overselling, and checks idempotency.
    """
    _verify_portfolio_access(db, portfolio_id, current_user.id)

    try:
        tx = PortfolioService.record_transaction(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            transaction_type=tx_in.transaction_type,
            trade_date=tx_in.trade_date,
            quantity=tx_in.quantity,
            price_per_unit=tx_in.price_per_unit,
            fees=tx_in.fees,
            instrument_id=tx_in.instrument_id,
            notes=tx_in.notes,
            idempotency_key=tx_in.idempotency_key,
        )

        resp = TransactionResponse.model_validate(tx)
        if tx.instrument_id:
            inst = db.query(Instrument).filter(Instrument.id == tx.instrument_id).first()
            if inst:
                resp.instrument_symbol = inst.symbol
                resp.instrument_name = inst.company_name
        return resp

    except DuplicateTransactionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except (InsufficientCashError, InsufficientSharesError, UnsupportedCurrencyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    portfolio_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """Retrieves chronological transaction ledger entries for the portfolio."""
    _verify_portfolio_access(db, portfolio_id, current_user.id)

    txs = (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.portfolio_id == portfolio_id)
        .order_by(
            PortfolioTransaction.trade_date.desc(),
            PortfolioTransaction.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    inst_ids = {tx.instrument_id for tx in txs if tx.instrument_id}
    inst_map = {}
    if inst_ids:
        inst_records = db.query(Instrument).filter(Instrument.id.in_(inst_ids)).all()
        inst_map = {inst.id: inst for inst in inst_records}

    results = []
    for tx in txs:
        resp = TransactionResponse.model_validate(tx)
        if tx.instrument_id and tx.instrument_id in inst_map:
            inst = inst_map[tx.instrument_id]
            resp.instrument_symbol = inst.symbol
            resp.instrument_name = inst.company_name
        results.append(resp)

    return results


@router.get("/{portfolio_id}/valuation", response_model=PortfolioValuationResponse)
async def get_portfolio_valuation(
    portfolio_id: uuid.UUID,
    as_of_date: Optional[date] = Query(default=None, description="Valuation cutoff date (defaults to today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioValuationResponse:
    """Calculates comprehensive portfolio valuation, holdings, and sector allocations."""
    portfolio = _verify_portfolio_access(db, portfolio_id, current_user.id)
    val_data = PortfolioAnalyticsService.get_portfolio_valuation(db, portfolio, as_of_date)
    return PortfolioValuationResponse(**val_data)


@router.get("/{portfolio_id}/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(
    portfolio_id: uuid.UUID,
    as_of_date: Optional[date] = Query(default=None, description="Valuation cutoff date (defaults to today)"),
    risk_free_rate: float = Query(default=0.06, ge=0.0, le=1.0, description="Annualized risk-free rate (e.g. 0.06 for 6%)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioPerformanceResponse:
    """Calculates TWR, XIRR, Annualized Volatility, Sharpe Ratio, and Maximum Drawdown."""
    portfolio = _verify_portfolio_access(db, portfolio_id, current_user.id)
    perf_data = PortfolioAnalyticsService.calculate_performance_and_risk(
        db, portfolio, as_of_date, risk_free_rate=Decimal(str(risk_free_rate))
    )
    return PortfolioPerformanceResponse(**perf_data)


@router.get("/{portfolio_id}/history", response_model=List[EquityPointResponse])
async def get_portfolio_history(
    portfolio_id: uuid.UUID,
    as_of_date: Optional[date] = Query(default=None, description="Valuation cutoff date (defaults to today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[EquityPointResponse]:
    """Retrieves daily equity curve timeline points for interactive charts."""
    portfolio = _verify_portfolio_access(db, portfolio_id, current_user.id)
    history = PortfolioAnalyticsService.get_historical_equity_curve(db, portfolio, as_of_date)
    return [EquityPointResponse(**item) for item in history]
