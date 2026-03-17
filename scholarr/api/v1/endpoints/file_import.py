"""Auto File Import endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.import_result import ImportResultResponse
from scholarr.services.import_service import ImportService

router = APIRouter()


@router.post("/trigger", response_model=ImportResultResponse, status_code=202)
async def trigger_auto_import(
    root_folder_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Trigger auto-import from a root folder."""
    service = ImportService(db)
    result = await service.trigger_auto_import(root_folder_id)
    return result
