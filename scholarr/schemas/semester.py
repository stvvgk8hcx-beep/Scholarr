"""Semester schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholarr.db.models import TermEnum


class SemesterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    year: int = Field(ge=1900, le=2100)
    term: TermEnum
    start_date: datetime
    end_date: datetime
    active: bool = False

    @model_validator(mode="after")
    def end_after_start(self) -> "SemesterCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SemesterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    year: int | None = Field(default=None, ge=1900, le=2100)
    term: TermEnum | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    active: bool | None = None


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    year: int
    term: TermEnum
    start_date: datetime
    end_date: datetime
    active: bool
    created_at: datetime
    updated_at: datetime


class SemesterListResponse(BaseModel):
    items: list[SemesterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
