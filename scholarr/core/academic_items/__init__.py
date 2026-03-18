"""Academic items management service for Scholarr."""

from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.courses import PaginatedResult
from scholarr.core.exceptions import NotFoundError, ValidationError


class AcademicItemService:
    """Service for managing academic items (assignments, exams, etc.)."""

    def __init__(self, session: AsyncSession):
        """Initialize academic item service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(
        self,
        course_id: int | None = None,
        status: str | None = None,
        item_type: str | None = None,
        overdue: bool | None = None,
    ) -> list:
        """Get all academic items with optional filtering.

        Args:
            course_id: Filter by course ID.
            status: Filter by status (pending, submitted, graded).
            item_type: Filter by item type (assignment, exam, project, etc.).
            overdue: Filter by overdue status.

        Returns:
            list: List of academic item records.
        """
        from scholarr.db.models import AcademicItem

        filters = []

        if course_id is not None:
            filters.append(AcademicItem.course_id == course_id)

        if status is not None:
            filters.append(AcademicItem.status == status)

        if item_type is not None:
            filters.append(AcademicItem.type == item_type)

        if overdue is not None:
            now = datetime.utcnow()
            if overdue:
                filters.append(
                    and_(
                        AcademicItem.due_date < now,
                        AcademicItem.status != "completed",
                    )
                )
            else:
                filters.append(
                    or_(
                        AcademicItem.due_date >= now,
                        AcademicItem.status == "completed",
                    )
                )

        query = select(AcademicItem)
        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_key: str = "due_date",
        sort_dir: str = "asc",
        filters: dict | None = None,
    ) -> PaginatedResult:
        """Get paginated academic items.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            sort_key: Column to sort by.
            sort_dir: Sort direction ('asc' or 'desc').
            filters: Dictionary of filter conditions.

        Returns:
            PaginatedResult: Paginated academic item results.
        """
        from scholarr.db.models import AcademicItem

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        filters = filters or {}
        query = select(AcademicItem)

        filter_conditions = []
        if "course_id" in filters:
            filter_conditions.append(AcademicItem.course_id == filters["course_id"])
        if "status" in filters:
            filter_conditions.append(AcademicItem.status == filters["status"])
        if "type" in filters:
            filter_conditions.append(AcademicItem.type == filters["type"])

        if filter_conditions:
            query = query.where(and_(*filter_conditions))

        count_query = select(AcademicItem)
        if filter_conditions:
            count_query = count_query.where(and_(*filter_conditions))
        count_result = await self.session.execute(count_query)
        total = len(count_result.scalars().all())

        if sort_key == "due_date":
            query = query.order_by(
                AcademicItem.due_date.asc() if sort_dir == "asc" else AcademicItem.due_date.desc()
            )
        elif sort_key == "title":
            query = query.order_by(
                AcademicItem.title.asc() if sort_dir == "asc" else AcademicItem.title.desc()
            )
        else:
            query = query.order_by(AcademicItem.due_date.asc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return PaginatedResult(items, page, page_size, total)

    async def get_by_id(self, item_id: int):
        """Get academic item by ID.

        Args:
            item_id: Academic item ID.

        Returns:
            AcademicItem: The academic item record.

        Raises:
            NotFoundError: If item not found.
        """
        from scholarr.db.models import AcademicItem

        result = await self.session.execute(
            select(AcademicItem).where(AcademicItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise NotFoundError(f"Academic item {item_id} not found")

        return item

    async def get_upcoming(self, days: int = 30) -> list:
        """Get upcoming academic items.

        Args:
            days: Number of days to look ahead.

        Returns:
            list: List of upcoming academic items.
        """
        from scholarr.db.models import AcademicItem

        now = datetime.utcnow()
        future = now + timedelta(days=days)

        result = await self.session.execute(
            select(AcademicItem).where(
                and_(
                    AcademicItem.due_date >= now,
                    AcademicItem.due_date <= future,
                    AcademicItem.status != "completed",
                )
            )
        )
        return list(result.scalars().all())

    async def create(self, data: dict):
        """Create a new academic item.

        Args:
            data: Dictionary containing academic item data.

        Returns:
            AcademicItem: The created academic item.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import AcademicItem

        required_fields = ["title", "type", "course_id", "due_date"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        item = AcademicItem(**data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def update(self, item_id: int, data: dict):
        """Update an existing academic item.

        Args:
            item_id: Academic item ID.
            data: Dictionary of fields to update.

        Returns:
            AcademicItem: The updated academic item.

        Raises:
            NotFoundError: If item not found.
        """
        item = await self.get_by_id(item_id)

        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def delete(self, item_id: int, delete_files: bool = False):
        """Delete an academic item.

        Args:
            item_id: Academic item ID.
            delete_files: Whether to delete associated files.

        Raises:
            NotFoundError: If item not found.
        """
        item = await self.get_by_id(item_id)

        if delete_files:
            from scholarr.db.models import ManagedFile

            files_result = await self.session.execute(
                select(ManagedFile).where(ManagedFile.academic_item_id == item_id)
            )
            files = files_result.scalars().all()
            for f in files:
                await self.session.delete(f)

        await self.session.delete(item)
        await self.session.commit()
