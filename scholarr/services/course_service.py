"""Course service."""

import json
import logging
from typing import Optional
from sqlalchemy import select, func, or_, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import AcademicItem, Course, Semester
from scholarr.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse

logger = logging.getLogger(__name__)


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _enrich(self, courses: list[Course]) -> list[CourseResponse]:
        """Batch-fetch semester names and item counts, return enriched responses."""
        if not courses:
            return []

        # Batch fetch semester names
        sem_ids = {c.semester_id for c in courses if c.semester_id}
        sem_names: dict[int, str] = {}
        if sem_ids:
            result = await self.db.execute(
                select(Semester.id, Semester.name).where(Semester.id.in_(sem_ids))
            )
            sem_names = {row.id: row.name for row in result}

        # Batch fetch item counts per course
        course_ids = [c.id for c in courses]
        item_counts: dict[int, int] = {}
        if course_ids:
            result = await self.db.execute(
                select(AcademicItem.course_id, func.count().label("cnt"))
                .where(AcademicItem.course_id.in_(course_ids))
                .group_by(AcademicItem.course_id)
            )
            item_counts = {row.course_id: row.cnt for row in result}

        responses = []
        for c in courses:
            r = CourseResponse.model_validate(c)
            r.semester_name = sem_names.get(c.semester_id) if c.semester_id else None
            r.item_count = item_counts.get(c.id, 0)
            responses.append(r)
        return responses

    async def _find_semester_id(self) -> Optional[int]:
        """Return the active semester id, or the first semester id, or None."""
        result = await self.db.execute(
            select(Semester.id).where(Semester.active == True).limit(1)  # noqa: E712
        )
        sid = result.scalar_one_or_none()
        if sid:
            return sid
        result = await self.db.execute(select(Semester.id).limit(1))
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        return await self._enrich(list(result.scalars().all()))

    async def list_courses_paginated(
        self,
        page: int,
        page_size: int,
        sort_key: str = "name",
        sort_dir: str = "asc",
        semester_id: int | None = None,
        monitored: bool | None = None,
        search: str | None = None,
    ) -> CourseListResponse:
        offset = (page - 1) * page_size

        count_query = select(func.count()).select_from(Course)
        data_query = select(Course)

        if semester_id is not None:
            count_query = count_query.where(Course.semester_id == semester_id)
            data_query = data_query.where(Course.semester_id == semester_id)
        if monitored is not None:
            count_query = count_query.where(Course.monitored == monitored)
            data_query = data_query.where(Course.monitored == monitored)
        if search:
            term = f"%{search}%"
            cond = or_(Course.name.ilike(term), Course.code.ilike(term))
            count_query = count_query.where(cond)
            data_query = data_query.where(cond)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        col = getattr(Course, sort_key, Course.name)
        order = col.asc() if sort_dir == "asc" else col.desc()
        result = await self.db.execute(
            data_query.order_by(order).offset(offset).limit(page_size)
        )
        items = await self._enrich(list(result.scalars().all()))
        return CourseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_course(self, id: int) -> CourseResponse | None:
        obj = await self.db.get(Course, id)
        if not obj:
            return None
        enriched = await self._enrich([obj])
        return enriched[0]

    async def create_course(self, course: CourseCreate) -> CourseResponse:
        if not course.code or not course.code.strip():
            raise ValueError("Course code cannot be empty")

        data = course.model_dump()
        # Serialize grade_weights dict to JSON string for storage
        if data.get("grade_weights") is not None:
            data["grade_weights"] = json.dumps(data["grade_weights"])

        # Resolve missing semester_id
        if not data.get("semester_id"):
            sid = await self._find_semester_id()
            if not sid:
                raise ValueError(
                    "No semester found. Create a semester before adding courses."
                )
            data["semester_id"] = sid

        from sqlalchemy.exc import IntegrityError

        obj = Course(**data)
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
        enriched = await self._enrich([obj])
        return enriched[0]

    async def update_course(
        self, id: int, course_update: CourseUpdate
    ) -> CourseResponse | None:
        obj = await self.db.get(Course, id)
        if not obj:
            return None
        update_data = course_update.model_dump(exclude_unset=True)
        if "grade_weights" in update_data and isinstance(update_data["grade_weights"], dict):
            update_data["grade_weights"] = json.dumps(update_data["grade_weights"])
        if update_data:
            await self.db.execute(
                sql_update(Course)
                .where(Course.id == id)
                .values(**update_data)
                .execution_options(synchronize_session=False)
            )
        await self.db.commit()
        # Build response from in-memory snapshot then apply the changed fields.
        # Avoid re-fetching via session.get() because expire_on_commit=False in
        # the test session means the identity-map object is still stale.
        enriched = await self._enrich([obj])
        result = enriched[0]
        for key, val in update_data.items():
            if hasattr(result, key):
                setattr(result, key, val)
        return result

    async def delete_course(self, id: int, delete_files: bool = False) -> bool:
        obj = await self.db.get(Course, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted course id={id} (delete_files={delete_files})")
        return True
