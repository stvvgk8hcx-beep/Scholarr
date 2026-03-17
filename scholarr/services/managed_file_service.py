"""Managed File service."""

import logging
import shutil
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import ManagedFile, AcademicItem, Course, HistoryEntry, HistoryEventTypeEnum
from scholarr.schemas.managed_file import (
    ManagedFileCreate,
    ManagedFileUpdate,
    ManagedFileResponse,
    ManagedFileListResponse,
)

logger = logging.getLogger(__name__)


async def _enrich_files(
    files: list[ManagedFileResponse], db: AsyncSession
) -> list[ManagedFileResponse]:
    """Batch-fetch item names and course codes for file responses."""
    if not files:
        return files
    item_ids = {f.academic_item_id for f in files}
    result = await db.execute(
        select(AcademicItem.id, AcademicItem.name, AcademicItem.course_id)
        .where(AcademicItem.id.in_(item_ids))
    )
    item_map = {row.id: (row.name, row.course_id) for row in result}

    course_ids = {cid for _, (_, cid) in item_map.items() if cid}
    code_map = {}
    if course_ids:
        cr = await db.execute(
            select(Course.id, Course.code).where(Course.id.in_(course_ids))
        )
        code_map = {row.id: row.code for row in cr}

    for f in files:
        item_name, course_id = item_map.get(f.academic_item_id, (None, None))
        f.item_name = item_name
        f.course_id = course_id
        f.course_code = code_map.get(course_id) if course_id else None
    return files


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
        files = [ManagedFileResponse.model_validate(row) for row in result.scalars().all()]
        return await _enrich_files(files, self.db)

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
        items = await _enrich_files(items, self.db)
        return ManagedFileListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_managed_file(self, id: int) -> ManagedFileResponse | None:
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return None
        files = await _enrich_files([ManagedFileResponse.model_validate(obj)], self.db)
        return files[0]

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

    async def rename_file(self, id: int, new_name: str) -> ManagedFileResponse | None:
        """Rename a file on disk and update DB record. Creates history entry."""
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return None
        old_path = Path(obj.path)
        new_path = old_path.parent / new_name
        if new_path.exists() and new_path != old_path:
            stem = Path(new_name).stem
            suffix = Path(new_name).suffix
            counter = 1
            while new_path.exists():
                new_path = old_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
        if old_path.exists():
            shutil.move(str(old_path), str(new_path))
        old_name = obj.original_filename or old_path.name
        obj.path = str(new_path)
        obj.original_filename = new_name
        item = await self.db.get(AcademicItem, obj.academic_item_id)
        entry = HistoryEntry(
            managed_file_id=obj.id,
            course_id=item.course_id if item else None,
            academic_item_id=obj.academic_item_id,
            event_type=HistoryEventTypeEnum.RENAME,
            source_path=old_name,
            destination_path=new_name,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Renamed file {id}: {old_name} -> {new_name}")
        files = await _enrich_files([ManagedFileResponse.model_validate(obj)], self.db)
        return files[0]

    async def move_file(
        self, id: int, new_academic_item_id: int
    ) -> ManagedFileResponse | None:
        """Move a file to a different academic item. Creates history entry."""
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return None
        new_item = await self.db.get(AcademicItem, new_academic_item_id)
        if not new_item:
            return None
        old_item_id = obj.academic_item_id
        old_name = obj.original_filename or obj.path
        obj.academic_item_id = new_academic_item_id
        entry = HistoryEntry(
            managed_file_id=obj.id,
            course_id=new_item.course_id,
            academic_item_id=new_academic_item_id,
            event_type=HistoryEventTypeEnum.MOVE,
            source_path=f"item:{old_item_id}",
            destination_path=f"item:{new_academic_item_id}",
            data={"old_item_id": old_item_id, "new_item_id": new_academic_item_id, "filename": old_name},
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Moved file {id} from item {old_item_id} to {new_academic_item_id}")
        files = await _enrich_files([ManagedFileResponse.model_validate(obj)], self.db)
        return files[0]

    async def delete_managed_file(self, id: int, delete_from_disk: bool = False) -> bool:
        obj = await self.db.get(ManagedFile, id)
        if not obj:
            return False
        if delete_from_disk:
            try:
                p = Path(obj.path)
                if p.exists():
                    p.unlink()
            except Exception as e:
                logger.warning(f"Could not delete file from disk {obj.path}: {e}")
        item = await self.db.get(AcademicItem, obj.academic_item_id)
        entry = HistoryEntry(
            managed_file_id=obj.id,
            course_id=item.course_id if item else None,
            academic_item_id=obj.academic_item_id,
            event_type=HistoryEventTypeEnum.DELETE,
            source_path=obj.original_filename or obj.path,
        )
        self.db.add(entry)
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted managed file id={id}")
        return True
