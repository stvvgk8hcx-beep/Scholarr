"""Notifications service for Scholarr."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Base class for notification providers."""

    @abstractmethod
    async def send(self, event_type: str, data: dict[str, Any]) -> bool:
        """Send a notification.

        Args:
            event_type: Type of event.
            data: Event data.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass


class LogNotificationProvider(NotificationProvider):
    """Notification provider that logs to file."""

    async def send(self, event_type: str, data: dict[str, Any]) -> bool:
        """Send notification via logging.

        Args:
            event_type: Type of event.
            data: Event data.

        Returns:
            bool: Always True.
        """
        logger.info(f"Notification [{event_type}]: {json.dumps(data)}")
        return True


class WebhookNotificationProvider(NotificationProvider):
    """Notification provider that sends HTTP POST requests."""

    def __init__(self, url: str, timeout: int = 10):
        """Initialize webhook provider.

        Args:
            url: Webhook URL.
            timeout: Request timeout in seconds.
        """
        self.url = url
        self.timeout = timeout

    async def send(self, event_type: str, data: dict[str, Any]) -> bool:
        """Send notification via webhook.

        Args:
            event_type: Type of event.
            data: Event data.

        Returns:
            bool: True if successful, False otherwise.
        """
        payload = {"event_type": event_type, "data": data}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.url, json=payload)
                return response.status_code < 400
        except httpx.RequestError as e:
            logger.error(f"Webhook request failed: {e}")
            return False


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, session: AsyncSession):
        """Initialize notification service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.providers: dict[str, NotificationProvider] = {}

    async def get_all(self) -> list:
        """Get all notification definitions.

        Returns:
            list: List of notification definition records.
        """
        from scholarr.db.models import NotificationDefinition

        result = await self.session.execute(select(NotificationDefinition))
        return result.scalars().all()

    async def get_by_id(self, notification_id: int):
        """Get notification definition by ID.

        Args:
            notification_id: Notification ID.

        Returns:
            NotificationDefinition: The notification definition.

        Raises:
            NotFoundError: If notification not found.
        """
        from scholarr.db.models import NotificationDefinition

        result = await self.session.execute(
            select(NotificationDefinition).where(NotificationDefinition.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")

        return notification

    async def create(self, data: dict):
        """Create a new notification definition.

        Args:
            data: Dictionary containing notification data.

        Returns:
            NotificationDefinition: The created notification.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import NotificationDefinition

        required_fields = ["name", "event_type", "provider_type"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        notification = NotificationDefinition(**data)
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        return notification

    async def update(self, notification_id: int, data: dict):
        """Update an existing notification definition.

        Args:
            notification_id: Notification ID.
            data: Dictionary of fields to update.

        Returns:
            NotificationDefinition: The updated notification.

        Raises:
            NotFoundError: If notification not found.
        """
        notification = await self.get_by_id(notification_id)

        for key, value in data.items():
            if hasattr(notification, key):
                setattr(notification, key, value)

        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        return notification

    async def delete(self, notification_id: int):
        """Delete a notification definition.

        Args:
            notification_id: Notification ID.

        Raises:
            NotFoundError: If notification not found.
        """
        notification = await self.get_by_id(notification_id)
        await self.session.delete(notification)
        await self.session.commit()

    def register_provider(self, name: str, provider: NotificationProvider):
        """Register a notification provider.

        Args:
            name: Provider name.
            provider: Provider instance.
        """
        self.providers[name] = provider

    async def send_notification(self, event_type: str, data: dict[str, Any]) -> list[bool]:
        """Send notifications for an event.

        Args:
            event_type: Type of event.
            data: Event data.

        Returns:
            list[bool]: List of success/failure for each notification sent.
        """
        from scholarr.db.models import NotificationDefinition

        result = await self.session.execute(
            select(NotificationDefinition).where(NotificationDefinition.event_type == event_type)
        )
        notifications = result.scalars().all()

        results = []

        for notification in notifications:
            if not notification.enabled:
                continue

            provider_name = notification.provider_type
            if provider_name not in self.providers:
                logger.warning(f"Provider {provider_name} not registered")
                results.append(False)
                continue

            provider = self.providers[provider_name]

            try:
                success = await provider.send(event_type, data)
                results.append(success)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
                results.append(False)

        return results
