"""Mass Editor endpoint for bulk operations."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.services.mass_editor_service import MassEditorService

router = APIRouter()


class BulkCourseUpdate(BaseModel):
    """Schema for bulk course updates."""

    course_ids: List[int] = Field(..., min_length=1)
    semester_id: Optional[int] = None
    root_folder_id: Optional[int] = None
    monitored: Optional[bool] = None
    tags: Optional[List[int]] = None


class BulkCourseUpdateResponse(BaseModel):
    """Response for bulk course updates."""

    updated_count: int
    failed_count: int
    errors: Optional[List[dict]] = None


class BulkAcademicItemUpdate(BaseModel):
    """Schema for bulk academic item updates."""

    item_ids: List[int] = Field(..., min_length=1)
    status: Optional[str] = None
    type: Optional[str] = None
    course_id: Optional[int] = None


class BulkAcademicItemUpdateResponse(BaseModel):
    """Response for bulk academic item updates."""

    updated_count: int
    failed_count: int
    errors: Optional[List[dict]] = None


@router.post("/courses", response_model=BulkCourseUpdateResponse, status_code=200)
async def bulk_update_courses(
    request: BulkCourseUpdate = Body(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Bulk update courses with specified fields."""
    service = MassEditorService(db)
    result = await service.bulk_update_courses(request)
    return result


@router.post("/academic-items", response_model=BulkAcademicItemUpdateResponse, status_code=200)
async def bulk_update_academic_items(
    request: BulkAcademicItemUpdate = Body(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Bulk update academic items with specified fields."""
    service = MassEditorService(db)
    result = await service.bulk_update_academic_items(request)
    return result
