"""Health check service for system status and diagnostics."""

import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from scholarr.core.config import settings

logger = logging.getLogger(__name__)


class HealthService:
    """Service for health check operations and system diagnostics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_health_checks(self) -> dict:
        """Run all health checks and return results."""
        # Check database connectivity
        db_healthy = await self._check_database()

        # Check disk space
        disk_status = self._check_disk_space()

        components = [
            {"name": "database", "status": "healthy" if db_healthy else "unhealthy"},
            {
                "name": "disk_space",
                "status": "healthy" if disk_status["available_gb"] > 1 else "warning",
                "details": disk_status,
            },
        ]

        overall_status = "healthy" if db_healthy and disk_status["available_gb"] > 1 else "warning"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": components,
        }

    async def get_detailed_status(self) -> dict:
        """Get comprehensive system status including versions, scheduler, errors."""
        db_healthy = await self._check_database()
        disk_status = self._check_disk_space()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "connected": db_healthy,
                "url": settings.database_url.split("@")[0] + "@***" if "@" in settings.database_url else "***",
            },
            "disk_space": disk_status,
            "system": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.system(),
                "app_version": settings.version,
            },
            "scheduler": {"enabled": settings.enable_scheduler},
            "file_watcher": {"enabled": settings.enable_file_watcher},
            "recent_errors": await self._get_recent_errors(),
        }

    async def _check_database(self) -> bool:
        """Check if database is reachable."""
        try:
            await self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def _check_disk_space(self) -> dict:
        """Check disk space on data directory."""
        try:
            data_path = Path(settings.data_dir)
            if not data_path.exists():
                data_path.mkdir(parents=True, exist_ok=True)

            import shutil

            total, used, free = shutil.disk_usage(data_path)

            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "available_gb": round(free / (1024**3), 2),
                "percent_used": round((used / total) * 100, 2),
            }
        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")
            return {
                "total_gb": None,
                "used_gb": None,
                "available_gb": None,
                "percent_used": None,
            }

    async def _get_recent_errors(self) -> dict:
        """Get count of recent errors from logs."""
        try:
            # TODO: implement error counting from log service
            # This would query the logs table or log file for errors in the last hour
            return {"last_hour": 0, "last_day": 0}
        except Exception as e:
            logger.warning(f"Could not retrieve recent errors: {e}")
            return {"last_hour": 0, "last_day": 0}
