"""Naming Configuration endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.naming_config import NamingConfigResponse, NamingConfigUpdate
from scholarr.services.naming_service import NamingService

router = APIRouter()


@router.get("", response_model=NamingConfigResponse)
async def get_naming_config(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get the naming configuration (singleton)."""
    service = NamingService(db)
    config = await service.get_naming_config()
    if not config:
        raise HTTPException(status_code=404, detail="Naming configuration not found")
    return config


@router.put("", response_model=NamingConfigResponse)
async def update_naming_config(
    config_update: NamingConfigUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update the naming configuration."""
    service = NamingService(db)
    updated = await service.update_naming_config(config_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Naming configuration not found")
    return updated
