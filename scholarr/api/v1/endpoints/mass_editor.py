"""Mass Editor endpoint for bulk operations."""


from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.services.mass_editor_service import MassEditorService

router = APIRouter()


class BulkCourseUpdate(BaseModel):
    """Schema for bulk course updates."""

    course_ids: list[int] = Field(..., min_length=1)
    semester_id: int | None = None
    root_folder_id: int | None = None
    monitored: bool | None = None
    tags: list[int] | None = None


class BulkCourseUpdateResponse(BaseModel):
    """Response for bulk course updates."""

    updated_count: int
    failed_count: int
    errors: list[dict] | None = None


class BulkAcademicItemUpdate(BaseModel):
    """Schema for bulk academic item updates."""

    item_ids: list[int] = Field(..., min_length=1)
    status: str | None = None
    type: str | None = None
    course_id: int | None = None


class BulkAcademicItemUpdateResponse(BaseModel):
    """Response for bulk academic item updates."""

    updated_count: int
    failed_count: int
    errors: list[dict] | None = None


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
