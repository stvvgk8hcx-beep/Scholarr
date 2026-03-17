"""Manual import service for file imports and previews."""

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from scholarr.core.config import get_settings
from scholarr.db.models import AcademicItem, ManagedFile, HistoryEntry, HistoryEventTypeEnum

logger = logging.getLogger(__name__)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ManualImportService:
    """Service for manually importing files and previewing imports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    def _upload_dir(self) -> Path:
        d = Path(self.settings.upload_dir)
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def preview_import(
        self, file_paths: List[str], course_id: Optional[int] = None
    ) -> dict:
        """Preview how files would be parsed without importing."""
        previews = []
        for fp in file_paths:
            p = Path(fp)
            if not p.exists():
                previews.append({"file_path": fp, "suggested_name": p.name, "error": "File not found"})
                continue
            ext = p.suffix.lower().lstrip(".")
            previews.append({
                "file_path": fp,
                "suggested_name": p.stem,
                "suggested_type": ext or "unknown",
                "metadata": {"size": p.stat().st_size, "extension": ext},
            })
        return {"previews": previews, "total_files": len(file_paths)}

    async def execute_import(self, file_paths: List[str], course_id: int) -> dict:
        """Execute import of local file paths into the library."""
        imported_count = 0
        failed_count = 0
        errors = []
        upload_dir = self._upload_dir()

        for fp in file_paths:
            try:
                src = Path(fp)
                if not src.exists():
                    errors.append(f"{fp}: file not found")
                    failed_count += 1
                    continue
                data = src.read_bytes()
                file_hash = _sha256(data)

                # Check duplicate
                existing = (await self.db.execute(
                    select(ManagedFile).where(ManagedFile.hash == file_hash)
                )).scalar_one_or_none()
                if existing:
                    errors.append(f"{fp}: duplicate (already imported)")
                    failed_count += 1
                    continue

                dest = upload_dir / src.name
                # Avoid overwriting
                counter = 1
                while dest.exists():
                    dest = upload_dir / f"{src.stem}_{counter}{src.suffix}"
                    counter += 1
                shutil.copy2(src, dest)

                entry = HistoryEntry(
                    event_type=HistoryEventTypeEnum.IMPORT,
                    source_path=str(src),
                    destination_path=str(dest),
                )
                self.db.add(entry)
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing {fp}: {e}")
                errors.append(f"{fp}: {e}")
                failed_count += 1

        await self.db.commit()
        return {
            "success": failed_count == 0,
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors,
            "file_id": None,
        }

    async def manual_import(self, file, academic_item_id: int) -> dict:
        """Import an uploaded file and associate it with an academic item."""
        # Validate academic item exists
        item = await self.db.get(AcademicItem, academic_item_id)
        if not item:
            return {"success": False, "error": f"Academic item {academic_item_id} not found"}

        try:
            data = await file.read()
            if len(data) == 0:
                return {"success": False, "message": "Empty file", "imported_count": 0, "failed_count": 1, "errors": ["File is empty"]}
            file_hash = _sha256(data)

            # Check duplicate
            existing = (await self.db.execute(
                select(ManagedFile).where(ManagedFile.hash == file_hash)
            )).scalar_one_or_none()
            if existing:
                return {
                    "success": False,
                    "message": "File already imported (duplicate)",
                    "file_id": existing.id,
                    "imported_count": 0,
                    "failed_count": 1,
                    "errors": ["File already imported (duplicate)"],
                }

            upload_dir = self._upload_dir()
            original_name = file.filename or "upload"
            dest = upload_dir / original_name
            counter = 1
            while dest.exists():
                p = Path(original_name)
                dest = upload_dir / f"{p.stem}_{counter}{p.suffix}"
                counter += 1
            dest.write_bytes(data)

            mf = ManagedFile(
                academic_item_id=academic_item_id,
                path=str(dest),
                original_filename=original_name,
                size=len(data),
                format=Path(original_name).suffix.lower().lstrip(".") or None,
                hash=file_hash,
            )
            self.db.add(mf)
            await self.db.flush()

            entry = HistoryEntry(
                course_id=item.course_id,
                academic_item_id=academic_item_id,
                managed_file_id=mf.id,
                event_type=HistoryEventTypeEnum.IMPORT,
                source_path=original_name,
                destination_path=str(dest),
            )
            self.db.add(entry)
            await self.db.commit()

            logger.info(f"Imported file {original_name} -> {dest} for item {academic_item_id}")
            return {
                "success": True,
                "message": "File imported successfully",
                "file_id": mf.id,
                "imported_count": 1,
                "failed_count": 0,
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error importing file: {e}")
            await self.db.rollback()
            return {"success": False, "message": str(e), "imported_count": 0, "failed_count": 1, "errors": [str(e)]}
