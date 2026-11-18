from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Returns application health and database connection status."""
    db_ok, db_msg = check_db_health()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        service="quantweave-api",
        environment=settings.environment,
        demo_mode=settings.demo_mode,
        database="connected" if db_ok else f"unavailable: {db_msg}",
        version=settings.app_version,
    )
