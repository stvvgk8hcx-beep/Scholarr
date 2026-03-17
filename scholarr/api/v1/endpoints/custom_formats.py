"""Custom Formats endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.custom_format import (
    CustomFormatCreate,
    CustomFormatUpdate,
    CustomFormatResponse,
)
from scholarr.services.custom_format_service import CustomFormatService

router = APIRouter()


@router.get("", response_model=list[CustomFormatResponse])
async def list_custom_formats(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all custom formats."""
    service = CustomFormatService(db)
    formats = await service.list_custom_formats()
    return formats


@router.get("/{id}", response_model=CustomFormatResponse)
async def get_custom_format(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a custom format by ID."""
    service = CustomFormatService(db)
    format = await service.get_custom_format(id)
    if not format:
        raise HTTPException(status_code=404, detail="Custom format not found")
    return format


@router.post("", response_model=CustomFormatResponse, status_code=201)
async def create_custom_format(
    format: CustomFormatCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new custom format."""
    service = CustomFormatService(db)
    new_format = await service.create_custom_format(format)
    return new_format


@router.put("/{id}", response_model=CustomFormatResponse)
async def update_custom_format(
    id: int,
    format_update: CustomFormatUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a custom format."""
    service = CustomFormatService(db)
    updated = await service.update_custom_format(id, format_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Custom format not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_custom_format(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a custom format."""
    service = CustomFormatService(db)
    success = await service.delete_custom_format(id)
    if not success:
        raise HTTPException(status_code=404, detail="Custom format not found")
    return None
