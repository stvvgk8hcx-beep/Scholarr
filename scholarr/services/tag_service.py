"""Tag service for business logic."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Tag
from scholarr.schemas.tag import TagCreate, TagResponse, TagUpdate

logger = logging.getLogger(__name__)


class TagService:
    """Service for tag operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tags(self) -> list[TagResponse]:
        """List all tags."""
        result = await self.db.execute(select(Tag).order_by(Tag.label))
        return [TagResponse.model_validate(row) for row in result.scalars().all()]

    async def get_tag(self, id: int) -> TagResponse | None:
        """Get a tag by ID."""
        obj = await self.db.get(Tag, id)
        return TagResponse.model_validate(obj) if obj else None

    async def create_tag(self, tag: TagCreate) -> TagResponse:
        """Create a new tag."""
        obj = Tag(**tag.model_dump())
        self.db.add(obj)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"A tag with label {tag.label!r} already exists") from None
        await self.db.refresh(obj)
        logger.info(f"Created tag id={obj.id} label={obj.label!r}")
        return TagResponse.model_validate(obj)

    async def update_tag(
        self, id: int, tag_update: TagUpdate
    ) -> TagResponse | None:
        """Update a tag."""
        obj = await self.db.get(Tag, id)
        if not obj:
            return None
        for key, value in tag_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return TagResponse.model_validate(obj)

    async def delete_tag(self, id: int) -> bool:
        """Delete a tag."""
        obj = await self.db.get(Tag, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted tag id={id}")
        return True
