"""
QuantLab Strategy Research, Simulation & Backtesting Engine API Routes.

Implements:
- Strategy definition, parameter validation, and versioned persistence
- Historical bar backtest execution with next-bar Open pricing, fees, and slippage
- Instant (ad-hoc) backtest execution
- Backtest run inspection, trade log analysis, and equity curves
- Multi-run strategy performance comparison
- Parameter grid search experiments with in-sample / out-of-sample train/test splits
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.backtesting import STRATEGY_REGISTRY, BacktestEngine, run_parameter_grid_search
from app.api.deps import get_current_user, get_db
from app.core.rate_limiter import limit_backtest, limit_grid_search
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory
from app.models.quantlab import (
    BacktestEquityPoint,
    BacktestRun,
    BacktestTrade,
    ResearchStrategy,
)
from app.models.user import User
from app.schemas.quantlab import (
    BacktestComparisonItem,
    BacktestComparisonRequest,
    BacktestComparisonResponse,
    BacktestEquityPointResponse,
    BacktestRequest,
    BacktestRunResponse,
    BacktestTradeResponse,
    GridSearchRequest,
    GridSearchResultItem,
    GridSearchResponse,
    InstantBacktestRequest,
    StrategyCreate,
    StrategyResponse,
    StrategyUpdate,
)

router = APIRouter(prefix="/api/v1/quantlab", tags=["quantlab"])


def _as_date(d: Any) -> Any:
    from datetime import date as dt_date
    if isinstance(d, dt_date):
        return d
    if hasattr(d, "date") and callable(getattr(d, "date")):
        return d.date()
    if isinstance(d, str):
        from datetime import datetime
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    return pd.to_datetime(d).date()


def _get_instrument_price_df(
    db: Session,
    instrument_id: uuid.UUID,
    start_date: Any,
    end_date: Any,
) -> tuple[Instrument, pd.DataFrame]:
    """Helper to fetch instrument and price history dataframe for simulation."""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with id '{instrument_id}' not found",
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date range: start_date ({start_date}) cannot be after end_date ({end_date}).",
        )

    records = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.instrument_id == instrument_id,
            PriceHistory.trade_date >= start_date,
            PriceHistory.trade_date <= end_date,
        )
        .order_by(PriceHistory.trade_date.asc())
        .all()
    )

    if len(records) < 2:
        min_bar = (
            db.query(PriceHistory.trade_date)
            .filter(PriceHistory.instrument_id == instrument_id)
            .order_by(PriceHistory.trade_date.asc())
            .first()
        )
        max_bar = (
            db.query(PriceHistory.trade_date)
            .filter(PriceHistory.instrument_id == instrument_id)
            .order_by(PriceHistory.trade_date.desc())
            .first()
        )
        avail_hint = (
            f"Available price history for {instrument.symbol} spans from {min_bar[0]} to {max_bar[0]}."
            if (min_bar and max_bar)
            else f"No historical prices exist for {instrument.symbol}."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient price history for {instrument.symbol} between {start_date} and {end_date} (found {len(records)} bars, minimum 2 required). {avail_hint}",
        )

    df = pd.DataFrame([
        {
            "trade_date": r.trade_date,
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": float(r.volume or 0),
        }
        for r in records
    ])

    return instrument, df


# ==========================================
# 1. Strategy Definition Endpoints (CRUD)
# ==========================================

@router.get("/strategies", response_model=List[StrategyResponse])
def list_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StrategyResponse]:
    """List all research strategies created by the authenticated user."""
    strategies = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.user_id == current_user.id)
        .order_by(ResearchStrategy.created_at.desc())
        .all()
    )
    return [StrategyResponse.model_validate(s) for s in strategies]


@router.post("/strategies", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyResponse:
    """Create a new research strategy with validated parameter configuration."""
    strategy_type = strategy_in.strategy_type.upper().strip()
    if strategy_type not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported strategy_type '{strategy_type}'. Supported: {list(STRATEGY_REGISTRY.keys())}",
        )

    strategy_cls = STRATEGY_REGISTRY[strategy_type]
    try:
        validated_params = strategy_cls.validate_parameters(strategy_in.parameters)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    strategy = ResearchStrategy(
        user_id=current_user.id,
        name=strategy_in.name.strip(),
        description=strategy_in.description,
        strategy_type=strategy_type,
        version=1,
        parameters=validated_params,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return StrategyResponse.model_validate(strategy)


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyResponse:
    """Get single strategy details. Strict user isolation enforced."""
    strategy = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.id == strategy_id, ResearchStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found or access denied",
        )
    return StrategyResponse.model_validate(strategy)


@router.put("/strategies/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: uuid.UUID,
    strategy_in: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StrategyResponse:
    """Update a research strategy. Increments version when parameters change."""
    strategy = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.id == strategy_id, ResearchStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found or access denied",
        )

    if strategy_in.name is not None:
        strategy.name = strategy_in.name.strip()
    if strategy_in.description is not None:
        strategy.description = strategy_in.description
    if strategy_in.parameters is not None:
        strategy_cls = STRATEGY_REGISTRY.get(strategy.strategy_type)
        if strategy_cls:
            try:
                validated_params = strategy_cls.validate_parameters(strategy_in.parameters)
                strategy.parameters = validated_params
                strategy.version += 1
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    strategy.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(strategy)
    return StrategyResponse.model_validate(strategy)


@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a research strategy. Associated backtest runs will set strategy_id to NULL."""
    strategy = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.id == strategy_id, ResearchStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found or access denied",
        )
    db.delete(strategy)
    db.commit()
    return None


