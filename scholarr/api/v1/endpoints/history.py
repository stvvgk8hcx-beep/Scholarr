"""History endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.history import HistoryEntryResponse, HistoryListResponse
from scholarr.services.history_service import HistoryService

router = APIRouter()


@router.get("", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get history entries with pagination and filtering."""
    service = HistoryService(db)
    result = await service.get_history(
        page=page,
        page_size=page_size,
        action_type=action_type,
        entity_type=entity_type,
        course_id=course_id,
    )
    return result
