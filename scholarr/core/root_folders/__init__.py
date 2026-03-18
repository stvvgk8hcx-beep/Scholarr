"""Root folders management service for Scholarr."""

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class RootFolderService:
    """Service for managing root folders."""

    def __init__(self, session: AsyncSession):
        """Initialize root folder service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all root folders.

        Returns:
            list: List of root folder records.
        """
        from scholarr.db.models import RootFolder

        result = await self.session.execute(select(RootFolder))
        return list(result.scalars().all())

    async def get_by_id(self, folder_id: int):
        """Get root folder by ID.

        Args:
            folder_id: Folder ID.

        Returns:
            RootFolder: The root folder record.

        Raises:
            NotFoundError: If folder not found.
        """
        from scholarr.db.models import RootFolder

        result = await self.session.execute(select(RootFolder).where(RootFolder.id == folder_id))
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundError(f"Root folder {folder_id} not found")

        return folder

    async def create(self, data: dict):
        """Create a new root folder.

        Args:
            data: Dictionary containing folder data.

        Returns:
            RootFolder: The created root folder.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import RootFolder

        required_fields = ["path", "name"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        folder = RootFolder(**data)
        self.session.add(folder)
        await self.session.commit()
        await self.session.refresh(folder)

        return folder

    async def update(self, folder_id: int, data: dict):
        """Update an existing root folder.

        Args:
            folder_id: Folder ID.
            data: Dictionary of fields to update.

        Returns:
            RootFolder: The updated root folder.

        Raises:
            NotFoundError: If folder not found.
        """
        folder = await self.get_by_id(folder_id)

        for key, value in data.items():
            if hasattr(folder, key):
                setattr(folder, key, value)

        self.session.add(folder)
        await self.session.commit()
        await self.session.refresh(folder)

        return folder

    async def delete(self, folder_id: int):
        """Delete a root folder.

        Args:
            folder_id: Folder ID.

        Raises:
            NotFoundError: If folder not found.
        """
        folder = await self.get_by_id(folder_id)
        await self.session.delete(folder)
        await self.session.commit()

    @staticmethod
    def get_free_space(path: str) -> int:
        """Get free disk space for a path.

        Args:
            path: Directory path.

        Returns:
            int: Free space in bytes.
        """
        try:
            stats = psutil.disk_usage(path)
            return stats.free
        except (OSError, ValueError):
            return 0

    @staticmethod
    def get_total_space(path: str) -> int:
        """Get total disk space for a path.

        Args:
            path: Directory path.

        Returns:
            int: Total space in bytes.
        """
        try:
            stats = psutil.disk_usage(path)
            return stats.total
        except (OSError, ValueError):
            return 0

    @staticmethod
    def get_used_space(path: str) -> int:
        """Get used disk space for a path.

        Args:
            path: Directory path.

        Returns:
            int: Used space in bytes.
        """
        try:
            stats = psutil.disk_usage(path)
            return stats.used
        except (OSError, ValueError):
            return 0

    @staticmethod
    def get_disk_info(path: str) -> dict:
        """Get complete disk information for a path.

        Args:
            path: Directory path.

        Returns:
            dict: Dictionary with total, used, and free space in bytes.
        """
        try:
            stats = psutil.disk_usage(path)
            return {
                "total": stats.total,
                "used": stats.used,
                "free": stats.free,
                "percent": stats.percent,
            }
        except (OSError, ValueError):
            return {"total": 0, "used": 0, "free": 0, "percent": 0}
