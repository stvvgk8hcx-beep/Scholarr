"""System Information endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.system import SystemStatusResponse
from scholarr.services.system_service import SystemService

router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get system status including uptime, version, database size, and file count."""
    service = SystemService(db)
    status = await service.get_system_status()
    return status
