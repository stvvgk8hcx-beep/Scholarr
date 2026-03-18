"""Course management service for Scholarr."""


from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class PaginatedResult:
    """Paginated result container."""

    def __init__(
        self,
        items: list,
        page: int,
        page_size: int,
        total: int,
    ):
        """Initialize paginated result.

        Args:
            items: List of items in current page.
            page: Current page number.
            page_size: Number of items per page.
            total: Total number of items.
        """
        self.items = items
        self.page = page
        self.page_size = page_size
        self.total = total
        self.pages = (total + page_size - 1) // page_size


class CourseService:
    """Service for managing courses."""

    def __init__(self, session: AsyncSession):
        """Initialize course service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(
        self,
        semester_id: int | None = None,
        monitored: bool | None = None,
        search: str | None = None,
    ) -> list:
        """Get all courses with optional filtering.

        Args:
            semester_id: Filter by semester ID.
            monitored: Filter by monitored status.
            search: Search in course code and name.

        Returns:
            list: List of course records.
        """
        from scholarr.db.models import Course

        filters = []

        if semester_id is not None:
            filters.append(Course.semester_id == semester_id)

        if monitored is not None:
            filters.append(Course.monitored == monitored)

        if search:
            search_term = f"%{search}%"
            filters.append(
                (Course.code.ilike(search_term)) | (Course.name.ilike(search_term))
            )

        query = select(Course)
        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paged(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_key: str = "code",
        sort_dir: str = "asc",
        filters: dict | None = None,
    ) -> PaginatedResult:
        """Get paginated courses with sorting and filtering.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            sort_key: Column to sort by.
            sort_dir: Sort direction ('asc' or 'desc').
            filters: Dictionary of filter conditions.

        Returns:
            PaginatedResult: Paginated course results.
        """
        from scholarr.db.models import Course

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        filters = filters or {}
        query = select(Course)

        filter_conditions = []
        if "semester_id" in filters:
            filter_conditions.append(Course.semester_id == filters["semester_id"])
        if "monitored" in filters:
            filter_conditions.append(Course.monitored == filters["monitored"])
        if "search" in filters:
            search_term = f"%{filters['search']}%"
            filter_conditions.append(
                (Course.code.ilike(search_term)) | (Course.name.ilike(search_term))
            )

        if filter_conditions:
            query = query.where(and_(*filter_conditions))

        count_result = await self.session.execute(
            select(Course).where(and_(*filter_conditions)) if filter_conditions else select(Course)
        )
        total = len(count_result.scalars().all())

        if sort_key == "code":
            query = query.order_by(Course.code.asc() if sort_dir == "asc" else Course.code.desc())
        elif sort_key == "name":
            query = query.order_by(Course.name.asc() if sort_dir == "asc" else Course.name.desc())
        else:
            query = query.order_by(Course.code.asc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return PaginatedResult(items, page, page_size, total)

    async def get_by_id(self, course_id: int):
        """Get course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course: The course record.

        Raises:
            NotFoundError: If course not found.
        """
        from scholarr.db.models import Course

        result = await self.session.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()

        if not course:
            raise NotFoundError(f"Course {course_id} not found")

        return course

    async def create(self, data: dict):
        """Create a new course.

        Args:
            data: Dictionary containing course data.

        Returns:
            Course: The created course.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import Course

        required_fields = ["code", "name", "semester_id"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        course = Course(**data)
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)

        return course

    async def update(self, course_id: int, data: dict):
        """Update an existing course.

        Args:
            course_id: Course ID.
            data: Dictionary of fields to update.

        Returns:
            Course: The updated course.

        Raises:
            NotFoundError: If course not found.
        """
        course = await self.get_by_id(course_id)

        for key, value in data.items():
            if hasattr(course, key):
                setattr(course, key, value)

        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)

        return course

    async def delete(self, course_id: int, delete_files: bool = False):
        """Delete a course.

        Args:
            course_id: Course ID.
            delete_files: Whether to delete associated files.

        Raises:
            NotFoundError: If course not found.
        """
        course = await self.get_by_id(course_id)

        if delete_files:
            from scholarr.db.models import AcademicItem, ManagedFile

            items_result = await self.session.execute(
                select(AcademicItem).where(AcademicItem.course_id == course_id)
            )
            items = items_result.scalars().all()

            for item in items:
                files_result = await self.session.execute(
                    select(ManagedFile).where(ManagedFile.academic_item_id == item.id)
                )
                files = files_result.scalars().all()
                for f in files:
                    await self.session.delete(f)
                await self.session.delete(item)

        await self.session.delete(course)
        await self.session.commit()
