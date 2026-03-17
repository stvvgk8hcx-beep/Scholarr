"""Academic Item service."""

import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import AcademicItem, AcademicItemStatusEnum
from scholarr.schemas.academic_item import (
    AcademicItemCreate,
    AcademicItemUpdate,
    AcademicItemResponse,
    AcademicItemListResponse,
)

logger = logging.getLogger(__name__)


class AcademicItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_academic_items(
        self,
        course_id: int | None = None,
        status: str | None = None,
        type: str | None = None,
        item_type: str | None = None,
        overdue: bool | None = None,
        search: str | None = None,
        due_after: str | None = None,
        due_before: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> list[AcademicItemResponse]:
        query = select(AcademicItem)
        if course_id is not None:
            query = query.where(AcademicItem.course_id == course_id)
        if status is not None:
            query = query.where(AcademicItem.status == status)
        if item_type is not None:
            type = item_type
        if type is not None:
            query = query.where(AcademicItem.type == type)
        if overdue:
            now = datetime.now(timezone.utc)
            query = query.where(
                AcademicItem.due_date < now,
                AcademicItem.status.not_in([
                    AcademicItemStatusEnum.COMPLETE,
                    AcademicItemStatusEnum.SUBMITTED,
                    AcademicItemStatusEnum.GRADED,
                ]),
            )
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    AcademicItem.name.ilike(pattern),
                    AcademicItem.topic.ilike(pattern),
                    AcademicItem.notes.ilike(pattern),
                )
            )
        if due_after:
            try:
                after_dt = datetime.fromisoformat(due_after)
                query = query.where(AcademicItem.due_date >= after_dt)
            except ValueError:
                pass
        if due_before:
            try:
                before_dt = datetime.fromisoformat(due_before)
                query = query.where(AcademicItem.due_date <= before_dt)
            except ValueError:
                pass
        query = query.order_by(AcademicItem.due_date.asc().nulls_last())
        if page is not None and page_size is not None:
            query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return [AcademicItemResponse.model_validate(row) for row in result.scalars().all()]

    async def list_academic_items_paginated(
        self,
        page: int,
        page_size: int,
        course_id: int | None = None,
        sort_key: str = "due_date",
        sort_dir: str = "asc",
    ) -> AcademicItemListResponse:
        offset = (page - 1) * page_size
        count_query = select(func.count()).select_from(AcademicItem)
        if course_id is not None:
            count_query = count_query.where(AcademicItem.course_id == course_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        col = getattr(AcademicItem, sort_key, AcademicItem.due_date)
        order = col.asc() if sort_dir == "asc" else col.desc()
        query = select(AcademicItem)
        if course_id is not None:
            query = query.where(AcademicItem.course_id == course_id)
        result = await self.db.execute(query.order_by(order).offset(offset).limit(page_size))
        items = [AcademicItemResponse.model_validate(row) for row in result.scalars().all()]
        return AcademicItemListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_upcoming_deadlines(
        self, days: int = 7, course_id: int | None = None
    ) -> list[AcademicItemResponse]:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        query = (
            select(AcademicItem)
            .where(
                AcademicItem.due_date >= now,
                AcademicItem.due_date <= cutoff,
                AcademicItem.status.not_in([
                    AcademicItemStatusEnum.COMPLETE,
                    AcademicItemStatusEnum.SUBMITTED,
                    AcademicItemStatusEnum.GRADED,
                ]),
            )
            .order_by(AcademicItem.due_date.asc())
        )
        if course_id is not None:
            query = query.where(AcademicItem.course_id == course_id)
        result = await self.db.execute(query)
        return [AcademicItemResponse.model_validate(row) for row in result.scalars().all()]

    async def get_academic_item(self, id: int) -> AcademicItemResponse | None:
        obj = await self.db.get(AcademicItem, id)
        return AcademicItemResponse.model_validate(obj) if obj else None

    async def create_academic_item(self, item: AcademicItemCreate) -> AcademicItemResponse:
        # Exclude front-end alias fields that don't exist on the DB model
        data = item.model_dump(exclude={"title", "item_type"})
        # If course_id is None, use a sentinel value or find the first course
        if data.get("course_id") is None:
            from sqlalchemy import select as sa_select
            from scholarr.db.models import Course
            result = await self.db.execute(sa_select(Course).limit(1))
            first_course = result.scalar_one_or_none()
            if first_course:
                data["course_id"] = first_course.id
            else:
                data["course_id"] = 1  # Fallback — will fail FK if no courses
        obj = AcademicItem(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created academic item id={obj.id} name={obj.name!r}")
        return AcademicItemResponse.model_validate(obj)

    async def update_academic_item(
        self, id: int, item_update: AcademicItemUpdate
    ) -> AcademicItemResponse | None:
        obj = await self.db.get(AcademicItem, id)
        if not obj:
            return None
        # Exclude front-end alias fields that don't map to DB columns
        update_data = item_update.model_dump(exclude_unset=True, exclude={"title", "item_type"})
        for key, value in update_data.items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return AcademicItemResponse.model_validate(obj)

    async def delete_academic_item(self, id: int, delete_files: bool = False) -> bool:
        obj = await self.db.get(AcademicItem, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted academic item id={id}")
        return True

    async def list_overdue_items(
        self, course_id: int | None = None
    ) -> list[AcademicItemResponse]:
        """List overdue items (past due date, not completed)."""
        now = datetime.now(timezone.utc)
        query = select(AcademicItem).where(
            AcademicItem.due_date < now,
            AcademicItem.status.not_in([
                AcademicItemStatusEnum.COMPLETE,
                AcademicItemStatusEnum.SUBMITTED,
                AcademicItemStatusEnum.GRADED,
            ]),
        )
        if course_id is not None:
            query = query.where(AcademicItem.course_id == course_id)
        result = await self.db.execute(query)
        return [AcademicItemResponse.model_validate(row) for row in result.scalars().all()]

    # Method aliases for test compatibility
    create_item = create_academic_item
    get_item = get_academic_item
    update_item = update_academic_item
    delete_item = delete_academic_item
    list_items = list_academic_items
    list_items_paginated = list_academic_items_paginated
    list_upcoming_deadlines = get_upcoming_deadlines
