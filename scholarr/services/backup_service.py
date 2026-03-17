"""Backup and restore service for database and configuration."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.config import settings
from scholarr.db.models import (
    Semester,
    Course,
    AcademicItem,
    ManagedFile,
    HistoryEntry,
    Tag,
    course_tags,
)

logger = logging.getLogger(__name__)

# Backup format version for forward compatibility
_BACKUP_VERSION = 1

# Tables to back up, in dependency order (parents before children)
_TABLE_MODELS = [
    ("semesters", Semester),
    ("tags", Tag),
    ("courses", Course),
    ("academic_items", AcademicItem),
    ("files", ManagedFile),
    ("history", HistoryEntry),
]


def _row_to_dict(row: Any) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict.

    Handles datetime and enum serialisation so the result is
    JSON-safe without a custom encoder.
    """
    d: dict[str, Any] = {}
    mapper = row.__class__.__mapper__
    for col in mapper.columns:
        value = getattr(row, col.key)
        if isinstance(value, datetime):
            d[col.key] = value.isoformat()
        elif hasattr(value, "value"):
            # Enum – store the underlying string value
            d[col.key] = value.value
        else:
            d[col.key] = value
    return d


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-format string back to a datetime, or return None."""
    if value is None:
        return None
    # fromisoformat handles the common formats we emit
    return datetime.fromisoformat(value)


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backup_dir = Path(settings.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    async def list_backups(self) -> dict:
        """List all available backups with metadata.

        Returns a dict matching ``BackupListResponse``:
        ``{"backups": [...], "total_count": N, "total_size": N}``
        """
        try:
            backups: list[dict] = []

            for path in sorted(
                self.backup_dir.glob("*.json"), key=os.path.getmtime, reverse=True
            ):
                stat = path.stat()
                backup_id = path.stem  # e.g. "backup_20260317_143012"

                # Try to read the created_at from the file metadata inside
                created_at = self._created_at_from_filename(backup_id)
                if created_at is None:
                    created_at = datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    )

                backups.append(
                    {
                        "id": backup_id,
                        "filename": path.name,
                        "size": stat.st_size,
                        "created_at": created_at.isoformat(),
                        "description": None,
                    }
                )

            return {
                "backups": backups,
                "total_count": len(backups),
                "total_size": sum(b["size"] for b in backups),
            }
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return {"backups": [], "total_count": 0, "total_size": 0}

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    async def create_backup(self) -> dict:
        """Export all tables to a JSON file in ``backup_dir``.

        Returns a dict matching ``BackupResponse``.
        """
        now = datetime.now(timezone.utc)
        backup_id = "backup_" + now.strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_id}.json"
        filepath = self.backup_dir / filename

        try:
            data: dict[str, Any] = {
                "version": _BACKUP_VERSION,
                "created_at": now.isoformat(),
                "backup_id": backup_id,
            }

            # --- Dump each model table ---
            for key, model in _TABLE_MODELS:
                result = await self.db.execute(select(model))
                rows = result.scalars().all()
                data[key] = [_row_to_dict(r) for r in rows]

            # --- Dump many-to-many association: course_tags ---
            result = await self.db.execute(select(course_tags))
            data["course_tags"] = [
                {"course_id": row.course_id, "tag_id": row.tag_id}
                for row in result.fetchall()
            ]

            # Write to disk
            filepath.write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8"
            )

            size = filepath.stat().st_size
            logger.info(
                "Backup created: %s (%d bytes, %d semesters, %d courses, "
                "%d items, %d files, %d history, %d tags, %d course_tags)",
                filename,
                size,
                len(data["semesters"]),
                len(data["courses"]),
                len(data["academic_items"]),
                len(data["files"]),
                len(data["history"]),
                len(data["tags"]),
                len(data["course_tags"]),
            )

            return {
                "id": backup_id,
                "filename": filename,
                "size": size,
                "created_at": now.isoformat(),
                "description": None,
            }
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            # Clean up partial file
            if filepath.exists():
                filepath.unlink()
            raise

    # ------------------------------------------------------------------
    # restore
    # ------------------------------------------------------------------

    async def restore_backup(self, backup_id: str) -> dict:
        """Read a JSON backup file and re-import all records.

        Returns a dict matching ``BackupRestoreResponse``.
        """
        filepath = self.backup_dir / f"{backup_id}.json"

        if not filepath.exists():
            return {
                "success": False,
                "message": f"Backup '{backup_id}' not found",
                "error": f"Backup '{backup_id}' not found",
            }

        try:
            raw = filepath.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
        except (json.JSONDecodeError, OSError) as e:
            return {
                "success": False,
                "message": f"Failed to read backup file: {e}",
                "error": f"Failed to read backup file: {e}",
            }

        try:
            counts: dict[str, int] = {}

            # Delete existing data in reverse dependency order so FK
            # constraints are satisfied.
            for key, model in reversed(_TABLE_MODELS):
                await self.db.execute(
                    text(f"DELETE FROM {model.__tablename__}")
                )
            # Clear association table
            await self.db.execute(text("DELETE FROM course_tags"))

            await self.db.flush()

            # --- Re-import rows in dependency order ---
            for key, model in _TABLE_MODELS:
                rows = data.get(key, [])
                for row_dict in rows:
                    obj = self._dict_to_model(model, row_dict)
                    self.db.add(obj)
                counts[key] = len(rows)

            # Flush so PKs are available before inserting association rows
            await self.db.flush()

            # --- Re-import course_tags association ---
            ct_rows = data.get("course_tags", [])
            for ct in ct_rows:
                await self.db.execute(
                    course_tags.insert().values(
                        course_id=ct["course_id"], tag_id=ct["tag_id"]
                    )
                )
            counts["course_tags"] = len(ct_rows)

            await self.db.commit()

            logger.info("Backup restored: %s  counts=%s", backup_id, counts)

            return {
                "success": True,
                "message": "Backup restored successfully",
                "details": {
                    "backup_id": backup_id,
                    "restored_at": datetime.now(timezone.utc).isoformat(),
                    "record_counts": counts,
                },
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return {
                "success": False,
                "message": f"Restore failed: {e}",
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete the backup file identified by *backup_id*.

        Returns ``True`` on success, ``False`` if the file was not found.
        """
        filepath = self.backup_dir / f"{backup_id}.json"
        if not filepath.exists():
            logger.warning("Backup not found for deletion: %s", backup_id)
            return False

        try:
            filepath.unlink()
            logger.info("Backup deleted: %s", backup_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            return False

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _created_at_from_filename(backup_id: str) -> datetime | None:
        """Try to parse a UTC datetime from a backup ID like
        ``backup_20260317_143012``.
        """
        prefix = "backup_"
        if not backup_id.startswith(prefix):
            return None
        ts_part = backup_id[len(prefix):]
        try:
            return datetime.strptime(ts_part, "%Y%m%d_%H%M%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

    @staticmethod
    def _dict_to_model(model: type, row: dict) -> Any:
        """Instantiate a SQLAlchemy model from a plain dict, coercing
        datetime strings back to ``datetime`` objects.
        """
        mapper = model.__mapper__
        kwargs: dict[str, Any] = {}
        for col in mapper.columns:
            key = col.key
            if key not in row:
                continue
            value = row[key]
            col_type = col.type

            # Coerce datetime strings
            if isinstance(col_type, type) or hasattr(col_type, "impl"):
                pass  # handled below
            if value is not None and hasattr(col_type, "python_type"):
                try:
                    if col_type.python_type is datetime:
                        value = _parse_datetime(value)
                except NotImplementedError:
                    pass

            kwargs[key] = value

        return model(**kwargs)
