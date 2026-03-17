"""Command service."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import CommandModel, CommandStatusEnum
from scholarr.schemas.command import CommandCreate, CommandResponse, CommandListResponse

logger = logging.getLogger(__name__)


class CommandService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_commands(
        self, status: str | None = None, limit: int = 50
    ) -> list[CommandResponse]:
        query = select(CommandModel).order_by(CommandModel.queued_at.desc()).limit(limit)
        if status is not None:
            query = query.where(CommandModel.status == status)
        result = await self.db.execute(query)
        return [CommandResponse.model_validate(row) for row in result.scalars().all()]

    async def get_command(self, id: int) -> CommandResponse | None:
        obj = await self.db.get(CommandModel, id)
        return CommandResponse.model_validate(obj) if obj else None

    async def queue_command(self, command: CommandCreate) -> CommandResponse:
        obj = CommandModel(
            name=command.name,
            body=command.body,
            priority=command.priority,
            trigger=command.trigger,
            status=CommandStatusEnum.QUEUED,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Queued command id={obj.id} name={obj.name!r}")
        return CommandResponse.model_validate(obj)
