"""Managed files service for Scholarr."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class ManagedFileService:
    """Service for managing academic files."""

    def __init__(self, session: AsyncSession):
        """Initialize managed file service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self, academic_item_id: Optional[int] = None) -> list:
        """Get all managed files with optional filtering.

        Args:
            academic_item_id: Filter by academic item ID.

        Returns:
            list: List of managed file records.
        """
        from scholarr.db.models import ManagedFile

        query = select(ManagedFile)

        if academic_item_id is not None:
            query = query.where(ManagedFile.academic_item_id == academic_item_id)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, file_id: int):
        """Get managed file by ID.

        Args:
            file_id: File ID.

        Returns:
            ManagedFile: The managed file record.

        Raises:
            NotFoundError: If file not found.
        """
        from scholarr.db.models import ManagedFile

        result = await self.session.execute(select(ManagedFile).where(ManagedFile.id == file_id))
        file = result.scalar_one_or_none()

        if not file:
            raise NotFoundError(f"File {file_id} not found")

        return file

    async def create(self, data: dict):
        """Create a new managed file record.

        Args:
            data: Dictionary containing file data.

        Returns:
            ManagedFile: The created managed file.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import ManagedFile

        required_fields = ["filename", "path", "academic_item_id"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        managed_file = ManagedFile(**data)
        self.session.add(managed_file)
        await self.session.commit()
        await self.session.refresh(managed_file)

        return managed_file

    async def update(self, file_id: int, data: dict):
        """Update an existing managed file.

        Args:
            file_id: File ID.
            data: Dictionary of fields to update.

        Returns:
            ManagedFile: The updated managed file.

        Raises:
            NotFoundError: If file not found.
        """
        managed_file = await self.get_by_id(file_id)

        for key, value in data.items():
            if hasattr(managed_file, key):
                setattr(managed_file, key, value)

        self.session.add(managed_file)
        await self.session.commit()
        await self.session.refresh(managed_file)

        return managed_file

    async def delete(self, file_id: int):
        """Delete a managed file record.

        Args:
            file_id: File ID.

        Raises:
            NotFoundError: If file not found.
        """
        managed_file = await self.get_by_id(file_id)
        await self.session.delete(managed_file)
        await self.session.commit()

    async def get_by_hash(self, file_hash: str) -> Optional[object]:
        """Get managed file by content hash.

        Args:
            file_hash: SHA256 hash of file content.

        Returns:
            ManagedFile: The managed file with matching hash, or None.
        """
        from scholarr.db.models import ManagedFile

        result = await self.session.execute(
            select(ManagedFile).where(ManagedFile.hash == file_hash)
        )
        return result.scalar_one_or_none()
