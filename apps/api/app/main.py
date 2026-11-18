from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import SessionLocal, check_db_health
from app.core.logging import logger
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.instruments import router as instruments_router
from app.api.routes.portfolios import router as portfolios_router
from app.api.routes.funds import router as funds_router
from app.api.routes.market import router as market_router
from app.api.routes.quantlab import router as quantlab_router
from app.api.routes.ai import router as ai_router
from app.services.ingestion import seed_demo_market_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.environment}]")
    logger.info(f"Demo Mode: {settings.demo_mode}")

    # In demo mode, automatically seed market data if database is reachable (skip during testing)
    if settings.environment != "testing":
        db_ok, _ = check_db_health()
        if db_ok and settings.demo_mode:
            try:
                db = SessionLocal()
                from app.models.instrument import Instrument
                from app.models.financial_statement import FinancialStatement
                from app.providers.financial_fixtures import seed_demo_financial_statements
                if db.query(Instrument).count() == 0:
                    logger.info("Database has no instruments. Seeding demo Indian equities...")
                    seed_demo_market_data(db)
                    logger.info("Demo market data seeded successfully.")
                if db.query(FinancialStatement).count() == 0:
                    logger.info("Database has no financial statements. Seeding demo financial statements...")
                    seed_demo_financial_statements(db)
                    logger.info("Demo financial statements seeded successfully.")
                from app.models.mutual_fund import MutualFund
                from app.providers.fund_fixtures import seed_demo_mutual_funds
                if db.query(MutualFund).count() == 0:
                    logger.info("Database has no mutual funds. Seeding demo Indian mutual funds...")
                    seed_demo_mutual_funds(db)
                    logger.info("Demo mutual funds seeded successfully.")
                from app.models.market import NewsArticle
                from app.services.news_ingestion import NewsIngestionService
                if db.query(NewsArticle).count() == 0:
                    logger.info("Database has no news articles. Seeding demo MarketPulse data...")
                    NewsIngestionService.seed_demo_market_pulse(db)
                    logger.info("Demo MarketPulse data seeded successfully.")
                db.close()
            except Exception as seed_err:
                logger.warning(f"Could not auto-seed demo data: {seed_err}")

    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Educational financial intelligence, portfolio analytics, and quantitative research platform API.",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# Exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(instruments_router)
app.include_router(portfolios_router)
app.include_router(funds_router)
app.include_router(market_router)
app.include_router(quantlab_router)
app.include_router(ai_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "mode": "demo" if settings.demo_mode else "live",
    }
