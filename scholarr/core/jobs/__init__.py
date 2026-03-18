"""Job queue and command processing service for Scholarr."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import JobError, NotFoundError

logger = logging.getLogger(__name__)


class CommandPriority(str, Enum):
    """Command priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class CommandService:
    """Service for managing commands and background jobs."""

    def __init__(self, session: AsyncSession):
        """Initialize command service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session
        self.scheduler = AsyncIOScheduler()
        self._callbacks: dict[str, list[Callable]] = {}

    async def queue_command(
        self,
        name: str,
        body: dict[str, Any],
        priority: str = CommandPriority.NORMAL,
    ):
        """Queue a new command for processing.

        Args:
            name: Command name.
            body: Command body/parameters.
            priority: Command priority (low, normal, high).

        Returns:
            Command: The queued command.
        """
        from scholarr.db.models import CommandModel as Command

        command = Command(
            name=name,
            body=body,
            priority=priority,
            status="queued",
            created_at=datetime.utcnow(),
        )

        self.session.add(command)
        await self.session.commit()
        await self.session.refresh(command)

        return command

    async def get_command(self, command_id: int):
        """Get command by ID.

        Args:
            command_id: Command ID.

        Returns:
            Command: The command record.

        Raises:
            NotFoundError: If command not found.
        """
        from scholarr.db.models import CommandModel as Command

        result = await self.session.execute(select(Command).where(Command.id == command_id))
        command = result.scalar_one_or_none()

        if not command:
            raise NotFoundError(f"Command {command_id} not found")

        return command

    async def get_all_commands(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list:
        """Get all commands with optional filtering.

        Args:
            status: Filter by status (queued, processing, completed, failed).
            limit: Maximum number of results.

        Returns:
            list: List of command records.
        """
        from scholarr.db.models import CommandModel as Command

        query = select(Command)

        if status:
            query = query.where(Command.status == status)

        query = query.order_by(
            Command.priority.desc(),
            Command.created_at.asc(),
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_command_status(
        self,
        command_id: int,
        status: str,
        result: dict | None = None,
        error: str | None = None,
    ):
        """Update command status.

        Args:
            command_id: Command ID.
            status: New status.
            result: Optional result data.
            error: Optional error message.
        """
        command = await self.get_command(command_id)

        command.status = status
        if result:
            command.result = result
        if error:
            command.error = error
        if status == "completed":
            command.completed_at = datetime.utcnow()

        self.session.add(command)
        await self.session.commit()

    async def process_commands(self) -> int:
        """Process queued commands.

        Returns:
            int: Number of commands processed.
        """
        from scholarr.db.models import CommandModel as Command

        result = await self.session.execute(
            select(Command)
            .where(Command.status == "queued")
            .order_by(
                Command.priority.desc(),
                Command.created_at.asc(),
            )
            .limit(10)
        )
        commands = result.scalars().all()

        processed = 0

        for command in commands:
            try:
                await self.update_command_status(command.id, "processing")
                command_result = await self._execute_command(command)
                await self.update_command_status(command.id, "completed", command_result)
                processed += 1

            except Exception as e:
                logger.error(f"Command {command.id} failed: {e}")
                await self.update_command_status(command.id, "failed", error=str(e))

        return processed

    async def _execute_command(self, command) -> dict:
        """Execute a command.

        Args:
            command: Command record.

        Returns:
            dict: Command result.

        Raises:
            JobError: If command execution fails.
        """
        callbacks = self._callbacks.get(command.name, [])

        if not callbacks:
            raise JobError(f"No handler for command: {command.name}")

        for callback in callbacks:
            result = await callback(command.body) if asyncio.iscoroutinefunction(callback) else callback(command.body)

            if result is False:
                raise JobError(f"Command handler failed: {command.name}")

        return {"executed_at": datetime.utcnow().isoformat()}

    def on_command(self, command_name: str):
        """Decorator to register a command handler.

        Args:
            command_name: Name of command to handle.

        Returns:
            Callable: Decorator function.
        """
        def decorator(func: Callable):
            if command_name not in self._callbacks:
                self._callbacks[command_name] = []
            self._callbacks[command_name].append(func)
            return func

        return decorator

    def start_scheduler(self):
        """Start the APScheduler scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()

    def stop_scheduler(self):
        """Stop the APScheduler scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_job(
        self,
        name: str,
        func: Callable,
        cron_expression: str,
    ):
        """Schedule a recurring job using cron expression.

        Args:
            name: Job name.
            func: Function to execute.
            cron_expression: Cron expression (minute, hour, day, month, day_of_week).
        """
        parts = cron_expression.split()
        if len(parts) != 5:
            raise JobError("Invalid cron expression")

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=name,
            name=name,
            replace_existing=True,
        )
