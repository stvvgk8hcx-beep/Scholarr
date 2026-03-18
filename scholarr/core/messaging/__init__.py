"""Event bus and messaging service for Scholarr."""

import asyncio
from collections.abc import Callable
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Event types broadcast in Scholarr."""

    # Course events
    COURSE_CREATED = "course.created"
    COURSE_UPDATED = "course.updated"
    COURSE_DELETED = "course.deleted"

    # Academic item events
    ACADEMIC_ITEM_CREATED = "academic_item.created"
    ACADEMIC_ITEM_UPDATED = "academic_item.updated"
    ACADEMIC_ITEM_DELETED = "academic_item.deleted"
    ACADEMIC_ITEM_COMPLETED = "academic_item.completed"
    ACADEMIC_ITEM_DUE_SOON = "academic_item.due_soon"

    # File events
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"
    FILE_SCANNED = "file.scanned"

    # Semester events
    SEMESTER_CREATED = "semester.created"
    SEMESTER_UPDATED = "semester.updated"
    SEMESTER_ACTIVATED = "semester.activated"
    SEMESTER_DELETED = "semester.deleted"

    # System events
    SYSTEM_HEALTH = "system.health"
    BACKUP_COMPLETED = "backup.completed"
    MAINTENANCE_STARTED = "maintenance.started"
    MAINTENANCE_COMPLETED = "maintenance.completed"


class EventBus:
    """Publish/subscribe event bus for async event handling."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: dict[str, list[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()

    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to.
            callback: Callback function to execute when event is published.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)

    async def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event.
            callback: Callback function to remove.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event_type: Type of event.
            data: Event data.
        """
        await self._event_queue.put({"type": event_type, "data": data})

    async def _process_events(self) -> None:
        """Process events from the queue.

        This method should run continuously in the background.
        """
        while True:
            event = await self._event_queue.get()
            await self._dispatch_event(event["type"], event["data"])

    async def _dispatch_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Dispatch an event to all subscribers.

        Args:
            event_type: Type of event.
            data: Event data.
        """
        if event_type not in self._subscribers:
            return

        callbacks = self._subscribers[event_type]
        tasks = []

        for callback in callbacks:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(data))
            else:
                tasks.append(asyncio.create_task(self._run_sync_callback(callback, data)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _run_sync_callback(callback: Callable, data: dict[str, Any]) -> None:
        """Run a synchronous callback in an executor.

        Args:
            callback: Callback function.
            data: Event data.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, callback, data)

    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Type of event.

        Returns:
            int: Number of subscribers.
        """
        return len(self._subscribers.get(event_type, []))

    async def start(self) -> asyncio.Task:
        """Start the event bus processor.

        Returns:
            asyncio.Task: Background task running the event processor.
        """
        return asyncio.create_task(self._process_events())

    async def shutdown(self) -> None:
        """Shut down the event bus."""
        while not self._event_queue.empty():
            event = await self._event_queue.get()
            await self._dispatch_event(event["type"], event["data"])

        self._subscribers.clear()


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        EventBus: The event bus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (for testing)."""
    global _event_bus
    _event_bus = None
