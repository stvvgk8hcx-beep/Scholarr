"""History schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HistoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: Optional[int] = None
    academic_item_id: Optional[int] = None
    managed_file_id: Optional[int] = None
    event_type: str
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    date: datetime
    data: Optional[dict] = None


class HistoryListResponse(BaseModel):
    items: list[HistoryEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
