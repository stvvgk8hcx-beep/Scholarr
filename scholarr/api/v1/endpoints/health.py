"""Health Check endpoint with comprehensive system status."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.health import HealthCheckResponse, HealthStatusResponse
from scholarr.services.health_service import HealthService

router = APIRouter()


@router.get("", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Run all health checks and return results."""
    service = HealthService(db)
    health_status = await service.run_health_checks()
    return health_status


@router.get("/status", response_model=HealthStatusResponse)
async def system_status(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get detailed system status including db, disk space, version, scheduler, errors."""
    service = HealthService(db)
    status = await service.get_detailed_status()
    return status
