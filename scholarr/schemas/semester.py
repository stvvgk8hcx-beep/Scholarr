"""Semester schemas."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholarr.db.models import TermEnum


def _derive_term_from_name_or_date(name: str, start_date: datetime) -> TermEnum:
    """Infer academic term from the semester name string or start_date month."""
    name_lower = name.lower()
    if "spring" in name_lower:
        return TermEnum.SPRING
    if "summer" in name_lower:
        return TermEnum.SUMMER
    if "fall" in name_lower or "autumn" in name_lower:
        return TermEnum.FALL
    if "winter" in name_lower:
        return TermEnum.WINTER
    # Fall back to month of start_date
    month = start_date.month
    if month in (1, 2):
        return TermEnum.WINTER
    if month in (3, 4, 5):
        return TermEnum.SPRING
    if month in (6, 7, 8):
        return TermEnum.SUMMER
    return TermEnum.FALL  # Sep–Dec


class SemesterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    term: Optional[TermEnum] = None
    start_date: datetime
    end_date: datetime
    active: bool = False

    @model_validator(mode="after")
    def fill_and_validate(self) -> "SemesterCreate":
        # Auto-derive year from name (look for 4-digit number) or start_date
        if self.year is None:
            m = re.search(r"\b(20\d{2}|19\d{2})\b", self.name)
            self.year = int(m.group(1)) if m else self.start_date.year
        # Auto-derive term from name or start_date month
        if self.term is None:
            self.term = _derive_term_from_name_or_date(self.name, self.start_date)
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SemesterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    term: Optional[TermEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    active: Optional[bool] = None


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    year: int
    term: TermEnum
    start_date: datetime
    end_date: datetime
    active: bool
    course_count: int = 0
    created_at: datetime
    updated_at: datetime


class SemesterListResponse(BaseModel):
    items: list[SemesterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
