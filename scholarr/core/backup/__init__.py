"""Backup and restore service for Scholarr."""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from scholarr.core.config import get_settings
from scholarr.core.exceptions import BackupError


class BackupService:
    """Service for managing database backups."""

    @staticmethod
    def get_backup_dir() -> Path:
        """Get backup directory path.

        Returns:
            Path: Backup directory.
        """
        backup_dir = Path.home() / ".scholarr" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    @staticmethod
    async def create_backup() -> str:
        """Create a database backup.

        Returns:
            str: Path to the backup file.

        Raises:
            BackupError: If backup fails.
        """
        settings = get_settings()
        backup_dir = BackupService.get_backup_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if "sqlite" in settings.database_url:
            db_path = settings.database_url.split("///")[-1]

            if not os.path.exists(db_path):
                raise BackupError(f"Database file not found: {db_path}")

            backup_path = backup_dir / f"scholarr_{timestamp}.db"

            try:
                shutil.copy2(db_path, backup_path)
                return str(backup_path)
            except Exception as e:
                raise BackupError(f"Failed to backup SQLite database: {e}")

        elif "postgresql" in settings.database_url:
            backup_path = backup_dir / f"scholarr_{timestamp}.sql"

            try:
                parts = settings.database_url.replace("postgresql+asyncpg://", "").split("/")
                if "@" in parts[0]:
                    auth, host = parts[0].split("@")
                    user, password = auth.split(":")
                else:
                    user = "postgres"
                    password = ""
                    host = parts[0]

                db_name = parts[1] if len(parts) > 1 else "scholarr"

                env = os.environ.copy()
                if password:
                    env["PGPASSWORD"] = password

                cmd = ["pg_dump", "-h", host, "-U", user, "-d", db_name]

                with open(backup_path, "w") as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)

                return str(backup_path)

            except subprocess.CalledProcessError as e:
                raise BackupError(f"Failed to backup PostgreSQL database: {e}")
            except Exception as e:
                raise BackupError(f"Backup failed: {e}")

        else:
            raise BackupError(f"Unsupported database: {settings.database_url}")

    @staticmethod
    async def restore_backup(backup_path: str) -> None:
        """Restore a database from backup.

        Args:
            backup_path: Path to the backup file.

        Raises:
            BackupError: If restore fails.
        """
        settings = get_settings()

        if not os.path.exists(backup_path):
            raise BackupError(f"Backup file not found: {backup_path}")

        if "sqlite" in settings.database_url:
            db_path = settings.database_url.split("///")[-1]

            try:
                shutil.copy2(backup_path, db_path)
            except Exception as e:
                raise BackupError(f"Failed to restore SQLite database: {e}")

        elif "postgresql" in settings.database_url:
            try:
                parts = settings.database_url.replace("postgresql+asyncpg://", "").split("/")
                if "@" in parts[0]:
                    auth, host = parts[0].split("@")
                    user, password = auth.split(":")
                else:
                    user = "postgres"
                    password = ""
                    host = parts[0]

                db_name = parts[1] if len(parts) > 1 else "scholarr"

                env = os.environ.copy()
                if password:
                    env["PGPASSWORD"] = password

                with open(backup_path, "r") as f:
                    cmd = ["psql", "-h", host, "-U", user, "-d", db_name]
                    subprocess.run(cmd, stdin=f, env=env, check=True)

            except subprocess.CalledProcessError as e:
                raise BackupError(f"Failed to restore PostgreSQL database: {e}")
            except Exception as e:
                raise BackupError(f"Restore failed: {e}")

        else:
            raise BackupError(f"Unsupported database: {settings.database_url}")

    @staticmethod
    def list_backups() -> list[dict]:
        """List all available backups.

        Returns:
            list[dict]: List of backup metadata.
        """
        backup_dir = BackupService.get_backup_dir()

        if not backup_dir.exists():
            return []

        backups = []
        for backup_file in sorted(backup_dir.glob("scholarr_*.db"), reverse=True):
            stat = backup_file.stat()
            backups.append(
                {
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime),
                }
            )

        return backups

    @staticmethod
    def delete_backup(backup_path: str) -> None:
        """Delete a backup file.

        Args:
            backup_path: Path to the backup file.

        Raises:
            BackupError: If deletion fails.
        """
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {e}")
