"""Course schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(min_length=1, max_length=255)
    professor: str | None = Field(default=None, max_length=255)
    semester_id: int
    section: str | None = Field(default=None, max_length=50)
    credits: float | None = Field(default=None, ge=0, le=20)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    root_folder_path: str | None = Field(default=None, max_length=1024)
    monitored: bool = False
    sort_name: str | None = Field(default=None, max_length=255)
    clean_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None


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
    notes: str | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    professor: str | None
    semester_id: int
    section: str | None
    credits: float | None
    color: str | None
    root_folder_path: str | None
    monitored: bool
    sort_name: str | None
    clean_name: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
