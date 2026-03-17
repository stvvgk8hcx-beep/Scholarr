"""Semester management service for Scholarr."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class SemesterService:
    """Service for managing semesters."""

    def __init__(self, session: AsyncSession):
        """Initialize semester service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all semesters.

        Returns:
            list: List of semester records.
        """
        from scholarr.db.models import Semester

        result = await self.session.execute(select(Semester))
        return result.scalars().all()

    async def get_by_id(self, semester_id: int):
        """Get semester by ID.

        Args:
            semester_id: Semester ID.

        Returns:
            Semester: The semester record.

        Raises:
            NotFoundError: If semester not found.
        """
        from scholarr.db.models import Semester

        result = await self.session.execute(select(Semester).where(Semester.id == semester_id))
        semester = result.scalar_one_or_none()

        if not semester:
            raise NotFoundError(f"Semester {semester_id} not found")

        return semester

    async def get_active(self):
        """Get the active semester.

        Returns:
            Semester: The active semester, or None if none is active.
        """
        from scholarr.db.models import Semester

        result = await self.session.execute(
            select(Semester).where(Semester.is_active == True)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict):
        """Create a new semester.

        Args:
            data: Dictionary containing semester data.

        Returns:
            Semester: The created semester.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import Semester

        required_fields = ["name", "start_date", "end_date"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        semester = Semester(**data)
        self.session.add(semester)
        await self.session.commit()
        await self.session.refresh(semester)

        return semester

    async def update(self, semester_id: int, data: dict):
        """Update an existing semester.

        Args:
            semester_id: Semester ID.
            data: Dictionary of fields to update.

        Returns:
            Semester: The updated semester.

        Raises:
            NotFoundError: If semester not found.
        """
        semester = await self.get_by_id(semester_id)

        for key, value in data.items():
            if hasattr(semester, key):
                setattr(semester, key, value)

        self.session.add(semester)
        await self.session.commit()
        await self.session.refresh(semester)

        return semester

    async def delete(self, semester_id: int):
        """Delete a semester.

        Args:
            semester_id: Semester ID.

        Raises:
            NotFoundError: If semester not found.
        """
        semester = await self.get_by_id(semester_id)
        await self.session.delete(semester)
        await self.session.commit()

    async def set_active(self, semester_id: int):
        """Set a semester as active, deactivating others.

        Args:
            semester_id: Semester ID to activate.

        Returns:
            Semester: The activated semester.

        Raises:
            NotFoundError: If semester not found.
        """
        from scholarr.db.models import Semester

        result = await self.session.execute(select(Semester))
        all_semesters = result.scalars().all()
        for sem in all_semesters:
            sem.is_active = False

        semester = await self.get_by_id(semester_id)
        semester.is_active = True

        self.session.add(semester)
        await self.session.commit()
        await self.session.refresh(semester)

        return semester
