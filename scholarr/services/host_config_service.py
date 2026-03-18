"""Host Configuration service — reads/writes application settings."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.config import settings
from scholarr.schemas.host_config import HostConfigResponse, HostConfigUpdate

logger = logging.getLogger(__name__)


class HostConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_host_config(self) -> HostConfigResponse:
        return HostConfigResponse(
            app_name=settings.app_name,
            version=settings.version,
            environment=settings.environment,
            debug=settings.debug,
            log_level=settings.log_level,
            enable_scheduler=settings.enable_scheduler,
            enable_file_watcher=settings.enable_file_watcher,
            inbox_path=settings.inbox_path,
        )

    async def update_host_config(self, config_update: HostConfigUpdate) -> HostConfigResponse:
        """Apply runtime overrides to in-memory settings.

        Note: these changes are not persisted across restarts. Configure via
        environment variables (SCHOLARR_*) or .env file for permanent changes.
        """
        data = config_update.model_dump(exclude_unset=True)
        for key, value in data.items():
            if hasattr(settings, key):
                object.__setattr__(settings, key, value)
                logger.info(f"Runtime config updated: {key}={value!r}")
        return await self.get_host_config()
