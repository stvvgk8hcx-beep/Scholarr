"""Notifications endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from scholarr.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all notifications."""
    service = NotificationService(db)
    notifications = await service.list_notifications()
    return notifications


@router.get("/{id}", response_model=NotificationResponse)
async def get_notification(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a notification by ID."""
    service = NotificationService(db)
    notification = await service.get_notification(id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification: NotificationCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new notification."""
    service = NotificationService(db)
    new_notification = await service.create_notification(notification)
    return new_notification


@router.put("/{id}", response_model=NotificationResponse)
async def update_notification(
    id: int,
    notification_update: NotificationUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a notification."""
    service = NotificationService(db)
    updated = await service.update_notification(id, notification_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return updated


@router.post("/{id}/test")
async def test_notification(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Test a notification by sending it."""
    service = NotificationService(db)
    success = await service.test_notification(id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "sent"}


@router.delete("/{id}", status_code=204)
async def delete_notification(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a notification."""
    service = NotificationService(db)
    success = await service.delete_notification(id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return None
