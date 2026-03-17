"""Notes endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from scholarr.services.note_service import NoteService

router = APIRouter()


@router.get("", response_model=NoteListResponse)
async def list_notes(
    course_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List notes with optional course filter and search."""
    service = NoteService(db)
    return await service.list_notes(course_id=course_id, search=search, page=page, page_size=page_size)


@router.get("/{id}", response_model=NoteResponse)
async def get_note(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a note by ID."""
    service = NoteService(db)
    note = await service.get_note(id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new note."""
    service = NoteService(db)
    return await service.create_note(data)


@router.put("/{id}", response_model=NoteResponse)
async def update_note(
    id: int,
    data: NoteUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a note."""
    service = NoteService(db)
    updated = await service.update_note(id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_note(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a note."""
    service = NoteService(db)
    if not await service.delete_note(id):
        raise HTTPException(status_code=404, detail="Note not found")
    return None


@router.post("/{id}/beacon", status_code=204)
async def beacon_save(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Save note via sendBeacon (no API key required, POST with JSON body)."""
    try:
        body = await request.json()
        data = NoteUpdate(**body)
        service = NoteService(db)
        await service.update_note(id, data)
    except Exception:
        pass  # beacon saves are best-effort
    return None


@router.get("/{id}/backups")
async def list_note_backups(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List backup snapshots for a note."""
    service = NoteService(db)
    return await service.list_backups(id)


@router.post("/{id}/backups/{backup_id}/restore", response_model=NoteResponse)
async def restore_note_backup(
    id: int,
    backup_id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Restore a note from a backup snapshot."""
    service = NoteService(db)
    result = await service.restore_backup(id, backup_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backup not found")
    return result