# ==========================================
# 2. Backtest Execution Endpoints
# ==========================================

@router.post("/strategies/{strategy_id}/backtest", response_model=BacktestRunResponse, status_code=status.HTTP_201_CREATED)
def run_strategy_backtest(
    strategy_id: uuid.UUID,
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _limit: None = Depends(limit_backtest),
) -> BacktestRunResponse:
    """
    Execute a backtest run on a saved research strategy.
    Simulation guarantees next-bar Open pricing, fees, and slippage.
    """
    strategy = (
        db.query(ResearchStrategy)
        .filter(ResearchStrategy.id == strategy_id, ResearchStrategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found or access denied",
        )

    instrument, df = _get_instrument_price_df(
        db=db,
        instrument_id=request.instrument_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    strategy_cls = STRATEGY_REGISTRY[strategy.strategy_type]
    fingerprint = hashlib.sha256(
        f"{instrument.symbol}_{request.start_date}_{request.end_date}_{len(df)}".encode("utf-8")
    ).hexdigest()[:16]

    started_at = datetime.now(timezone.utc)
    engine_result = BacktestEngine.run_backtest(
        df=df,
        strategy_cls=strategy_cls,
        parameters=strategy.parameters,
        starting_capital=request.starting_capital,
        fee_rate=request.fee_rate,
        slippage_bps=request.slippage_bps,
    )
    completed_at = datetime.now(timezone.utc)

    # Persist BacktestRun
    run = BacktestRun(
        strategy_id=strategy.id,
        user_id=current_user.id,
        instrument_id=instrument.id,
        starting_capital=Decimal(str(request.starting_capital)),
        start_date=request.start_date,
        end_date=request.end_date,
        fee_rate=request.fee_rate,
        slippage_bps=request.slippage_bps,
        status="COMPLETED",
        metrics=engine_result["metrics"],
        dataset_fingerprint=fingerprint,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(run)
    db.flush()  # allocate run.id

    # Persist trades
    for t in engine_result["trades"]:
        sig_d = _as_date(t["signal_date"]) if t.get("signal_date") else _as_date(t["execution_date"])
        exec_d = _as_date(t["execution_date"])
        trade = BacktestTrade(
            run_id=run.id,
            side=t["side"],
            signal_date=sig_d,
            execution_date=exec_d,
            quantity=Decimal(str(t["quantity"])),
            execution_price=Decimal(str(t["execution_price"])),
            fees=Decimal(str(t["fees"])),
            slippage_cost=Decimal(str(t["slippage_cost"])),
            cash_after=Decimal(str(t["cash_after"])),
            position_after=Decimal(str(t["position_after"])),
            realized_pnl=Decimal(str(t["realized_pnl"])) if t["realized_pnl"] is not None else None,
            pnl_pct=Decimal(str(t["pnl_pct"])) if t["pnl_pct"] is not None else None,
        )
        db.add(trade)

    # Persist daily equity curve points
    for pt in engine_result["equity_curve"]:
        eq_point = BacktestEquityPoint(
            run_id=run.id,
            point_date=_as_date(pt["point_date"]),
            equity=Decimal(str(pt["equity"])),
            cash=Decimal(str(pt["cash"])),
            position_value=Decimal(str(pt["position_value"])),
            drawdown_pct=Decimal(str(pt["drawdown_pct"])),
            benchmark_equity=Decimal(str(pt["benchmark_equity"])) if pt.get("benchmark_equity") is not None else None,
        )
        db.add(eq_point)

    db.commit()
    db.refresh(run)

    return BacktestRunResponse(
        id=run.id,
        strategy_id=run.strategy_id,
        user_id=run.user_id,
        instrument_id=run.instrument_id,
        instrument_ticker=instrument.symbol,
        instrument_name=instrument.company_name,
        strategy_name=strategy.name,
        strategy_type=strategy.strategy_type,
        starting_capital=float(run.starting_capital),
        start_date=run.start_date,
        end_date=run.end_date,
        fee_rate=run.fee_rate,
        slippage_bps=run.slippage_bps,
        status=run.status,
        metrics=run.metrics,
        dataset_fingerprint=run.dataset_fingerprint,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


@router.post("/backtest/instant", response_model=BacktestRunResponse, status_code=status.HTTP_201_CREATED)
def run_instant_backtest(
    request: InstantBacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _limit: None = Depends(limit_backtest),
) -> BacktestRunResponse:
    """
    Run an instant ad-hoc strategy simulation without needing a saved strategy record first.
    """
    strategy_type = request.strategy_type.upper().strip()
    if strategy_type not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported strategy_type '{strategy_type}'. Supported: {list(STRATEGY_REGISTRY.keys())}",
        )

    strategy_cls = STRATEGY_REGISTRY[strategy_type]
    try:
        validated_params = strategy_cls.validate_parameters(request.parameters)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    instrument, df = _get_instrument_price_df(
        db=db,
        instrument_id=request.instrument_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    fingerprint = hashlib.sha256(
        f"{instrument.symbol}_{request.start_date}_{request.end_date}_{len(df)}".encode("utf-8")
    ).hexdigest()[:16]

    started_at = datetime.now(timezone.utc)
    engine_result = BacktestEngine.run_backtest(
        df=df,
        strategy_cls=strategy_cls,
        parameters=validated_params,
        starting_capital=request.starting_capital,
        fee_rate=request.fee_rate,
        slippage_bps=request.slippage_bps,
    )
    completed_at = datetime.now(timezone.utc)

    # Persist BacktestRun
    run = BacktestRun(
        strategy_id=None,
        user_id=current_user.id,
        instrument_id=instrument.id,
        starting_capital=Decimal(str(request.starting_capital)),
        start_date=request.start_date,
        end_date=request.end_date,
        fee_rate=request.fee_rate,
        slippage_bps=request.slippage_bps,
        status="COMPLETED",
        metrics=engine_result["metrics"],
        dataset_fingerprint=fingerprint,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(run)
    db.flush()

    # Persist trades
    for t in engine_result["trades"]:
        sig_d = _as_date(t["signal_date"]) if t.get("signal_date") else _as_date(t["execution_date"])
        exec_d = _as_date(t["execution_date"])
        trade = BacktestTrade(
            run_id=run.id,
            side=t["side"],
            signal_date=sig_d,
            execution_date=exec_d,
            quantity=Decimal(str(t["quantity"])),
            execution_price=Decimal(str(t["execution_price"])),
            fees=Decimal(str(t["fees"])),
            slippage_cost=Decimal(str(t["slippage_cost"])),
            cash_after=Decimal(str(t["cash_after"])),
            position_after=Decimal(str(t["position_after"])),
            realized_pnl=Decimal(str(t["realized_pnl"])) if t["realized_pnl"] is not None else None,
            pnl_pct=Decimal(str(t["pnl_pct"])) if t["pnl_pct"] is not None else None,
        )
        db.add(trade)

    # Persist daily equity curve points
    for pt in engine_result["equity_curve"]:
        eq_point = BacktestEquityPoint(
            run_id=run.id,
            point_date=_as_date(pt["point_date"]),
            equity=Decimal(str(pt["equity"])),
            cash=Decimal(str(pt["cash"])),
            position_value=Decimal(str(pt["position_value"])),
            drawdown_pct=Decimal(str(pt["drawdown_pct"])),
            benchmark_equity=Decimal(str(pt["benchmark_equity"])) if pt.get("benchmark_equity") is not None else None,
        )
        db.add(eq_point)

    db.commit()
    db.refresh(run)

    return BacktestRunResponse(
        id=run.id,
        strategy_id=None,
        user_id=run.user_id,
        instrument_id=run.instrument_id,
        instrument_ticker=instrument.symbol,
        instrument_name=instrument.company_name,
        strategy_name=f"{strategy_type} (Instant)",
        strategy_type=strategy_type,
        starting_capital=float(run.starting_capital),
        start_date=run.start_date,
        end_date=run.end_date,
        fee_rate=run.fee_rate,
        slippage_bps=run.slippage_bps,
        status=run.status,
        metrics=run.metrics,
        dataset_fingerprint=run.dataset_fingerprint,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


# ==========================================
# 3. Backtest Runs Inspection Endpoints
# ==========================================

@router.get("/runs", response_model=List[BacktestRunResponse])
def list_backtest_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BacktestRunResponse]:
    """List historical backtest runs executed by the authenticated user."""
    runs = (
        db.query(BacktestRun)
        .filter(BacktestRun.user_id == current_user.id)
        .order_by(BacktestRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for r in runs:
        instrument = db.query(Instrument).filter(Instrument.id == r.instrument_id).first()
        strat = db.query(ResearchStrategy).filter(ResearchStrategy.id == r.strategy_id).first() if r.strategy_id else None

        results.append(
            BacktestRunResponse(
                id=r.id,
                strategy_id=r.strategy_id,
                user_id=r.user_id,
                instrument_id=r.instrument_id,
                instrument_ticker=instrument.symbol if instrument else None,
                instrument_name=instrument.company_name if instrument else None,
                strategy_name=strat.name if strat else "Instant / Ad-hoc",
                strategy_type=strat.strategy_type if strat else "CUSTOM",
                starting_capital=float(r.starting_capital),
                start_date=r.start_date,
                end_date=r.end_date,
                fee_rate=r.fee_rate,
                slippage_bps=r.slippage_bps,
                status=r.status,
                metrics=r.metrics,
                dataset_fingerprint=r.dataset_fingerprint,
                error_message=r.error_message,
                started_at=r.started_at,
                completed_at=r.completed_at,
                created_at=r.created_at,
            )
        )
    return results


@router.get("/runs/{run_id}", response_model=BacktestRunResponse)
def get_backtest_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _limit: None = Depends(limit_backtest),
) -> BacktestRunResponse:
    """Get backtest run metadata and performance metrics summary."""
    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.user_id == current_user.id)
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found or access denied",
        )

    instrument = db.query(Instrument).filter(Instrument.id == run.instrument_id).first()
    strat = db.query(ResearchStrategy).filter(ResearchStrategy.id == run.strategy_id).first() if run.strategy_id else None

    return BacktestRunResponse(
        id=run.id,
        strategy_id=run.strategy_id,
        user_id=run.user_id,
        instrument_id=run.instrument_id,
        instrument_ticker=instrument.symbol if instrument else None,
        instrument_name=instrument.company_name if instrument else None,
        strategy_name=strat.name if strat else "Instant / Ad-hoc",
        strategy_type=strat.strategy_type if strat else "CUSTOM",
        starting_capital=float(run.starting_capital),
        start_date=run.start_date,
        end_date=run.end_date,
        fee_rate=run.fee_rate,
        slippage_bps=run.slippage_bps,
        status=run.status,
        metrics=run.metrics,
        dataset_fingerprint=run.dataset_fingerprint,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


@router.get("/runs/{run_id}/trades", response_model=List[BacktestTradeResponse])
def get_backtest_trades(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BacktestTradeResponse]:
    """Get the full chronological trade log for a backtest run."""
    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.user_id == current_user.id)
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found or access denied",
        )

    trades = (
        db.query(BacktestTrade)
        .filter(BacktestTrade.run_id == run_id)
        .order_by(BacktestTrade.execution_date.asc())
        .all()
    )

    return [
        BacktestTradeResponse(
            id=t.id,
            run_id=t.run_id,
            side=t.side,
            signal_date=t.signal_date,
            execution_date=t.execution_date,
            quantity=float(t.quantity),
            execution_price=float(t.execution_price),
            fees=float(t.fees),
            slippage_cost=float(t.slippage_cost),
            cash_after=float(t.cash_after),
            position_after=float(t.position_after),
            realized_pnl=float(t.realized_pnl) if t.realized_pnl is not None else None,
            pnl_pct=float(t.pnl_pct) if t.pnl_pct is not None else None,
        )
        for t in trades
    ]


@router.get("/runs/{run_id}/equity", response_model=List[BacktestEquityPointResponse])
def get_backtest_equity_curve(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BacktestEquityPointResponse]:
    """Get daily portfolio equity curve and benchmark comparison points."""
    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.user_id == current_user.id)
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found or access denied",
        )

    equity_points = (
        db.query(BacktestEquityPoint)
        .filter(BacktestEquityPoint.run_id == run_id)
        .order_by(BacktestEquityPoint.point_date.asc())
        .all()
    )

    return [
        BacktestEquityPointResponse(
            point_date=pt.point_date,
            equity=float(pt.equity),
            cash=float(pt.cash),
            position_value=float(pt.position_value),
            drawdown_pct=float(pt.drawdown_pct),
            benchmark_equity=float(pt.benchmark_equity) if pt.benchmark_equity is not None else None,
        )
        for pt in equity_points
    ]


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a backtest run and its cascaded trades and equity points."""
    run = (
        db.query(BacktestRun)
        .filter(BacktestRun.id == run_id, BacktestRun.user_id == current_user.id)
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found or access denied",
        )
    db.delete(run)
    db.commit()
    return None


# ==========================================
# 4. Multi-Run Comparison Endpoint
# ==========================================

@router.post("/runs/compare", response_model=BacktestComparisonResponse)
def compare_backtest_runs(
    request: BacktestComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BacktestComparisonResponse:
    """Compare performance across 2 to 5 historical backtest runs."""
    items = []
    for rid in request.run_ids:
        run = (
            db.query(BacktestRun)
            .filter(BacktestRun.id == rid, BacktestRun.user_id == current_user.id)
            .first()
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run '{rid}' not found or does not belong to you",
            )
        inst = db.query(Instrument).filter(Instrument.id == run.instrument_id).first()
        strat = db.query(ResearchStrategy).filter(ResearchStrategy.id == run.strategy_id).first() if run.strategy_id else None

        items.append(
            BacktestComparisonItem(
                run_id=run.id,
                strategy_name=strat.name if strat else "Instant / Ad-hoc",
                strategy_type=strat.strategy_type if strat else "CUSTOM",
                instrument_ticker=inst.symbol if inst else None,
                start_date=run.start_date,
                end_date=run.end_date,
                starting_capital=float(run.starting_capital),
                fee_rate=run.fee_rate,
                slippage_bps=run.slippage_bps,
                metrics=run.metrics,
            )
        )

    return BacktestComparisonResponse(runs=items)


# ==========================================
# 5. Parameter Experiments (Grid Search)
# ==========================================

@router.post("/experiments/grid-search", response_model=GridSearchResponse)
def run_grid_search_experiment(
    request: GridSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _limit: None = Depends(limit_grid_search),
) -> GridSearchResponse:
    """
    Run bounded parameter grid search with train/test (in-sample / out-of-sample) validation.
    Detects overfitting when out-of-sample performance degrades severely vs in-sample.
    """
    strategy_type = request.strategy_type.upper().strip()
    if strategy_type not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported strategy_type '{strategy_type}'. Supported: {list(STRATEGY_REGISTRY.keys())}",
        )

    strategy_cls = STRATEGY_REGISTRY[strategy_type]
    instrument, df = _get_instrument_price_df(
        db=db,
        instrument_id=request.instrument_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if len(df) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least 20 historical bars are required for grid search splitting (found {len(df)}).",
        )

    try:
        raw_result = run_parameter_grid_search(
            df=df,
            strategy_cls=strategy_cls,
            param_grid=request.param_grid,
            starting_capital=request.starting_capital,
            fee_rate=request.fee_rate,
            slippage_bps=request.slippage_bps,
            train_ratio=request.train_ratio,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    formatted_results = [
        GridSearchResultItem(
            params=r["params"],
            in_sample_return_pct=r["in_sample_return_pct"],
            in_sample_sharpe=r["in_sample_sharpe"],
            in_sample_max_dd_pct=r["in_sample_max_dd_pct"],
            out_of_sample_return_pct=r["out_of_sample_return_pct"],
            out_of_sample_sharpe=r["out_of_sample_sharpe"],
            out_of_sample_max_dd_pct=r["out_of_sample_max_dd_pct"],
            overfitting_warning=r["overfitting_warning"],
            status=r["status"],
            error_message=r["error_message"],
        )
        for r in raw_result["results"]
    ]

    return GridSearchResponse(
        strategy_type=strategy_type,
        instrument_id=instrument.id,
        combinations_tested=raw_result["combinations_tested"],
        results=formatted_results,
        best_params=raw_result["best_params"],
        summary=raw_result["summary"],
    )
