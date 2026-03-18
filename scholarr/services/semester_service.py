"""Semester service."""

import logging

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Course, Semester
from scholarr.schemas.semester import (
    SemesterCreate,
    SemesterListResponse,
    SemesterResponse,
    SemesterUpdate,
)

logger = logging.getLogger(__name__)


class SemesterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Internal: batch-load course counts for a list of semester rows
    # ------------------------------------------------------------------

    async def _course_counts(self, semester_ids: list[int]) -> dict[int, int]:
        if not semester_ids:
            return {}
        result = await self.db.execute(
            select(Course.semester_id, func.count().label("cnt"))
            .where(Course.semester_id.in_(semester_ids))
            .group_by(Course.semester_id)
        )
        return {row.semester_id: row.cnt for row in result}

    def _to_response(self, obj: Semester, count: int = 0) -> SemesterResponse:
        r = SemesterResponse.model_validate(obj)
        r.course_count = count
        return r

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_semesters(self, year: int | None = None) -> list[SemesterResponse]:
        query = select(Semester)
        if year is not None:
            query = query.where(Semester.year == year)
        query = query.order_by(Semester.year.desc(), Semester.term)
        result = await self.db.execute(query)
        rows = result.scalars().all()
        counts = await self._course_counts([s.id for s in rows])
        return [self._to_response(s, counts.get(s.id, 0)) for s in rows]

    async def list_semesters_paginated(
        self, page: int, page_size: int
    ) -> SemesterListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(
            select(func.count()).select_from(Semester)
        )
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(Semester).order_by(Semester.year.desc()).offset(offset).limit(page_size)
        )
        rows = result.scalars().all()
        counts = await self._course_counts([s.id for s in rows])
        items = [self._to_response(s, counts.get(s.id, 0)) for s in rows]
        return SemesterListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_semester(self, id: int) -> SemesterResponse | None:
        result = await self.db.execute(select(Semester).where(Semester.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        counts = await self._course_counts([obj.id])
        return self._to_response(obj, counts.get(obj.id, 0))

    async def get_active_semester(self) -> SemesterResponse | None:
        result = await self.db.execute(
            select(Semester).where(Semester.active == True)  # noqa: E712
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        counts = await self._course_counts([obj.id])
        return self._to_response(obj, counts.get(obj.id, 0))

    async def set_active_semester(self, id: int) -> SemesterResponse | None:
        """Mark the given semester as active and deactivate all others."""
        obj = await self.db.get(Semester, id)
        if not obj:
            return None
        await self.db.execute(
            update(Semester).where(Semester.id != id).values(active=False)
        )
        await self.db.execute(
            update(Semester).where(Semester.id == id).values(active=True)
        )
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Set active semester id={id}")
        counts = await self._course_counts([obj.id])
        return self._to_response(obj, counts.get(obj.id, 0))

    async def create_semester(self, semester: SemesterCreate) -> SemesterResponse:
        obj = Semester(**semester.model_dump())
        self.db.add(obj)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            term_str = semester.term.value if semester.term else "Unknown"
            raise ValueError(
                f"A semester for {semester.year} {term_str} already exists"
            ) from None
        await self.db.refresh(obj)
        logger.info(f"Created semester id={obj.id} name={obj.name!r}")
        return self._to_response(obj, 0)

    async def update_semester(
        self, id: int, semester_update: SemesterUpdate
    ) -> SemesterResponse | None:
        obj = await self.db.get(Semester, id)
        if not obj:
            return None
        for key, value in semester_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        counts = await self._course_counts([obj.id])
        return self._to_response(obj, counts.get(obj.id, 0))

    async def delete_semester(self, id: int, cascade: bool = False) -> bool:
        obj = await self.db.get(Semester, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted semester id={id} (cascade={cascade})")
        return True
