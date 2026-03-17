"""Root Folder schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RootFolderCreate(BaseModel):
    path: str = Field(min_length=1, max_length=1024)
    name: str = Field(min_length=1, max_length=255)
    default_file_profile_id: int | None = None
    default_monitored: bool = True


class RootFolderUpdate(BaseModel):
    path: str | None = Field(default=None, min_length=1, max_length=1024)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    default_file_profile_id: int | None = None
    default_monitored: bool | None = None


class RootFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    name: str
    default_file_profile_id: int | None
    default_monitored: bool
    created_at: datetime
    updated_at: datetime


class RootFolderListResponse(BaseModel):
    items: list[RootFolderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
