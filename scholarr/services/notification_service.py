"""Notification service."""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import NotificationDefinition
from scholarr.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    NotificationUpdate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notifications(self) -> list[NotificationResponse]:
        result = await self.db.execute(select(NotificationDefinition).order_by(NotificationDefinition.name))
        return [NotificationResponse.model_validate(row) for row in result.scalars().all()]

    async def list_notifications_paginated(self, page: int, page_size: int) -> NotificationListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(NotificationDefinition))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(NotificationDefinition).order_by(NotificationDefinition.name).offset(offset).limit(page_size)
        )
        items = [NotificationResponse.model_validate(row) for row in result.scalars().all()]
        return NotificationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_notification(self, id: int) -> NotificationResponse | None:
        obj = await self.db.get(NotificationDefinition, id)
        return NotificationResponse.model_validate(obj) if obj else None

    async def create_notification(self, notification: NotificationCreate) -> NotificationResponse:
        obj = NotificationDefinition(**notification.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created notification id={obj.id} name={obj.name!r}")
        return NotificationResponse.model_validate(obj)

    async def update_notification(
        self, id: int, notification_update: NotificationUpdate
    ) -> NotificationResponse | None:
        obj = await self.db.get(NotificationDefinition, id)
        if not obj:
            return None
        for key, value in notification_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return NotificationResponse.model_validate(obj)

    async def test_notification(self, id: int) -> bool:
        """Send a test notification. Stub — actual delivery depends on implementation field."""
        obj = await self.db.get(NotificationDefinition, id)
        if not obj or not obj.enabled:
            return False
        logger.info(f"Test notification triggered for id={id} implementation={obj.implementation!r}")
        return True

    async def delete_notification(self, id: int) -> bool:
        obj = await self.db.get(NotificationDefinition, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted notification id={id}")
        return True
