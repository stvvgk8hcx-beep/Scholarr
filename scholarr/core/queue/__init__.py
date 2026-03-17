"""Queue management service for Scholarr."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class QueueService:
    """Service for managing processing queue."""

    def __init__(self, session: AsyncSession):
        """Initialize queue service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_queue(self) -> list:
        """Get current queue items.

        Returns:
            list: List of queue items ordered by priority.
        """
        from scholarr.db.models import QueueItem

        result = await self.session.execute(
            select(QueueItem)
            .where(QueueItem.status.in_(["pending", "processing"]))
            .order_by(
                QueueItem.priority.desc(),
                QueueItem.created_at.asc(),
            )
        )
        return result.scalars().all()

    async def add_to_queue(self, data: dict):
        """Add item to queue.

        Args:
            data: Dictionary containing queue item data.

        Returns:
            QueueItem: The created queue item.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import QueueItem

        required_fields = ["item_type", "item_id"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        item = QueueItem(**data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def remove_from_queue(self, queue_item_id: int):
        """Remove item from queue.

        Args:
            queue_item_id: Queue item ID.

        Raises:
            NotFoundError: If item not found.
        """
        from scholarr.db.models import QueueItem

        result = await self.session.execute(
            select(QueueItem).where(QueueItem.id == queue_item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise NotFoundError(f"Queue item {queue_item_id} not found")

        await self.session.delete(item)
        await self.session.commit()

    async def get_progress(self, queue_item_id: int) -> Optional[dict]:
        """Get progress of a queue item.

        Args:
            queue_item_id: Queue item ID.

        Returns:
            dict: Progress information with status and percent_complete.
        """
        from scholarr.db.models import QueueItem

        result = await self.session.execute(
            select(QueueItem).where(QueueItem.id == queue_item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        return {
            "id": item.id,
            "status": item.status,
            "percent_complete": item.progress or 0,
            "message": item.message,
        }

    async def update_progress(
        self,
        queue_item_id: int,
        status: str,
        progress: Optional[int] = None,
        message: Optional[str] = None,
    ):
        """Update queue item progress.

        Args:
            queue_item_id: Queue item ID.
            status: New status.
            progress: Progress percentage (0-100).
            message: Status message.

        Raises:
            NotFoundError: If item not found.
        """
        from scholarr.db.models import QueueItem

        result = await self.session.execute(
            select(QueueItem).where(QueueItem.id == queue_item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise NotFoundError(f"Queue item {queue_item_id} not found")

        item.status = status
        if progress is not None:
            item.progress = max(0, min(100, progress))
        if message is not None:
            item.message = message

        self.session.add(item)
        await self.session.commit()

    async def clear_completed(self) -> int:
        """Clear completed items from queue.

        Returns:
            int: Number of items cleared.
        """
        from scholarr.db.models import QueueItem

        result = await self.session.execute(
            select(QueueItem).where(QueueItem.status == "completed")
        )
        items = result.scalars().all()
        count = len(items)

        for item in items:
            await self.session.delete(item)

        if count > 0:
            await self.session.commit()

        return count
