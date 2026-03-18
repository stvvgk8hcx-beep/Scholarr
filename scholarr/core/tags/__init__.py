"""Tags management service for Scholarr."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationError


class TagService:
    """Service for managing tags."""

    def __init__(self, session: AsyncSession):
        """Initialize tag service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all tags.

        Returns:
            list: List of tag records.
        """
        from scholarr.db.models import Tag

        result = await self.session.execute(select(Tag))
        return list(result.scalars().all())

    async def get_by_id(self, tag_id: int):
        """Get tag by ID.

        Args:
            tag_id: Tag ID.

        Returns:
            Tag: The tag record.

        Raises:
            NotFoundError: If tag not found.
        """
        from scholarr.db.models import Tag

        result = await self.session.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()

        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")

        return tag

    async def create(self, data: dict):
        """Create a new tag.

        Args:
            data: Dictionary containing tag data.

        Returns:
            Tag: The created tag.

        Raises:
            ValidationError: If data is invalid.
        """
        from scholarr.db.models import Tag

        if "name" not in data:
            raise ValidationError("Missing required field: name")

        tag = Tag(**data)
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)

        return tag

    async def update(self, tag_id: int, data: dict):
        """Update an existing tag.

        Args:
            tag_id: Tag ID.
            data: Dictionary of fields to update.

        Returns:
            Tag: The updated tag.

        Raises:
            NotFoundError: If tag not found.
        """
        tag = await self.get_by_id(tag_id)

        for key, value in data.items():
            if hasattr(tag, key):
                setattr(tag, key, value)

        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)

        return tag

    async def delete(self, tag_id: int):
        """Delete a tag.

        Args:
            tag_id: Tag ID.

        Raises:
            NotFoundError: If tag not found.
        """
        tag = await self.get_by_id(tag_id)
        await self.session.delete(tag)
        await self.session.commit()
