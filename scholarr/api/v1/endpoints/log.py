"""Logs endpoint for viewing application logs."""


from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.log import LogListResponse
from scholarr.services.log_service import LogService

router = APIRouter()


@router.get("", response_model=LogListResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    level: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get application logs with pagination and filtering by level/search text."""
    service = LogService(db)
    result = await service.get_logs(page=page, page_size=page_size, level=level, search=search)
    return result


@router.get("/file")
async def download_log_file(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Download the current log file."""
    service = LogService(db)
    file_path = await service.get_log_file_path()
    if not file_path:
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(file_path, filename="scholarr.log", media_type="text/plain")
