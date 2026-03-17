"""Host Configuration endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.host_config import HostConfigResponse, HostConfigUpdate
from scholarr.services.host_config_service import HostConfigService

router = APIRouter()


@router.get("", response_model=HostConfigResponse)
async def get_host_config(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get the application configuration."""
    service = HostConfigService(db)
    config = await service.get_host_config()
    return config


@router.put("", response_model=HostConfigResponse)
async def update_host_config(
    config_update: HostConfigUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update the application configuration."""
    service = HostConfigService(db)
    updated = await service.update_host_config(config_update)
    return updated
