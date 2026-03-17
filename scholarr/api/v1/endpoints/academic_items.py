"""Academic Items endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.academic_item import (
    AcademicItemCreate,
    AcademicItemUpdate,
    AcademicItemResponse,
    AcademicItemListResponse,
)
from scholarr.services.academic_item_service import AcademicItemService

router = APIRouter()


@router.get("", response_model=list[AcademicItemResponse])
async def list_academic_items(
    course_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List academic items with optional filtering."""
    service = AcademicItemService(db)
    items = await service.list_academic_items(
        course_id=course_id, status=status, type=type, overdue=overdue
    )
    return items


@router.get("/paged", response_model=AcademicItemListResponse)
async def list_academic_items_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_key: str = Query("due_date"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List academic items with pagination."""
    service = AcademicItemService(db)
    result = await service.list_academic_items_paginated(
        page=page, page_size=page_size, sort_key=sort_key, sort_dir=sort_dir
    )
    return result


@router.get("/upcoming", response_model=list[AcademicItemResponse])
async def get_upcoming_deadlines(
    days: int = Query(7, ge=1),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get upcoming deadlines within specified number of days."""
    service = AcademicItemService(db)
    items = await service.get_upcoming_deadlines(days=days)
    return items


@router.get("/{id}", response_model=AcademicItemResponse)
async def get_academic_item(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get an academic item by ID."""
    service = AcademicItemService(db)
    item = await service.get_academic_item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Academic item not found")
    return item


@router.post("", response_model=AcademicItemResponse, status_code=201)
async def create_academic_item(
    item: AcademicItemCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new academic item."""
    service = AcademicItemService(db)
    new_item = await service.create_academic_item(item)
    return new_item


@router.put("/{id}", response_model=AcademicItemResponse)
async def update_academic_item(
    id: int,
    item_update: AcademicItemUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update an academic item."""
    service = AcademicItemService(db)
    updated = await service.update_academic_item(id, item_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Academic item not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_academic_item(
    id: int,
    delete_files: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete an academic item."""
    service = AcademicItemService(db)
    success = await service.delete_academic_item(id, delete_files=delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Academic item not found")
    return None
