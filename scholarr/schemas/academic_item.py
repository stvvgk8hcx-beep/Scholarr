"""Academic Item schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholarr.db.models import AcademicItemTypeEnum, AcademicItemStatusEnum


def _coerce_type(v: Optional[str]) -> Optional[AcademicItemTypeEnum]:
    """Accept lowercase/alias type strings from the front-end."""
    if v is None:
        return None
    try:
        return AcademicItemTypeEnum(v)
    except ValueError:
        pass
    try:
        return AcademicItemTypeEnum(v.title())
    except ValueError:
        pass
    aliases = {
        "exam": AcademicItemTypeEnum.EXAM,
        "quiz": AcademicItemTypeEnum.QUIZ,
        "assignment": AcademicItemTypeEnum.ASSIGNMENT,
        "project": AcademicItemTypeEnum.PROJECT,
        "lab": AcademicItemTypeEnum.LAB,
        "presentation": AcademicItemTypeEnum.OTHER,
        "test": AcademicItemTypeEnum.EXAM,
        "other": AcademicItemTypeEnum.OTHER,
    }
    return aliases.get(v.lower(), AcademicItemTypeEnum.OTHER)


class AcademicItemCreate(BaseModel):
    # Accept both 'name' and 'title' from front-end
    name: Optional[str] = Field(default=None, max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)
    # Accept both 'type' and 'item_type' (lowercase ok)
    type: Optional[AcademicItemTypeEnum] = None
    item_type: Optional[str] = None
    # course_id optional — front-end may omit if no course selected
    course_id: Optional[int] = None
    number: Optional[str] = Field(default=None, max_length=50)
    topic: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[datetime] = None
    date_received: Optional[datetime] = None
    status: AcademicItemStatusEnum = AcademicItemStatusEnum.NOT_STARTED
    grade: Optional[float] = Field(default=None, ge=0)   # No upper cap — allow bonus grades >100
    weight: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    monitored: bool = True
    clean_name: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def resolve_aliases(self) -> "AcademicItemCreate":
        # Resolve name from title
        if not self.name and self.title:
            self.name = self.title
        if not self.name:
            self.name = "Untitled Item"
        # Resolve type from item_type
        if self.type is None and self.item_type:
            self.type = _coerce_type(self.item_type)
        if self.type is None:
            self.type = AcademicItemTypeEnum.OTHER
        # course_id=0 is treated as None in service
        if self.course_id == 0:
            self.course_id = None
        return self


class AcademicItemUpdate(BaseModel):
    course_id: Optional[int] = None
    type: Optional[AcademicItemTypeEnum] = None
    item_type: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)
    number: Optional[str] = Field(default=None, max_length=50)
    topic: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[datetime] = None
    date_received: Optional[datetime] = None
    status: Optional[AcademicItemStatusEnum] = None
    grade: Optional[float] = Field(default=None, ge=0)  # Allow >100 for bonus grades
    weight: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    monitored: Optional[bool] = None
    clean_name: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def resolve_aliases(self) -> "AcademicItemUpdate":
        if not self.name and self.title:
            self.name = self.title
        if self.type is None and self.item_type:
            self.type = _coerce_type(self.item_type)
        return self


class AcademicItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    course_id: int
    type: AcademicItemTypeEnum
    name: str
    number: Optional[str]
    topic: Optional[str]
    due_date: Optional[datetime]
    date_received: Optional[datetime]
    status: AcademicItemStatusEnum
    grade: Optional[float]
    weight: Optional[float]
    notes: Optional[str]
    monitored: bool
    clean_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Front-end aliases — serialised in JSON output
    @property
    def title(self) -> str:
        return self.name

    @property
    def item_type(self) -> str:
        return self.type.value if self.type else "Other"

    def model_post_init(self, __context):
        pass  # Hook available for future extension


class AcademicItemListResponse(BaseModel):
    items: list[AcademicItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
