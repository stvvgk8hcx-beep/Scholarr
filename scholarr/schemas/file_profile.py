"""File Profile schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cutoff_format_id: int | None = None
    upgrade_allowed: bool = True


class FileProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    cutoff_format_id: int | None = None
    upgrade_allowed: bool | None = None


class FileProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cutoff_format_id: int | None
    upgrade_allowed: bool
    created_at: datetime
    updated_at: datetime


class FileProfileListResponse(BaseModel):
    items: list[FileProfileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
