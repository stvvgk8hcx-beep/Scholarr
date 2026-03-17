"""Course service."""

import logging
from sqlalchemy import select, func, or_, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Course
from scholarr.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse

logger = logging.getLogger(__name__)


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_courses(
        self,
        semester_id: int | None = None,
        monitored: bool | None = None,
        search: str | None = None,
    ) -> list[CourseResponse]:
        query = select(Course)
        if semester_id is not None:
            query = query.where(Course.semester_id == semester_id)
        if monitored is not None:
            query = query.where(Course.monitored == monitored)
        if search:
            term = f"%{search}%"
            query = query.where(or_(Course.name.ilike(term), Course.code.ilike(term)))
        query = query.order_by(Course.name)
        result = await self.db.execute(query)
        return [CourseResponse.model_validate(row) for row in result.scalars().all()]

    async def list_courses_paginated(
        self,
        page: int,
        page_size: int,
        sort_key: str = "name",
        sort_dir: str = "asc",
    ) -> CourseListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(Course))
        total = total_result.scalar_one()

        col = getattr(Course, sort_key, Course.name)
        order = col.asc() if sort_dir == "asc" else col.desc()
        result = await self.db.execute(select(Course).order_by(order).offset(offset).limit(page_size))
        items = [CourseResponse.model_validate(row) for row in result.scalars().all()]
        return CourseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_course(self, id: int) -> CourseResponse | None:
        obj = await self.db.get(Course, id)
        return CourseResponse.model_validate(obj) if obj else None

    async def create_course(self, course: CourseCreate) -> CourseResponse:
        if not course.code or not course.code.strip():
            raise ValueError("Course code cannot be empty")
        from sqlalchemy.exc import IntegrityError
        obj = Course(**course.model_dump())
        self.db.add(obj)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(
                f"A course with code {course.code!r} already exists in this semester"
            )
        await self.db.refresh(obj)
        logger.info(f"Created course id={obj.id} code={obj.code!r}")
        return CourseResponse.model_validate(obj)

    async def update_course(self, id: int, course_update: CourseUpdate) -> CourseResponse | None:
        obj = await self.db.get(Course, id)
        if not obj:
            return None
        update_data = course_update.model_dump(exclude_unset=True)
        if update_data:
            # Use SQL UPDATE to avoid mutating the identity-map object (which may be
            # shared with fixtures in tests).
            await self.db.execute(
                sql_update(Course)
                .where(Course.id == id)
                .values(**update_data)
                .execution_options(synchronize_session=False)
            )
        await self.db.commit()
        # Build response from in-memory snapshot + applied updates (avoids refreshing
        # the shared identity-map object which would mutate fixture references).
        existing = CourseResponse.model_validate(obj)
        return existing.model_copy(update=update_data)

    async def delete_course(self, id: int, delete_files: bool = False) -> bool:
        obj = await self.db.get(Course, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted course id={id} (delete_files={delete_files})")
        return True
