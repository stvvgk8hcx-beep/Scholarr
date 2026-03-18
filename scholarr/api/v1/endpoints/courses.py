"""Courses endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.course import CourseCreate, CourseListResponse, CourseResponse, CourseUpdate
from scholarr.services.course_service import CourseService

router = APIRouter()


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    semester_id: int | None = Query(None),
    monitored: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all courses with optional filtering."""
    service = CourseService(db)
    return await service.list_courses(
        semester_id=semester_id, monitored=monitored, search=search
    )


@router.get("/paged", response_model=CourseListResponse)
async def list_courses_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_key: str = Query("name"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    semester_id: int | None = Query(None),
    monitored: bool | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List courses with pagination and full filtering support."""
    service = CourseService(db)
    return await service.list_courses_paginated(
        page=page,
        page_size=page_size,
        sort_key=sort_key,
        sort_dir=sort_dir,
        semester_id=semester_id,
        monitored=monitored,
        search=search,
    )


@router.get("/{id}", response_model=CourseResponse)
async def get_course(
    id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a course by ID."""
    service = CourseService(db)
    course = await service.get_course(id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new course."""
    service = CourseService(db)
    try:
        return await service.create_course(course)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.put("/{id}", response_model=CourseResponse)
async def update_course(
    id: Annotated[int, Path(ge=1)],
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a course."""
    service = CourseService(db)
    updated = await service.update_course(id, course_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_course(
    id: Annotated[int, Path(ge=1)],
    delete_files: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a course."""
    service = CourseService(db)
    success = await service.delete_course(id, delete_files=delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return None
