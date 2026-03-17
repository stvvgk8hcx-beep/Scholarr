"""Queue status endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.queue import QueueStatusResponse
from scholarr.services.queue_service import QueueService

router = APIRouter()


@router.get("/status", response_model=QueueStatusResponse)
async def get_queue_status(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get current queue status."""
    service = QueueService(db)
    status = await service.get_queue_status()
    return status
