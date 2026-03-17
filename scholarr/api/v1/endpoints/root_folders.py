"""Root Folders endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.root_folder import (
    RootFolderCreate,
    RootFolderUpdate,
    RootFolderResponse,
)
from scholarr.services.root_folder_service import RootFolderService

router = APIRouter()


@router.get("", response_model=list[RootFolderResponse])
async def list_root_folders(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all root folders with disk space info."""
    service = RootFolderService(db)
    folders = await service.list_root_folders_with_info()
    return folders


@router.get("/{id}", response_model=RootFolderResponse)
async def get_root_folder(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a root folder by ID with disk space info."""
    service = RootFolderService(db)
    folder = await service.get_root_folder_with_info(id)
    if not folder:
        raise HTTPException(status_code=404, detail="Root folder not found")
    return folder


@router.post("", response_model=RootFolderResponse, status_code=201)
async def create_root_folder(
    folder: RootFolderCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new root folder."""
    service = RootFolderService(db)
    new_folder = await service.create_root_folder(folder)
    return new_folder


@router.put("/{id}", response_model=RootFolderResponse)
async def update_root_folder(
    id: int,
    folder_update: RootFolderUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a root folder."""
    service = RootFolderService(db)
    updated = await service.update_root_folder(id, folder_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Root folder not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_root_folder(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a root folder."""
    service = RootFolderService(db)
    success = await service.delete_root_folder(id)
    if not success:
        raise HTTPException(status_code=404, detail="Root folder not found")
    return None
