"""WebSocket broadcast manager for real-time updates."""

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        with contextlib.suppress(ValueError):
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def broadcast_course_added(self, course_data: dict[str, Any]):
        """Broadcast when a course is added."""
        message = {
            "type": "course_added",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": course_data,
        }
        await self.broadcast(message)

    async def broadcast_course_updated(self, course_data: dict[str, Any]):
        """Broadcast when a course is updated."""
        message = {
            "type": "course_updated",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": course_data,
        }
        await self.broadcast(message)

    async def broadcast_course_deleted(self, course_id: int):
        """Broadcast when a course is deleted."""
        message = {
            "type": "course_deleted",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"id": course_id},
        }
        await self.broadcast(message)

    async def broadcast_academic_item_added(self, item_data: dict[str, Any]):
        """Broadcast when an academic item is added."""
        message = {
            "type": "academic_item_added",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": item_data,
        }
        await self.broadcast(message)

    async def broadcast_academic_item_updated(self, item_data: dict[str, Any]):
        """Broadcast when an academic item is updated."""
        message = {
            "type": "academic_item_updated",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": item_data,
        }
        await self.broadcast(message)

    async def broadcast_academic_item_deleted(self, item_id: int):
        """Broadcast when an academic item is deleted."""
        message = {
            "type": "academic_item_deleted",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"id": item_id},
        }
        await self.broadcast(message)

    async def broadcast_managed_file_imported(self, file_data: dict[str, Any]):
        """Broadcast when a file is imported."""
        message = {
            "type": "managed_file_imported",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": file_data,
        }
        await self.broadcast(message)

    async def broadcast_managed_file_organized(self, file_data: dict[str, Any]):
        """Broadcast when a file is organized/moved."""
        message = {
            "type": "managed_file_organized",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": file_data,
        }
        await self.broadcast(message)

    async def broadcast_health_check_results(self, results: dict[str, Any]):
        """Broadcast health check results."""
        message = {
            "type": "health_check_results",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": results,
        }
        await self.broadcast(message)

    async def broadcast_queue_progress(self, progress_data: dict[str, Any]):
        """Broadcast queue progress update."""
        message = {
            "type": "queue_progress",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": progress_data,
        }
        await self.broadcast(message)

    async def broadcast_history_entry(self, history_data: dict[str, Any]):
        """Broadcast a new history entry."""
        message = {
            "type": "history_entry",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": history_data,
        }
        await self.broadcast(message)

    async def broadcast_system_status(self, status_data: dict[str, Any]):
        """Broadcast system status update."""
        message = {
            "type": "system_status",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": status_data,
        }
        await self.broadcast(message)

    async def broadcast_notification_sent(self, notification_data: dict[str, Any]):
        """Broadcast when a notification is sent."""
        message = {
            "type": "notification_sent",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": notification_data,
        }
        await self.broadcast(message)

    async def broadcast_backup_completed(self, backup_data: dict[str, Any]):
        """Broadcast when a backup is completed."""
        message = {
            "type": "backup_completed",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": backup_data,
        }
        await self.broadcast(message)

    async def broadcast_error(self, error_message: str, error_code: str = "error"):
        """Broadcast an error message."""
        message = {
            "type": "error",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "message": error_message,
                "error_code": error_code,
            },
        }
        await self.broadcast(message)
