"""Note service for class notes and writing sessions."""

import json
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Course, Note, NoteBackup
from scholarr.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate

logger = logging.getLogger(__name__)

MAX_BACKUPS_PER_NOTE = 20


async def _enrich_notes(notes: list[NoteResponse], db: AsyncSession) -> list[NoteResponse]:
    """Attach course_code and course_name to note responses."""
    if not notes:
        return notes
    course_ids = {n.course_id for n in notes if n.course_id}
    if not course_ids:
        return notes
    result = await db.execute(
        select(Course.id, Course.code, Course.name).where(Course.id.in_(course_ids))
    )
    course_map = {row.id: (row.code, row.name) for row in result}
    for n in notes:
        if n.course_id and n.course_id in course_map:
            n.course_code, n.course_name = course_map[n.course_id]
    return notes


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notes(
        self,
        course_id: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> NoteListResponse:
        offset = (page - 1) * page_size
        count_q = select(func.count()).select_from(Note)
        data_q = select(Note)

        if course_id is not None:
            count_q = count_q.where(Note.course_id == course_id)
            data_q = data_q.where(Note.course_id == course_id)
        if search:
            pattern = f"%{search}%"
            count_q = count_q.where(Note.title.ilike(pattern))
            data_q = data_q.where(Note.title.ilike(pattern))

        total = (await self.db.execute(count_q)).scalar_one()
        rows = (await self.db.execute(
            data_q.order_by(Note.pinned.desc(), Note.updated_at.desc())
            .offset(offset).limit(page_size)
        )).scalars().all()

        items = [NoteResponse.model_validate(r) for r in rows]
        items = await _enrich_notes(items, self.db)
        return NoteListResponse(
            items=items, total=total, page=page, page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_note(self, id: int) -> NoteResponse | None:
        obj = await self.db.get(Note, id)
        if not obj:
            return None
        items = await _enrich_notes([NoteResponse.model_validate(obj)], self.db)
        return items[0]

    async def create_note(self, data: NoteCreate) -> NoteResponse:
        dump = data.model_dump()
        if dump.get("preferences") is not None:
            dump["preferences"] = json.dumps(dump["preferences"])
        obj = Note(**dump)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info(f"Created note id={obj.id} title={obj.title!r}")
        items = await _enrich_notes([NoteResponse.model_validate(obj)], self.db)
        return items[0]

    async def update_note(self, id: int, data: NoteUpdate) -> NoteResponse | None:
        obj = await self.db.get(Note, id)
        if not obj:
            return None

        # Create backup of current content before overwriting
        if obj.content is not None:
            backup = NoteBackup(
                note_id=obj.id,
                content=obj.content,
                word_count=obj.word_count or 0,
            )
            self.db.add(backup)
            # Prune old backups beyond limit
            await self._prune_backups(obj.id)

        update = data.model_dump(exclude_unset=True)
        # Don't allow setting required fields to None
        update = {k: v for k, v in update.items() if v is not None or k in ("content", "course_id", "preferences")}
        if "preferences" in update and isinstance(update["preferences"], dict):
            update["preferences"] = json.dumps(update["preferences"])
        for key, val in update.items():
            setattr(obj, key, val)
        await self.db.commit()
        await self.db.refresh(obj)
        items = await _enrich_notes([NoteResponse.model_validate(obj)], self.db)
        return items[0]

    async def delete_note(self, id: int) -> bool:
        obj = await self.db.get(Note, id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        logger.info(f"Deleted note id={id}")
        return True

    async def list_backups(self, note_id: int) -> list[dict]:
        """List backup snapshots for a note, newest first."""
        result = await self.db.execute(
            select(NoteBackup)
            .where(NoteBackup.note_id == note_id)
            .order_by(NoteBackup.created_at.desc())
            .limit(MAX_BACKUPS_PER_NOTE)
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "note_id": r.note_id,
                "word_count": r.word_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "preview": (r.content or "")[:200],
            }
            for r in rows
        ]

    async def restore_backup(self, note_id: int, backup_id: int) -> NoteResponse | None:
        """Restore a note's content from a backup snapshot."""
        backup = await self.db.get(NoteBackup, backup_id)
        if not backup or backup.note_id != note_id:
            return None
        note = await self.db.get(Note, note_id)
        if not note:
            return None
        # Save current as a new backup before restoring
        if note.content is not None:
            save_current = NoteBackup(
                note_id=note.id,
                content=note.content,
                word_count=note.word_count or 0,
            )
            self.db.add(save_current)
        # Restore
        note.content = backup.content
        note.word_count = backup.word_count
        await self.db.commit()
        await self.db.refresh(note)
        items = await _enrich_notes([NoteResponse.model_validate(note)], self.db)
        return items[0]

    async def _prune_backups(self, note_id: int):
        """Keep only the most recent MAX_BACKUPS_PER_NOTE backups."""
        count_result = await self.db.execute(
            select(func.count()).select_from(NoteBackup).where(NoteBackup.note_id == note_id)
        )
        count = count_result.scalar_one()
        if count >= MAX_BACKUPS_PER_NOTE:
            # Find IDs to delete (oldest beyond the limit)
            oldest = await self.db.execute(
                select(NoteBackup.id)
                .where(NoteBackup.note_id == note_id)
                .order_by(NoteBackup.created_at.asc())
                .limit(count - MAX_BACKUPS_PER_NOTE + 1)
            )
            ids_to_delete = [row.id for row in oldest]
            if ids_to_delete:
                for bid in ids_to_delete:
                    obj = await self.db.get(NoteBackup, bid)
                    if obj:
                        await self.db.delete(obj)
