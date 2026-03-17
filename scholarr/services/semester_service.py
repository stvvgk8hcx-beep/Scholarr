"""Semester service."""

import logging
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Semester
from scholarr.schemas.semester import SemesterCreate, SemesterUpdate, SemesterResponse, SemesterListResponse

logger = logging.getLogger(__name__)


class SemesterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_semesters(self, year: int | None = None) -> list[SemesterResponse]:
        query = select(Semester)
        if year is not None:
            query = query.where(Semester.year == year)
        query = query.order_by(Semester.year.desc(), Semester.term)
        result = await self.db.execute(query)
        return [SemesterResponse.model_validate(row) for row in result.scalars().all()]

    async def list_semesters_paginated(self, page: int, page_size: int) -> SemesterListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(Semester))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(Semester).order_by(Semester.year.desc()).offset(offset).limit(page_size)
        )
        items = [SemesterResponse.model_validate(row) for row in result.scalars().all()]
        return SemesterListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_semester(self, id: int) -> SemesterResponse | None:
        # Use SELECT instead of session.get() to always get fresh data from DB,
        # avoiding MissingGreenlet on expired objects after bulk UPDATEs.
        result = await self.db.execute(select(Semester).where(Semester.id == id))
        obj = result.scalar_one_or_none()
        return SemesterResponse.model_validate(obj) if obj else None

    async def get_active_semester(self) -> SemesterResponse | None:
        result = await self.db.execute(select(Semester).where(Semester.active == True))  # noqa: E712
        obj = result.scalar_one_or_none()
        return SemesterResponse.model_validate(obj) if obj else None

    async def set_active_semester(self, id: int) -> SemesterResponse | None:
        """Mark the given semester as active and deactivate all others."""
        obj = await self.db.get(Semester, id)
        if not obj:
            return None
        # Use synchronize_session="evaluate" (default) so SQLAlchemy updates the
        # in-memory identity-map objects to reflect the bulk SQL changes.
        await self.db.execute(
            update(Semester).where(Semester.id != id).values(active=False)
        )
        await self.db.execute(
            update(Semester).where(Semester.id == id).values(active=True)
        )
        await self.db.commit()
        # Refresh target object from DB to get authoritative state
        await self.db.refresh(obj)
        logger.info(f"Set active semester id={id}")
        return SemesterResponse.model_validate(obj)

    async def create_semester(self, semester: SemesterCreate) -> SemesterResponse:
        obj = Semester(**semester.model_dump())
        self.db.add(obj)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(
                f"A semester for {semester.year} {semester.term.value} already exists"
            )
        await self.db.refresh(obj)
        logger.info(f"Created semester id={obj.id} name={obj.name!r}")
        return SemesterResponse.model_validate(obj)

    async def update_semester(self, id: int, semester_update: SemesterUpdate) -> SemesterResponse | None:
        obj = await self.db.get(Semester, id)
        if not obj:
            return None
        for key, value in semester_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return SemesterResponse.model_validate(obj)

    async def delete_semester(self, id: int, cascade: bool = False) -> bool:
        obj = await self.db.get(Semester, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted semester id={id} (cascade={cascade})")
        return True
