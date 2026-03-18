"""File Profile service."""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import FileProfile
from scholarr.schemas.file_profile import (
    FileProfileCreate,
    FileProfileListResponse,
    FileProfileResponse,
    FileProfileUpdate,
)

logger = logging.getLogger(__name__)


class FileProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_file_profiles(self) -> list[FileProfileResponse]:
        result = await self.db.execute(select(FileProfile).order_by(FileProfile.name))
        return [FileProfileResponse.model_validate(row) for row in result.scalars().all()]

    async def list_file_profiles_paginated(self, page: int, page_size: int) -> FileProfileListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(FileProfile))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(FileProfile).order_by(FileProfile.name).offset(offset).limit(page_size)
        )
        items = [FileProfileResponse.model_validate(row) for row in result.scalars().all()]
        return FileProfileListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_file_profile(self, id: int) -> FileProfileResponse | None:
        obj = await self.db.get(FileProfile, id)
        return FileProfileResponse.model_validate(obj) if obj else None

    async def create_file_profile(self, profile: FileProfileCreate) -> FileProfileResponse:
        obj = FileProfile(**profile.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created file profile id={obj.id} name={obj.name!r}")
        return FileProfileResponse.model_validate(obj)

    async def update_file_profile(
        self, id: int, profile_update: FileProfileUpdate
    ) -> FileProfileResponse | None:
        obj = await self.db.get(FileProfile, id)
        if not obj:
            return None
        for key, value in profile_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return FileProfileResponse.model_validate(obj)

    async def delete_file_profile(self, id: int) -> bool:
        obj = await self.db.get(FileProfile, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted file profile id={id}")
        return True
