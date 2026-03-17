"""History service for business logic."""

import logging
from typing import Optional
from sqlalchemy import select, func
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
        action_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        course_id: Optional[int] = None,
    ) -> dict:
        """Get history entries with pagination and filtering."""
        offset = (page - 1) * page_size

        count_q = select(func.count()).select_from(HistoryEntry)
        data_q = select(HistoryEntry)

        if action_type or entity_type:
            # event_type filter (action_type and entity_type both map to event_type)
            filter_val = action_type or entity_type
            count_q = count_q.where(HistoryEntry.event_type == filter_val)
            data_q = data_q.where(HistoryEntry.event_type == filter_val)

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
