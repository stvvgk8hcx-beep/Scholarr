"""Managed Files endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.managed_file import (
    ManagedFileCreate,
    ManagedFileUpdate,
    ManagedFileResponse,
)
from scholarr.services.managed_file_service import ManagedFileService

router = APIRouter()


@router.get("", response_model=list[ManagedFileResponse])
async def list_managed_files(
    academic_item_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List managed files with optional filtering."""
    service = ManagedFileService(db)
    files = await service.list_managed_files(academic_item_id=academic_item_id)
    return files


@router.get("/{id}", response_model=ManagedFileResponse)
async def get_managed_file(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a managed file by ID."""
    service = ManagedFileService(db)
    file = await service.get_managed_file(id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.post("", response_model=ManagedFileResponse, status_code=201)
async def create_managed_file(
    file: ManagedFileCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new managed file entry."""
    service = ManagedFileService(db)
    new_file = await service.create_managed_file(file)
    return new_file


@router.put("/{id}", response_model=ManagedFileResponse)
async def update_managed_file(
    id: int,
    file_update: ManagedFileUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a managed file."""
    service = ManagedFileService(db)
    updated = await service.update_managed_file(id, file_update)
    if not updated:
        raise HTTPException(status_code=404, detail="File not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_managed_file(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a managed file entry."""
    service = ManagedFileService(db)
    success = await service.delete_managed_file(id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return None
