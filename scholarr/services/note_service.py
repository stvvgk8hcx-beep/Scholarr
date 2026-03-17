"""Note service for class notes and writing sessions."""

import json
import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.db.models import Note, Course
from scholarr.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse

logger = logging.getLogger(__name__)


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
        course_id: Optional[int] = None,
        search: Optional[str] = None,
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

    async def get_note(self, id: int) -> Optional[NoteResponse]:
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

    async def update_note(self, id: int, data: NoteUpdate) -> Optional[NoteResponse]:
        obj = await self.db.get(Note, id)
        if not obj:
            return None
        update = data.model_dump(exclude_unset=True)
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
