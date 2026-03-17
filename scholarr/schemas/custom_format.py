"""Custom Format schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomFormatCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    include_when_renaming: bool = True
    specifications: dict = Field(default_factory=dict)


class CustomFormatUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    include_when_renaming: bool | None = None
    specifications: dict | None = None


class CustomFormatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    include_when_renaming: bool
    specifications: dict
    created_at: datetime
    updated_at: datetime


class CustomFormatListResponse(BaseModel):
    items: list[CustomFormatResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
