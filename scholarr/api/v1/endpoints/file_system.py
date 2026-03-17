"""File System endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.file_system import DirectoryEntryResponse
from scholarr.services.file_system_service import FileSystemService

router = APIRouter()


@router.get("/browse", response_model=list[DirectoryEntryResponse])
async def browse_directory(
    path: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Browse a directory in the file system."""
    service = FileSystemService(db)
    entries = await service.browse_directory(path)
    return entries
