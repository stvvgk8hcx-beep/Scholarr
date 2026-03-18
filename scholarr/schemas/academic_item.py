"""Academic Item schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholarr.db.models import AcademicItemStatusEnum, AcademicItemTypeEnum


def _coerce_type(v: str | None) -> AcademicItemTypeEnum | None:
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
    name: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    # Accept both 'type' and 'item_type' (lowercase ok)
    type: AcademicItemTypeEnum | None = None
    item_type: str | None = None
    # course_id optional — front-end may omit if no course selected
    course_id: int | None = None
    number: str | None = Field(default=None, max_length=50)
    topic: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    date_received: datetime | None = None
    status: AcademicItemStatusEnum = AcademicItemStatusEnum.NOT_STARTED
    grade: float | None = Field(default=None, ge=0)   # No upper cap — allow bonus grades >100
    weight: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    monitored: bool = True
    clean_name: str | None = Field(default=None, max_length=255)

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
    course_id: int | None = None
    type: AcademicItemTypeEnum | None = None
    item_type: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=50)
    topic: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    date_received: datetime | None = None
    status: AcademicItemStatusEnum | None = None
    grade: float | None = Field(default=None, ge=0)  # Allow >100 for bonus grades
    weight: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    monitored: bool | None = None
    clean_name: str | None = Field(default=None, max_length=255)

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
    course_code: str | None = None  # populated by service via join
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
