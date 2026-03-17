"""Log schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    logger_name: str
    message: str
    timestamp: datetime


class LogListResponse(BaseModel):
    items: list[LogEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
