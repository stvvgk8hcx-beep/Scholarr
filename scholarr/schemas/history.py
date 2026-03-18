"""History schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int | None = None
    academic_item_id: int | None = None
    managed_file_id: int | None = None
    event_type: str
    source_path: str | None = None
    destination_path: str | None = None
    date: datetime
    data: dict | None = None


class HistoryListResponse(BaseModel):
    items: list[HistoryEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
