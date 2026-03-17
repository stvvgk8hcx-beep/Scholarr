"""Academic Item schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from scholarr.db.models import AcademicItemTypeEnum, AcademicItemStatusEnum


class AcademicItemCreate(BaseModel):
    course_id: int
    type: AcademicItemTypeEnum
    name: str = Field(min_length=1, max_length=255)
    number: str | None = Field(default=None, max_length=50)
    topic: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    date_received: datetime | None = None
    status: AcademicItemStatusEnum = AcademicItemStatusEnum.NOT_STARTED  # "NotStarted"
    grade: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    monitored: bool = True
    clean_name: str | None = Field(default=None, max_length=255)


class AcademicItemUpdate(BaseModel):
    course_id: int | None = None
    type: AcademicItemTypeEnum | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    number: str | None = Field(default=None, max_length=50)
    topic: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    date_received: datetime | None = None
    status: AcademicItemStatusEnum | None = None
    grade: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    monitored: bool | None = None
    clean_name: str | None = Field(default=None, max_length=255)


class AcademicItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    type: AcademicItemTypeEnum
    name: str
    number: str | None
    topic: str | None
    due_date: datetime | None
    date_received: datetime | None
    status: AcademicItemStatusEnum
    grade: float | None
    weight: float | None
    notes: str | None
    monitored: bool
    clean_name: str | None
    created_at: datetime
    updated_at: datetime


class AcademicItemListResponse(BaseModel):
    items: list[AcademicItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
