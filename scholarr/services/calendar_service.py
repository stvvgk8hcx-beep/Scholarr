"""Calendar service for business logic."""

import logging
from collections import defaultdict
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from scholarr.db.models import AcademicItem, Course
from scholarr.schemas.calendar import CalendarDayResponse, CalendarItemInfo

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_calendar_entries(
        self, start_date: date, end_date: date
    ) -> list[CalendarDayResponse]:
        """Get due dates for a date range, grouped by day."""
        # Convert date boundaries to datetime for comparison with the DateTime column
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        query = (
            select(AcademicItem)
            .join(Course, AcademicItem.course_id == Course.id)
            .options(joinedload(AcademicItem.course))
            .where(
                AcademicItem.due_date >= start_dt,
                AcademicItem.due_date <= end_dt,
            )
            .order_by(AcademicItem.due_date.asc())
        )

        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        # Group items by date
        days: dict[date, list[CalendarItemInfo]] = defaultdict(list)
        for item in items:
            due_day = item.due_date.date()
            days[due_day].append(
                CalendarItemInfo(
                    id=item.id,
                    title=item.name,
                    type=item.type.value if item.type else "",
                    course_id=item.course_id,
                    status=item.status.value if item.status else "",
                )
            )

        # Build the response sorted by date
        return [
            CalendarDayResponse(
                date=day,
                items=day_items,
                item_count=len(day_items),
            )
            for day, day_items in sorted(days.items())
        ]
