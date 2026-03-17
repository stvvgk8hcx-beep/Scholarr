"""Course schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(min_length=1, max_length=255)
    professor: Optional[str] = Field(default=None, max_length=255)
    semester_id: Optional[int] = None
    section: Optional[str] = Field(default=None, max_length=50)
    credits: Optional[float] = Field(default=None, ge=0, le=20)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    root_folder_path: Optional[str] = Field(default=None, max_length=1024)
    monitored: bool = False
    sort_name: Optional[str] = Field(default=None, max_length=255)
    clean_name: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class CourseUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    professor: Optional[str] = Field(default=None, max_length=255)
    semester_id: Optional[int] = None
    section: Optional[str] = Field(default=None, max_length=50)
    credits: Optional[float] = Field(default=None, ge=0, le=20)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    root_folder_path: Optional[str] = Field(default=None, max_length=1024)
    monitored: Optional[bool] = None
    sort_name: Optional[str] = Field(default=None, max_length=255)
    clean_name: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    professor: Optional[str]
    semester_id: Optional[int]
    semester_name: Optional[str] = None  # populated by service via JOIN
    item_count: int = 0              # populated by service via count query
    section: Optional[str]
    credits: Optional[float]
    color: Optional[str]
    root_folder_path: Optional[str]
    monitored: bool
    sort_name: Optional[str]
    clean_name: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
