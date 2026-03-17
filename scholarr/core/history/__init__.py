"""History tracking service for Scholarr."""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.courses import PaginatedResult
from scholarr.core.exceptions import NotFoundError, ValidationError


class HistoryService:
    """Service for managing history records."""

    def __init__(self, session: AsyncSession):
        """Initialize history service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all history records.

        Returns:
            list: List of history records.
        """
        from scholarr.db.models import History

        result = await self.session.execute(select(History))
        return result.scalars().all()

    async def get_by_id(self, history_id: int):
        """Get history record by ID.

        Args:
            history_id: History record ID.

        Returns:
            History: The history record.

        Raises:
            NotFoundError: If record not found.
        """
        from scholarr.db.models import History

        result = await self.session.execute(select(History).where(History.id == history_id))
        record = result.scalar_one_or_none()

        if not record:
            raise NotFoundError(f"History record {history_id} not found")

        return record

    async def get_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PaginatedResult:
        """Get paginated history records with filtering.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            event_type: Filter by event type.
            start_date: Filter by start date.
            end_date: Filter by end date.

        Returns:
            PaginatedResult: Paginated history results.
        """
        from scholarr.db.models import History

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        query = select(History)
        filters = []

        if event_type:
            filters.append(History.event_type == event_type)

        if start_date:
            filters.append(History.timestamp >= start_date)

        if end_date:
            filters.append(History.timestamp <= end_date)

        if filters:
            query = query.where(and_(*filters))

        count_query = select(History)
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await self.session.execute(count_query)
        total = len(count_result.scalars().all())

        query = query.order_by(History.timestamp.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        return PaginatedResult(items, page, page_size, total)

    async def create(self, data: dict):
        """Create a new history record.

        Args:
            data: Dictionary containing history data.

        Returns:
            History: The created history record.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import History

        required_fields = ["event_type", "description"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        record = History(**data)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return record

    async def delete(self, history_id: int):
        """Delete a history record.

        Args:
            history_id: History record ID.

        Raises:
            NotFoundError: If record not found.
        """
        record = await self.get_by_id(history_id)
        await self.session.delete(record)
        await self.session.commit()

    async def delete_older_than(self, days: int) -> int:
        """Delete history records older than specified days.

        Args:
            days: Number of days to keep.

        Returns:
            int: Number of records deleted.
        """
        from scholarr.db.models import History

        cutoff_date = datetime.utcnow().timestamp() - (days * 86400)
        result = await self.session.execute(
            select(History).where(History.timestamp.timestamp() < cutoff_date)
        )
        records = result.scalars().all()
        count = len(records)

        for record in records:
            await self.session.delete(record)

        if count > 0:
            await self.session.commit()

        return count
