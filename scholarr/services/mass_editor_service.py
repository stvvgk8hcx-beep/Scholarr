"""Mass editor service for bulk operations on courses and academic items."""

import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import (
    AcademicItem,
    AcademicItemStatusEnum,
    AcademicItemTypeEnum,
    Course,
    Tag,
    course_tags,
)

logger = logging.getLogger(__name__)


class MassEditorService:
    """Service for bulk editing courses and academic items."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_update_courses(self, request) -> dict:
        """Bulk update multiple courses with specified fields.

        Updates courses based on provided IDs and only the fields that are not None.
        """
        try:
            errors: list[dict] = []

            # Build the values dict from non-None fields
            values = {}
            if request.semester_id is not None:
                values["semester_id"] = request.semester_id
            if request.monitored is not None:
                values["monitored"] = request.monitored
            if request.root_folder_id is not None:
                values["root_folder_path"] = request.root_folder_id

            # Determine how many of the requested IDs actually exist
            result = await self.db.execute(
                select(Course.id).where(Course.id.in_(request.course_ids))
            )
            existing_ids = {row[0] for row in result}
            missing_ids = set(request.course_ids) - existing_ids

            for mid in missing_ids:
                errors.append({"id": mid, "error": f"Course {mid} not found"})

            updated_count = 0

            if existing_ids and values:
                stmt = (
                    update(Course)
                    .where(Course.id.in_(list(existing_ids)))
                    .values(**values)
                    .execution_options(synchronize_session=False)
                )
                result = await self.db.execute(stmt)
                updated_count = result.rowcount  # type: ignore[union-attr]

            elif existing_ids and not values and request.tags is None:
                # Nothing to update but IDs exist — count them as updated (no-op)
                updated_count = len(existing_ids)

            # Handle tag associations if provided
            if request.tags is not None and existing_ids:
                # Validate that all tag IDs exist
                tag_result = await self.db.execute(
                    select(Tag.id).where(Tag.id.in_(request.tags))
                )
                valid_tag_ids = {row[0] for row in tag_result}
                invalid_tag_ids = set(request.tags) - valid_tag_ids

                for tid in invalid_tag_ids:
                    errors.append({"id": tid, "error": f"Tag {tid} not found"})

                # Remove existing tag associations for these courses
                await self.db.execute(
                    course_tags.delete().where(
                        course_tags.c.course_id.in_(list(existing_ids))
                    )
                )

                # Insert new tag associations
                if valid_tag_ids:
                    rows = [
                        {"course_id": cid, "tag_id": tid}
                        for cid in existing_ids
                        for tid in valid_tag_ids
                    ]
                    await self.db.execute(course_tags.insert(), rows)

                # If no scalar values were updated, count tag-only updates
                if not values:
                    updated_count = len(existing_ids)

            await self.db.commit()

            failed_count = len(missing_ids)
            return {
                "updated_count": updated_count,
                "failed_count": failed_count,
                "errors": errors if errors else None,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk updating courses: {e}")
            return {
                "updated_count": 0,
                "failed_count": len(request.course_ids),
                "errors": [{"error": str(e)}],
            }

    async def bulk_update_academic_items(self, request) -> dict:
        """Bulk update multiple academic items with specified fields.

        Updates items based on provided IDs and only the fields that are not None.
        """
        try:
            errors: list[dict] = []

            # Validate enum values if provided
            if request.status is not None:
                try:
                    AcademicItemStatusEnum(request.status)
                except ValueError:
                    valid = [e.value for e in AcademicItemStatusEnum]
                    return {
                        "updated_count": 0,
                        "failed_count": len(request.item_ids),
                        "errors": [
                            {
                                "error": f"Invalid status '{request.status}'. "
                                f"Valid values: {valid}"
                            }
                        ],
                    }

            if request.type is not None:
                try:
                    AcademicItemTypeEnum(request.type)
                except ValueError:
                    valid = [e.value for e in AcademicItemTypeEnum]
                    return {
                        "updated_count": 0,
                        "failed_count": len(request.item_ids),
                        "errors": [
                            {
                                "error": f"Invalid type '{request.type}'. "
                                f"Valid values: {valid}"
                            }
                        ],
                    }

            # Validate course_id if provided
            if request.course_id is not None:
                course = await self.db.get(Course, request.course_id)
                if not course:
                    return {
                        "updated_count": 0,
                        "failed_count": len(request.item_ids),
                        "errors": [
                            {
                                "error": f"Course {request.course_id} not found"
                            }
                        ],
                    }

            # Build the values dict from non-None fields
            values: dict[str, Any] = {}
            if request.status is not None:
                values["status"] = AcademicItemStatusEnum(request.status)
            if request.type is not None:
                values["type"] = AcademicItemTypeEnum(request.type)
            if request.course_id is not None:
                values["course_id"] = request.course_id

            # Determine how many of the requested IDs actually exist
            result = await self.db.execute(
                select(AcademicItem.id).where(
                    AcademicItem.id.in_(request.item_ids)
                )
            )
            existing_ids = {row[0] for row in result}
            missing_ids = set(request.item_ids) - existing_ids

            for mid in missing_ids:
                errors.append(
                    {"id": mid, "error": f"Academic item {mid} not found"}
                )

            updated_count = 0

            if existing_ids and values:
                stmt = (
                    update(AcademicItem)
                    .where(AcademicItem.id.in_(list(existing_ids)))
                    .values(**values)
                    .execution_options(synchronize_session=False)
                )
                result = await self.db.execute(stmt)
                updated_count = result.rowcount  # type: ignore[union-attr]
            elif existing_ids and not values:
                # Nothing to update but IDs exist — count them as updated (no-op)
                updated_count = len(existing_ids)

            await self.db.commit()

            failed_count = len(missing_ids)
            return {
                "updated_count": updated_count,
                "failed_count": failed_count,
                "errors": errors if errors else None,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk updating academic items: {e}")
            return {
                "updated_count": 0,
                "failed_count": len(request.item_ids),
                "errors": [{"error": str(e)}],
            }
