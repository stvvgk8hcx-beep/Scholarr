"""Semesters endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.semester import SemesterCreate, SemesterUpdate, SemesterResponse
from scholarr.services.semester_service import SemesterService

router = APIRouter()


@router.get("", response_model=list[SemesterResponse])
async def list_semesters(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all semesters."""
    service = SemesterService(db)
    semesters = await service.list_semesters()
    return semesters


@router.get("/{id}", response_model=SemesterResponse)
async def get_semester(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a semester by ID."""
    service = SemesterService(db)
    semester = await service.get_semester(id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester


@router.post("", response_model=SemesterResponse, status_code=201)
async def create_semester(
    semester: SemesterCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new semester."""
    service = SemesterService(db)
    new_semester = await service.create_semester(semester)
    return new_semester


@router.put("/{id}", response_model=SemesterResponse)
async def update_semester(
    id: int,
    semester_update: SemesterUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a semester."""
    service = SemesterService(db)
    updated = await service.update_semester(id, semester_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Semester not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_semester(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a semester."""
    service = SemesterService(db)
    success = await service.delete_semester(id)
    if not success:
        raise HTTPException(status_code=404, detail="Semester not found")
    return None
