"""File System service — rename, move, delete with full history tracking."""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import HistoryEntry, HistoryEventTypeEnum, ManagedFile

logger = logging.getLogger(__name__)


class FileOperationService:
    """Wraps every file rename/move/delete with database history tracking.

    Whenever a file is renamed or moved on disk, the original path and name are
    preserved in ManagedFile.original_path / original_filename, and a HistoryEntry
    row is created so there is always an auditable trail of every change:
        - When the file was changed
        - What the old name / path was
        - What the new name / path is
        - What kind of change it was (Rename / Move / Delete)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def rename_file(
        self,
        managed_file_id: int,
        new_filename: str,
        *,
        reason: Optional[str] = None,
    ) -> ManagedFile:
        """Rename a file on disk and record the change in history.

        The *original* filename is preserved in ManagedFile.original_filename
        (only written the first time a rename happens, so you always know what
        the user actually called the file).

        Args:
            managed_file_id: ID of the ManagedFile row.
            new_filename: Desired new filename (basename only, no path).
            reason: Optional free-text description stored in the history entry.

        Returns:
            Updated ManagedFile row.

        Raises:
            ValueError: If the managed file does not exist.
            FileNotFoundError: If the file no longer exists on disk.
            OSError: If the rename fails for any OS reason.
        """
        mf = await self.db.get(ManagedFile, managed_file_id)
        if not mf:
            raise ValueError(f"ManagedFile {managed_file_id} not found")

        old_path = Path(mf.path)
        if not old_path.exists():
            raise FileNotFoundError(f"File not found on disk: {old_path}")

        new_path = old_path.parent / new_filename
        if new_path == old_path:
            return mf  # Nothing to do

        # Perform rename on disk
        old_path.rename(new_path)
        logger.info(f"Renamed file: {old_path} → {new_path}")

        # Preserve original filename (first rename wins)
        if not mf.original_filename:
            mf.original_filename = old_path.name
        if not mf.original_path:
            mf.original_path = str(old_path)

        old_path_str = mf.path
        mf.path = str(new_path)

        await self.db.commit()
        await self.db.refresh(mf)

        await self._record_history(
            mf,
            event_type=HistoryEventTypeEnum.RENAME,
            source_path=old_path_str,
            destination_path=str(new_path),
            data={
                "old_filename": old_path.name,
                "new_filename": new_filename,
                "original_filename": mf.original_filename,
                "reason": reason,
            },
        )
        return mf

    async def move_file(
        self,
        managed_file_id: int,
        new_directory: str,
        *,
        new_filename: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> ManagedFile:
        """Move a file to a different directory (optionally renaming it too).

        The old directory and filename are captured in HistoryEntry so you can
        always trace where any file came from and when it was moved.

        Args:
            managed_file_id: ID of the ManagedFile row.
            new_directory: Target directory path (will be created if missing).
            new_filename: Optional new basename; keeps the current name if None.
            reason: Optional description stored in history.

        Returns:
            Updated ManagedFile row.
        """
        mf = await self.db.get(ManagedFile, managed_file_id)
        if not mf:
            raise ValueError(f"ManagedFile {managed_file_id} not found")

        old_path = Path(mf.path)
        if not old_path.exists():
            raise FileNotFoundError(f"File not found on disk: {old_path}")

        target_dir = Path(new_directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        dest_name = new_filename or old_path.name
        new_path = target_dir / dest_name

        # Avoid overwriting another file
        counter = 1
        while new_path.exists() and new_path != old_path:
            stem, suffix = old_path.stem, old_path.suffix
            new_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(old_path), str(new_path))
        logger.info(f"Moved file: {old_path} → {new_path}")

        # Preserve original info on first move
        if not mf.original_path:
            mf.original_path = str(old_path)
        if not mf.original_filename:
            mf.original_filename = old_path.name

        old_path_str = mf.path
        mf.path = str(new_path)

        await self.db.commit()
        await self.db.refresh(mf)

        await self._record_history(
            mf,
            event_type=HistoryEventTypeEnum.MOVE,
            source_path=old_path_str,
            destination_path=str(new_path),
            data={
                "old_directory": str(old_path.parent),
                "new_directory": str(new_path.parent),
                "old_filename": old_path.name,
                "new_filename": new_path.name,
                "original_path": mf.original_path,
                "original_filename": mf.original_filename,
                "reason": reason,
            },
        )
        return mf

    async def delete_file(
        self,
        managed_file_id: int,
        *,
        remove_from_disk: bool = False,
        reason: Optional[str] = None,
    ) -> bool:
        """Delete a ManagedFile record (and optionally the physical file).

        A HistoryEntry with event_type=Delete is always written so the audit
        trail shows that the file existed and when it was removed.

        Args:
            managed_file_id: ID of the ManagedFile row.
            remove_from_disk: If True, also delete the physical file.
            reason: Optional description stored in history.

        Returns:
            True if the record was found and deleted.
        """
        mf = await self.db.get(ManagedFile, managed_file_id)
        if not mf:
            return False

        file_path = mf.path

        await self._record_history(
            mf,
            event_type=HistoryEventTypeEnum.DELETE,
            source_path=file_path,
            destination_path=None,
            data={
                "filename": Path(file_path).name,
                "original_filename": mf.original_filename,
                "original_path": mf.original_path,
                "remove_from_disk": remove_from_disk,
                "reason": reason,
            },
        )

        await self.db.delete(mf)
        await self.db.commit()

        if remove_from_disk:
            try:
                p = Path(file_path)
                if p.exists():
                    p.unlink()
                    logger.info(f"Deleted file from disk: {file_path}")
            except OSError as e:
                logger.warning(f"Could not delete file from disk: {e}")

        return True

    async def get_file_history(self, managed_file_id: int) -> list[HistoryEntry]:
        """Return all history entries for a managed file, newest first.

        Args:
            managed_file_id: ID of the ManagedFile row.

        Returns:
            List of HistoryEntry rows ordered by date descending.
        """
        result = await self.db.execute(
            select(HistoryEntry)
            .where(HistoryEntry.managed_file_id == managed_file_id)
            .order_by(HistoryEntry.date.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _record_history(
        self,
        mf: ManagedFile,
        event_type: HistoryEventTypeEnum,
        source_path: Optional[str],
        destination_path: Optional[str],
        data: Optional[dict] = None,
    ) -> None:
        entry = HistoryEntry(
            course_id=mf.academic_item.course_id if mf.academic_item else None,
            academic_item_id=mf.academic_item_id,
            managed_file_id=mf.id,
            source_path=source_path,
            destination_path=destination_path,
            event_type=event_type,
            date=datetime.now(timezone.utc),
            data=data or {},
        )
        self.db.add(entry)
        await self.db.commit()


# Backwards-compat stub kept from the original stub
class FileSystemService(FileOperationService):
    """Alias kept for any existing imports."""

    async def browse_directory(self, path: str) -> list[dict]:
        """Browse a directory in the file system."""
        from pathlib import Path as _Path
        p = _Path(path)
        if not p.is_dir():
            return []
        entries = []
        for child in sorted(p.iterdir()):
            entries.append({
                "name": child.name,
                "path": str(child),
                "is_dir": child.is_dir(),
                "size": child.stat().st_size if child.is_file() else None,
                "modified": datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        return entries
