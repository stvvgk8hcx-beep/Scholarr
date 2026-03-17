"""History schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    entity_type: str
    entity_id: int | None = None
    entity_name: str | None = None
    details: dict | None = None
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: list[HistoryEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
