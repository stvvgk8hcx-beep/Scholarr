"""Course schemas."""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(min_length=1, max_length=255)
    professor: str | None = Field(default=None, max_length=255)
    semester_id: int | None = None
    section: str | None = Field(default=None, max_length=50)
    credits: float | None = Field(default=None, ge=0, le=20)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    root_folder_path: str | None = Field(default=None, max_length=1024)
    monitored: bool = False
    sort_name: str | None = Field(default=None, max_length=255)
    clean_name: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    schedule: list[dict[str, Any]] | None = None
    notes: str | None = None
    grade_weights: dict[str, float] | None = None

    @field_validator("grade_weights")
    @classmethod
    def validate_weights(cls, v):
        if v is not None:
            for key, val in v.items():
                if val < 0 or val > 100:
                    raise ValueError(f"Weight for '{key}' must be between 0 and 100, got {val}")
        return v


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    professor: str | None = Field(default=None, max_length=255)
    semester_id: int | None = None
    section: str | None = Field(default=None, max_length=50)
    credits: float | None = Field(default=None, ge=0, le=20)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    root_folder_path: str | None = Field(default=None, max_length=1024)
    monitored: bool | None = None
    sort_name: str | None = Field(default=None, max_length=255)
    clean_name: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    schedule: list[dict[str, Any]] | None = None
    notes: str | None = None
    grade_weights: dict[str, float] | None = None

    @field_validator("grade_weights")
    @classmethod
    def validate_weights(cls, v):
        if v is not None:
            for key, val in v.items():
                if val < 0 or val > 100:
                    raise ValueError(f"Weight for '{key}' must be between 0 and 100, got {val}")
        return v


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    professor: str | None
    semester_id: int | None
    semester_name: str | None = None  # populated by service via JOIN
    item_count: int = 0              # populated by service via count query
    section: str | None
    credits: float | None
    color: str | None
    root_folder_path: str | None
    monitored: bool
    sort_name: str | None
    clean_name: str | None
    location: str | None = None
    schedule: list[dict[str, Any]] | None = None
    notes: str | None
    grade_weights: dict[str, float] | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("grade_weights", mode="before")
    @classmethod
    def parse_grade_weights(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v

    @field_validator("schedule", mode="before")
    @classmethod
    def parse_schedule(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
