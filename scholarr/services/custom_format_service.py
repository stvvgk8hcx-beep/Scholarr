"""Custom Format service."""

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import CustomFormat
from scholarr.schemas.custom_format import (
    CustomFormatCreate,
    CustomFormatUpdate,
    CustomFormatResponse,
    CustomFormatListResponse,
)

logger = logging.getLogger(__name__)


class CustomFormatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_custom_formats(self) -> list[CustomFormatResponse]:
        result = await self.db.execute(select(CustomFormat).order_by(CustomFormat.name))
        return [CustomFormatResponse.model_validate(row) for row in result.scalars().all()]

    async def list_custom_formats_paginated(self, page: int, page_size: int) -> CustomFormatListResponse:
        offset = (page - 1) * page_size
        total_result = await self.db.execute(select(func.count()).select_from(CustomFormat))
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(CustomFormat).order_by(CustomFormat.name).offset(offset).limit(page_size)
        )
        items = [CustomFormatResponse.model_validate(row) for row in result.scalars().all()]
        return CustomFormatListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_custom_format(self, id: int) -> CustomFormatResponse | None:
        obj = await self.db.get(CustomFormat, id)
        return CustomFormatResponse.model_validate(obj) if obj else None

    async def create_custom_format(self, fmt: CustomFormatCreate) -> CustomFormatResponse:
        obj = CustomFormat(**fmt.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created custom format id={obj.id} name={obj.name!r}")
        return CustomFormatResponse.model_validate(obj)

    async def update_custom_format(
        self, id: int, format_update: CustomFormatUpdate
    ) -> CustomFormatResponse | None:
        obj = await self.db.get(CustomFormat, id)
        if not obj:
            return None
        for key, value in format_update.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return CustomFormatResponse.model_validate(obj)

    async def delete_custom_format(self, id: int) -> bool:
        obj = await self.db.get(CustomFormat, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted custom format id={id}")
        return True
