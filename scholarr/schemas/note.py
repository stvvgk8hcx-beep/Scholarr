"""Note schemas."""

import json
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteCreate(BaseModel):
    course_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=500)
    content: Optional[str] = None
    word_count: int = 0
    duration_seconds: int = 0
    preferences: Optional[Dict[str, Any]] = None
    pinned: bool = False


class NoteUpdate(BaseModel):
    course_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content: Optional[str] = None
    word_count: Optional[int] = None
    duration_seconds: Optional[int] = None
    preferences: Optional[Dict[str, Any]] = None
    pinned: Optional[bool] = None


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: Optional[int]
    title: str
    content: Optional[str]
    word_count: int
    duration_seconds: int
    preferences: Optional[Dict[str, Any]] = None
    pinned: bool
    created_at: datetime
    updated_at: datetime
    # Enriched
    course_code: Optional[str] = None
    course_name: Optional[str] = None

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
