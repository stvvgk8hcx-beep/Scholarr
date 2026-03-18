"""Calendar schemas."""

from datetime import date

from pydantic import BaseModel


class CalendarItemInfo(BaseModel):
    """Information about an item due on a date."""

    id: int
    title: str
    type: str
    course_id: int
    status: str


class CalendarDayResponse(BaseModel):
    """Schema for a calendar day with due items."""

    date: date
    items: list[CalendarItemInfo]
    item_count: int
