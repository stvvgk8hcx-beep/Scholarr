"""Managed File schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ManagedFileCreate(BaseModel):
    academic_item_id: int
    path: str = Field(min_length=1, max_length=1024)
    original_path: str | None = Field(default=None, max_length=1024)
    size: int | None = Field(default=None, ge=0)
    format: str | None = Field(default=None, max_length=50)
    quality: str | None = Field(default=None, max_length=50)
    version: int = Field(default=1, ge=1)
    hash: str | None = Field(default=None, max_length=64)
    original_filename: str | None = Field(default=None, max_length=255)


class ManagedFileUpdate(BaseModel):
    academic_item_id: int | None = None
    path: str | None = Field(default=None, min_length=1, max_length=1024)
    original_path: str | None = Field(default=None, max_length=1024)
    size: int | None = Field(default=None, ge=0)
    format: str | None = Field(default=None, max_length=50)
    quality: str | None = Field(default=None, max_length=50)
    version: int | None = Field(default=None, ge=1)
    hash: str | None = Field(default=None, max_length=64)
    original_filename: str | None = Field(default=None, max_length=255)


class ManagedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_item_id: int
    path: str
    original_path: str | None
    size: int | None
    format: str | None
    quality: str | None
    version: int
    date_imported: datetime
    hash: str | None
    original_filename: str | None
    created_at: datetime
    updated_at: datetime
    # Enriched fields (not from DB)
    item_name: str | None = None
    course_code: str | None = None
    course_id: int | None = None


class ManagedFileListResponse(BaseModel):
    items: list[ManagedFileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
