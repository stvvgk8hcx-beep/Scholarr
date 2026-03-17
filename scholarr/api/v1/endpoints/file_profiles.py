"""File Profiles endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.file_profile import (
    FileProfileCreate,
    FileProfileUpdate,
    FileProfileResponse,
)
from scholarr.services.file_profile_service import FileProfileService

router = APIRouter()


@router.get("", response_model=list[FileProfileResponse])
async def list_file_profiles(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all file profiles."""
    service = FileProfileService(db)
    profiles = await service.list_file_profiles()
    return profiles


@router.get("/{id}", response_model=FileProfileResponse)
async def get_file_profile(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a file profile by ID."""
    service = FileProfileService(db)
    profile = await service.get_file_profile(id)
    if not profile:
        raise HTTPException(status_code=404, detail="File profile not found")
    return profile


@router.post("", response_model=FileProfileResponse, status_code=201)
async def create_file_profile(
    profile: FileProfileCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new file profile."""
    service = FileProfileService(db)
    new_profile = await service.create_file_profile(profile)
    return new_profile


@router.put("/{id}", response_model=FileProfileResponse)
async def update_file_profile(
    id: int,
    profile_update: FileProfileUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a file profile."""
    service = FileProfileService(db)
    updated = await service.update_file_profile(id, profile_update)
    if not updated:
        raise HTTPException(status_code=404, detail="File profile not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_file_profile(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a file profile."""
    service = FileProfileService(db)
    success = await service.delete_file_profile(id)
    if not success:
        raise HTTPException(status_code=404, detail="File profile not found")
    return None
