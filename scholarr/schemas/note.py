"""Note schemas."""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteCreate(BaseModel):
    course_id: int | None = None
    title: str = Field(min_length=1, max_length=500)
    content: str | None = None
    word_count: int = 0
    duration_seconds: int = 0
    preferences: dict[str, Any] | None = None
    pinned: bool = False


class NoteUpdate(BaseModel):
    course_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = None
    word_count: int | None = None
    duration_seconds: int | None = None
    preferences: dict[str, Any] | None = None
    pinned: bool | None = None


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int | None
    title: str
    content: str | None
    word_count: int
    duration_seconds: int
    preferences: dict[str, Any] | None = None
    pinned: bool
    created_at: datetime
    updated_at: datetime
    # Enriched
    course_code: str | None = None
    course_name: str | None = None

    @field_validator("preferences", mode="before")
    @classmethod
    def parse_preferences(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
