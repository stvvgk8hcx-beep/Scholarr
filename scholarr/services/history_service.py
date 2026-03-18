"""History service for business logic."""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import HistoryEntry

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for history operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_history(
        self,
        page: int,
        page_size: int,
        event_type: str | None = None,
        course_id: int | None = None,
    ) -> dict:
        """Get history entries with pagination and filtering."""
        offset = (page - 1) * page_size

        count_q = select(func.count()).select_from(HistoryEntry)
        data_q = select(HistoryEntry)

        if event_type:
            count_q = count_q.where(HistoryEntry.event_type == event_type)
            data_q = data_q.where(HistoryEntry.event_type == event_type)

        if course_id is not None:
            count_q = count_q.where(HistoryEntry.course_id == course_id)
            data_q = data_q.where(HistoryEntry.course_id == course_id)

        total = (await self.db.execute(count_q)).scalar_one()
        rows = (
            await self.db.execute(
                data_q.order_by(HistoryEntry.date.desc()).offset(offset).limit(page_size)
            )
        ).scalars().all()

        return {
            "items": list(rows),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
