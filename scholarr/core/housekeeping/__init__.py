"""Housekeeping and maintenance service for Scholarr."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import MaintenanceError


class HousekeepingService:
    """Service for performing maintenance tasks."""

    def __init__(self, session: AsyncSession):
        """Initialize housekeeping service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def cleanup_old_commands(self, days: int = 30) -> int:
        """Clean up old command records.

        Args:
            days: Number of days to keep.

        Returns:
            int: Number of records deleted.
        """
        from scholarr.db.models import CommandModel as Command

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(Command).where(Command.created_at < cutoff_date)
        )
        records = list(result.scalars().all())
        count = len(records)

        for record in records:
            await self.session.delete(record)

        if count > 0:
            await self.session.commit()

        return count

    async def cleanup_old_history(self, days: int = 365) -> int:
        """Clean up old history records.

        Args:
            days: Number of days to keep.

        Returns:
            int: Number of records deleted.
        """
        from scholarr.db.models import HistoryEntry as History

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(History).where(History.timestamp < cutoff_date)
        )
        records = list(result.scalars().all())
        count = len(records)

        for record in records:
            await self.session.delete(record)

        if count > 0:
            await self.session.commit()

        return count

    async def cleanup_orphaned_files(self) -> int:
        """Clean up file records with no associated academic item.

        Returns:
            int: Number of records deleted.
        """
        from scholarr.db.models import ManagedFile

        result = await self.session.execute(select(ManagedFile))
        all_files = list(result.scalars().all())

        orphaned_count = 0

        for managed_file in all_files:
            if not managed_file.academic_item:
                await self.session.delete(managed_file)
                orphaned_count += 1

        if orphaned_count > 0:
            await self.session.commit()

        return orphaned_count

    async def run_all(self) -> dict:
        """Run all housekeeping tasks.

        Returns:
            dict: Results of each cleanup operation.
        """
        try:
            old_commands = await self.cleanup_old_commands()
            old_history = await self.cleanup_old_history()
            orphaned = await self.cleanup_orphaned_files()

            return {
                "old_commands": old_commands,
                "old_history": old_history,
                "orphaned_files": orphaned,
                "success": True,
            }
        except Exception as e:
            raise MaintenanceError(f"Housekeeping failed: {e}") from e
