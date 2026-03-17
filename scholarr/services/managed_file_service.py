"""Managed File service."""

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import ManagedFile
from scholarr.schemas.managed_file import (
    ManagedFileCreate,
    ManagedFileUpdate,
    ManagedFileResponse,
    ManagedFileListResponse,
)

logger = logging.getLogger(__name__)


class ManagedFileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_managed_files(
        self, academic_item_id: int | None = None
    ) -> list[ManagedFileResponse]:
        query = select(ManagedFile)
        if academic_item_id is not None:
            query = query.where(ManagedFile.academic_item_id == academic_item_id)
        query = query.order_by(ManagedFile.date_imported.desc())
        result = await self.db.execute(query)
        return [ManagedFileResponse.model_validate(row) for row in result.scalars().all()]

    async def list_managed_files_paginated(
        self, page: int, page_size: int
    ) -> ManagedFileListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(ManagedFile))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(ManagedFile).order_by(ManagedFile.date_imported.desc()).offset(offset).limit(page_size)
        )
        items = [ManagedFileResponse.model_validate(row) for row in result.scalars().all()]
        return ManagedFileListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_managed_file(self, id: int) -> ManagedFileResponse | None:
        obj = await self.db.get(ManagedFile, id)
        return ManagedFileResponse.model_validate(obj) if obj else None

    async def get_by_hash(self, hash: str) -> ManagedFileResponse | None:
        result = await self.db.execute(select(ManagedFile).where(ManagedFile.hash == hash))
        obj = result.scalar_one_or_none()
        return ManagedFileResponse.model_validate(obj) if obj else None

    async def create_managed_file(self, file: ManagedFileCreate) -> ManagedFileResponse:
        obj = ManagedFile(**file.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created managed file id={obj.id} path={obj.path!r}")
        return ManagedFileResponse.model_validate(obj)

    async def update_managed_file(
        self, id: int, file_update: ManagedFileUpdate
    ) -> ManagedFileResponse | None:
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return None
        for key, value in file_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return ManagedFileResponse.model_validate(obj)

    async def delete_managed_file(self, id: int) -> bool:
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted managed file id={id}")
        return True
