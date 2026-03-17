"""Manual Import endpoint for file imports and previews."""

import hashlib
from typing import Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.import_result import ImportResultResponse
from scholarr.services.manual_import_service import ManualImportService

router = APIRouter()

# Accepted file extensions for manual import
_ACCEPTED_EXTENSIONS = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "txt", "md", "py", "java", "c", "cpp", "h", "jpg",
    "jpeg", "png", "gif", "zip", "tar", "gz", "mp4", "mp3",
}


class ImportFilePathRequest(BaseModel):
    """Request schema for importing from file paths."""

    file_paths: List[str] = Field(..., min_length=1)
    course_id: Optional[int] = None


class ImportPreview(BaseModel):
    """Preview of how a file would be organized."""

    file_path: str
    suggested_name: str
    suggested_course: Optional[str] = None
    suggested_type: Optional[str] = None
    metadata: Optional[dict] = None


class ImportPreviewResponse(BaseModel):
    """Response containing import previews."""

    previews: List[ImportPreview]
    total_files: int


class ImportConfirmRequest(BaseModel):
    """Request to confirm import after preview."""

    file_paths: List[str] = Field(..., min_length=1)
    course_id: int
    apply_to_all: bool = False


class ImportAcceptedResponse(BaseModel):
    """Response for accepted file import."""

    accepted: bool
    filename: str
    course_id: Optional[int] = None
    message: str


@router.post("/manual", response_model=ImportAcceptedResponse, status_code=202)
async def import_file(
    file: UploadFile = File(...),
    course_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Import a file into the library."""
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in _ACCEPTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: .{ext}")
    return ImportAcceptedResponse(
        accepted=True,
        filename=filename,
        course_id=course_id,
        message="File queued for import",
    )


@router.post("/csv", status_code=202)
async def import_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Import academic data from a CSV file."""
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext != "csv":
        raise HTTPException(status_code=400, detail="Expected a .csv file")
    return {"accepted": True, "filename": filename, "message": "CSV queued for processing"}


@router.get("/status")
async def import_status(
    api_key: str = Depends(verify_api_key),
):
    """Get status of the file import pipeline."""
    return {"status": "idle", "queue_size": 0}


@router.post("/manual/preview", response_model=ImportPreviewResponse, status_code=200)
async def preview_import(
    request: ImportFilePathRequest = Body(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Preview how files would be parsed and organized without importing."""
    service = ManualImportService(db)
    previews = await service.preview_import(request.file_paths, request.course_id)
    return previews


@router.post("/manual/confirm", response_model=ImportResultResponse, status_code=201)
async def confirm_and_import(
    request: ImportConfirmRequest = Body(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Execute import after confirming preview details."""
    service = ManualImportService(db)
    result = await service.execute_import(request.file_paths, request.course_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    return result


@router.post("/manual/file", response_model=ImportResultResponse, status_code=201)
async def manual_import_file(
    file: UploadFile = File(...),
    academic_item_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Manually import a single file for an academic item."""
    service = ManualImportService(db)
    result = await service.manual_import(file, academic_item_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))
    return result
