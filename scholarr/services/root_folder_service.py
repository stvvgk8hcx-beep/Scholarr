"""Root Folder service."""

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import RootFolder
from scholarr.schemas.root_folder import (
    RootFolderCreate,
    RootFolderUpdate,
    RootFolderResponse,
    RootFolderListResponse,
)

logger = logging.getLogger(__name__)


class RootFolderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_root_folders_with_info(self) -> list[RootFolderResponse]:
        result = await self.db.execute(select(RootFolder).order_by(RootFolder.name))
        return [RootFolderResponse.model_validate(row) for row in result.scalars().all()]

    async def list_root_folders_paginated(self, page: int, page_size: int) -> RootFolderListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(RootFolder))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(RootFolder).order_by(RootFolder.name).offset(offset).limit(page_size)
        )
        items = [RootFolderResponse.model_validate(row) for row in result.scalars().all()]
        return RootFolderListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_root_folder_with_info(self, id: int) -> RootFolderResponse | None:
        obj = await self.db.get(RootFolder, id)
        return RootFolderResponse.model_validate(obj) if obj else None

    async def create_root_folder(self, folder: RootFolderCreate) -> RootFolderResponse:
        obj = RootFolder(**folder.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created root folder id={obj.id} path={obj.path!r}")
        return RootFolderResponse.model_validate(obj)

    async def update_root_folder(
        self, id: int, folder_update: RootFolderUpdate
    ) -> RootFolderResponse | None:
        obj = await self.db.get(RootFolder, id)
        if not obj:
            return None
        for key, value in folder_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return RootFolderResponse.model_validate(obj)

    async def delete_root_folder(self, id: int) -> bool:
        obj = await self.db.get(RootFolder, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted root folder id={id}")
        return True
