"""Backup and restore endpoints."""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Path
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.backup import BackupResponse, BackupRestoreResponse, BackupListResponse
from scholarr.services.backup_service import BackupService

router = APIRouter()


@router.get("", response_model=BackupListResponse)
async def list_backups(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all available backups with metadata."""
    service = BackupService(db)
    backups = await service.list_backups()
    return backups


@router.post("", response_model=BackupResponse, status_code=201)
async def create_backup(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new backup (database dump + config files)."""
    service = BackupService(db)
    backup = await service.create_backup()
    return backup


@router.post("/{backup_id}/restore", response_model=BackupRestoreResponse, status_code=200)
async def restore_backup(
    backup_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Restore database and config from an existing backup."""
    service = BackupService(db)
    result = await service.restore_backup(backup_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Restore failed"))
    return result


@router.delete("/{backup_id}", status_code=204)
async def delete_backup(
    backup_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a backup by ID."""
    service = BackupService(db)
    success = await service.delete_backup(backup_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")
    return None
