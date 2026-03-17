"""Pydantic V2 schemas for database models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TermEnum(str, Enum):
    """Academic term types."""
    WINTER = "Winter"
    SPRING = "Spring"
    SUMMER = "Summer"
    FALL = "Fall"


class AcademicItemTypeEnum(str, Enum):
    """Types of academic items."""
    ASSIGNMENT = "Assignment"
    LAB = "Lab"
    LECTURE = "Lecture"
    EXAM = "Exam"
    PAPER = "Paper"
    PROJECT = "Project"
    NOTES = "Notes"
    SYLLABUS = "Syllabus"
    TEXTBOOK = "Textbook"
    SLIDES = "Slides"
    TUTORIAL = "Tutorial"
    QUIZ = "Quiz"
    OTHER = "Other"


class AcademicItemStatusEnum(str, Enum):
    """Status of academic items."""
    NOT_STARTED = "NotStarted"
    IN_PROGRESS = "InProgress"
    SUBMITTED = "Submitted"
    GRADED = "Graded"
    LATE = "Late"
    INCOMPLETE = "Incomplete"
    COMPLETE = "Complete"


class ImportSourceTypeEnum(str, Enum):
    """Types of import sources."""
    MANUAL = "Manual"
    FILE_WATCHER = "FileWatcher"
    LMS_IMPORT = "LmsImport"
    CSV_IMPORT = "CsvImport"
    EMAIL_ATTACHMENT = "EmailAttachment"


class HistoryEventTypeEnum(str, Enum):
    """Types of history events."""
    IMPORT = "Import"
    RENAME = "Rename"
    MOVE = "Move"
    DELETE = "Delete"
    GRADE_CHANGE = "GradeChange"
    STATUS_CHANGE = "StatusChange"
    ARCHIVE = "Archive"
    EXTRACT = "Extract"
    DUPLICATE = "Duplicate"


class CommandStatusEnum(str, Enum):
    """Status of queued commands."""
    QUEUED = "Queued"
    STARTED = "Started"
    COMPLETED = "Completed"
    FAILED = "Failed"
    ABORTED = "Aborted"


class QueueItemStatusEnum(str, Enum):
    """Status of queue items."""
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    SKIPPED = "Skipped"


# ---------------------------------------------------------------------------
# Semester Schemas
# ---------------------------------------------------------------------------

class SemesterCreate(BaseModel):
    """Create a semester."""
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
    """Update a semester."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    year: int | None = Field(default=None, ge=1900, le=2100)
    term: TermEnum | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    active: bool | None = None


class SemesterResponse(BaseModel):
    """Semester response model."""
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
    """List response for semesters."""
    items: list[SemesterResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Tag Schemas
# ---------------------------------------------------------------------------

_HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class TagCreate(BaseModel):
    """Create a tag."""
    label: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=_HEX_COLOR_PATTERN)


class TagUpdate(BaseModel):
    """Update a tag."""
    label: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=_HEX_COLOR_PATTERN)


class TagResponse(BaseModel):
    """Tag response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    color: str | None
    created_at: datetime
    updated_at: datetime


class TagListResponse(BaseModel):
    """List response for tags."""
    items: list[TagResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Course Schemas
# ---------------------------------------------------------------------------

class CourseCreate(BaseModel):
    """Create a course."""
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    professor: str | None = Field(default=None, max_length=255)
    semester_id: int
    section: str | None = Field(default=None, max_length=50)
    credits: float | None = Field(default=None, ge=0, le=20)
    color: str | None = Field(default=None, pattern=_HEX_COLOR_PATTERN)
    root_folder_path: str | None = Field(default=None, max_length=1024)
    monitored: bool = False
    sort_name: str | None = Field(default=None, max_length=255)
    clean_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None

    @field_validator("code")
    @classmethod
    def code_alphanumeric(cls, v: str) -> str:
        import re
        if not re.match(r"^[A-Z0-9\s\-]+$", v, re.IGNORECASE):
            raise ValueError("Course code may only contain letters, digits, spaces, and hyphens")
        return v.upper()


class CourseUpdate(BaseModel):
    """Update a course."""
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    professor: str | None = Field(default=None, max_length=255)
    semester_id: int | None = None
    section: str | None = Field(default=None, max_length=50)
    credits: float | None = Field(default=None, ge=0, le=20)
    color: str | None = Field(default=None, pattern=_HEX_COLOR_PATTERN)
    root_folder_path: str | None = Field(default=None, max_length=1024)
    monitored: bool | None = None
    sort_name: str | None = Field(default=None, max_length=255)
    clean_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class CourseResponse(BaseModel):
    """Course response model."""
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
    """List response for courses."""
    items: list[CourseResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Academic Item Schemas
# ---------------------------------------------------------------------------

class AcademicItemCreate(BaseModel):
    """Create an academic item."""
    course_id: int
    type: AcademicItemTypeEnum
    name: str = Field(min_length=1, max_length=255)
    number: str | None = Field(default=None, max_length=50)
    topic: str | None = Field(default=None, max_length=255)
    due_date: datetime | None = None
    date_received: datetime | None = None
    status: AcademicItemStatusEnum = AcademicItemStatusEnum.NOT_STARTED
    grade: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    monitored: bool = True
    clean_name: str | None = Field(default=None, max_length=255)


class AcademicItemUpdate(BaseModel):
    """Update an academic item."""
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
    """Academic item response model."""
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
    """List response for academic items."""
    items: list[AcademicItemResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Managed File Schemas
# ---------------------------------------------------------------------------

class ManagedFileCreate(BaseModel):
    """Create a managed file."""
    academic_item_id: int
    path: str = Field(min_length=1, max_length=1024)
    original_path: str | None = Field(default=None, max_length=1024)
    size: int | None = Field(default=None, ge=0)
    format: str | None = Field(default=None, max_length=50)
    quality: str | None = Field(default=None, max_length=50)
    version: int = Field(default=1, ge=1)
    hash: str | None = Field(default=None, max_length=64)
    original_filename: str | None = Field(default=None, max_length=255)


class ManagedFileUpdate(BaseModel):
    """Update a managed file."""
    academic_item_id: int | None = None
    path: str | None = Field(default=None, min_length=1, max_length=1024)
    original_path: str | None = Field(default=None, max_length=1024)
    size: int | None = Field(default=None, ge=0)
    format: str | None = Field(default=None, max_length=50)
    quality: str | None = Field(default=None, max_length=50)
    version: int | None = Field(default=None, ge=1)
    hash: str | None = Field(default=None, max_length=64)
    original_filename: str | None = Field(default=None, max_length=255)


class ManagedFileResponse(BaseModel):
    """Managed file response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_item_id: int
    path: str
    original_path: str | None
    size: int | None
    format: str | None
    quality: str | None
    version: int
    date_imported: datetime
    hash: str | None
    original_filename: str | None
    created_at: datetime
    updated_at: datetime


class ManagedFileListResponse(BaseModel):
    """List response for managed files."""
    items: list[ManagedFileResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# File Profile Schemas
# ---------------------------------------------------------------------------

class FileProfileCreate(BaseModel):
    """Create a file profile."""
    name: str = Field(min_length=1, max_length=255)
    cutoff_format_id: int | None = None
    upgrade_allowed: bool = True


class FileProfileUpdate(BaseModel):
    """Update a file profile."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    cutoff_format_id: int | None = None
    upgrade_allowed: bool | None = None


class FileProfileResponse(BaseModel):
    """File profile response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cutoff_format_id: int | None
    upgrade_allowed: bool
    created_at: datetime
    updated_at: datetime


class FileProfileListResponse(BaseModel):
    """List response for file profiles."""
    items: list[FileProfileResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Custom Format Schemas
# ---------------------------------------------------------------------------

class CustomFormatCreate(BaseModel):
    """Create a custom format."""
    name: str = Field(min_length=1, max_length=255)
    include_when_renaming: bool = True
    specifications: dict = Field(default_factory=dict)


class CustomFormatUpdate(BaseModel):
    """Update a custom format."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    include_when_renaming: bool | None = None
    specifications: dict | None = None


class CustomFormatResponse(BaseModel):
    """Custom format response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    include_when_renaming: bool
    specifications: dict
    created_at: datetime
    updated_at: datetime


class CustomFormatListResponse(BaseModel):
    """List response for custom formats."""
    items: list[CustomFormatResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Root Folder Schemas
# ---------------------------------------------------------------------------

class RootFolderCreate(BaseModel):
    """Create a root folder."""
    path: str = Field(min_length=1, max_length=1024)
    name: str = Field(min_length=1, max_length=255)
    default_file_profile_id: int | None = None
    default_monitored: bool = True


class RootFolderUpdate(BaseModel):
    """Update a root folder."""
    path: str | None = Field(default=None, min_length=1, max_length=1024)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    default_file_profile_id: int | None = None
    default_monitored: bool | None = None


class RootFolderResponse(BaseModel):
    """Root folder response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    name: str
    default_file_profile_id: int | None
    default_monitored: bool
    created_at: datetime
    updated_at: datetime


class RootFolderListResponse(BaseModel):
    """List response for root folders."""
    items: list[RootFolderResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# History Entry Schemas
# ---------------------------------------------------------------------------

class HistoryEntryCreate(BaseModel):
    """Create a history entry."""
    course_id: int | None = None
    academic_item_id: int | None = None
    managed_file_id: int | None = None
    source_path: str | None = Field(default=None, max_length=1024)
    destination_path: str | None = Field(default=None, max_length=1024)
    event_type: HistoryEventTypeEnum
    data: dict | None = None


class HistoryEntryResponse(BaseModel):
    """History entry response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int | None
    academic_item_id: int | None
    managed_file_id: int | None
    source_path: str | None
    destination_path: str | None
    date: datetime
    event_type: HistoryEventTypeEnum
    data: dict | None


class HistoryEntryListResponse(BaseModel):
    """List response for history entries."""
    items: list[HistoryEntryResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Naming Config Schemas
# ---------------------------------------------------------------------------

class NamingConfigCreate(BaseModel):
    """Create naming config."""
    renaming_enabled: bool = True
    replace_illegal_characters: bool = True
    standard_file_format: str | None = Field(default=None, max_length=255)
    folder_format: str | None = Field(default=None, max_length=255)
    course_folder_format: str | None = Field(default=None, max_length=255)
    semester_folder_format: str | None = Field(default=None, max_length=255)
    colon_replacement_format: str | None = Field(default=None, max_length=10)


class NamingConfigUpdate(BaseModel):
    """Update naming config."""
    renaming_enabled: bool | None = None
    replace_illegal_characters: bool | None = None
    standard_file_format: str | None = Field(default=None, max_length=255)
    folder_format: str | None = Field(default=None, max_length=255)
    course_folder_format: str | None = Field(default=None, max_length=255)
    semester_folder_format: str | None = Field(default=None, max_length=255)
    colon_replacement_format: str | None = Field(default=None, max_length=10)


class NamingConfigResponse(BaseModel):
    """Naming config response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    renaming_enabled: bool
    replace_illegal_characters: bool
    standard_file_format: str | None
    folder_format: str | None
    course_folder_format: str | None
    semester_folder_format: str | None
    colon_replacement_format: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Import Source Schemas
# ---------------------------------------------------------------------------

class ImportSourceCreate(BaseModel):
    """Create an import source."""
    name: str = Field(min_length=1, max_length=255)
    source_type: ImportSourceTypeEnum
    watch_path: str | None = Field(default=None, max_length=1024)
    enabled: bool = True
    default_course_id: int | None = None
    settings: dict = Field(default_factory=dict)


class ImportSourceUpdate(BaseModel):
    """Update an import source."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    source_type: ImportSourceTypeEnum | None = None
    watch_path: str | None = Field(default=None, max_length=1024)
    enabled: bool | None = None
    default_course_id: int | None = None
    settings: dict | None = None


class ImportSourceResponse(BaseModel):
    """Import source response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: ImportSourceTypeEnum
    watch_path: str | None
    enabled: bool
    default_course_id: int | None
    settings: dict
    created_at: datetime
    updated_at: datetime


class ImportSourceListResponse(BaseModel):
    """List response for import sources."""
    items: list[ImportSourceResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Notification Definition Schemas
# ---------------------------------------------------------------------------

class NotificationDefinitionCreate(BaseModel):
    """Create a notification definition."""
    name: str = Field(min_length=1, max_length=255)
    enabled: bool = True
    implementation: str = Field(min_length=1, max_length=255)
    config_contract: str | None = Field(default=None, max_length=255)
    fields: dict = Field(default_factory=dict)


class NotificationDefinitionUpdate(BaseModel):
    """Update a notification definition."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    enabled: bool | None = None
    implementation: str | None = Field(default=None, min_length=1, max_length=255)
    config_contract: str | None = Field(default=None, max_length=255)
    fields: dict | None = None


class NotificationDefinitionResponse(BaseModel):
    """Notification definition response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    enabled: bool
    implementation: str
    config_contract: str | None
    fields: dict
    created_at: datetime
    updated_at: datetime


class NotificationDefinitionListResponse(BaseModel):
    """List response for notification definitions."""
    items: list[NotificationDefinitionResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Command Model Schemas
# ---------------------------------------------------------------------------

class CommandModelCreate(BaseModel):
    """Create a command."""
    name: str = Field(min_length=1, max_length=255)
    body: dict
    priority: int = Field(default=0, ge=0)
    status: CommandStatusEnum = CommandStatusEnum.QUEUED
    trigger: str | None = Field(default=None, max_length=255)


class CommandModelUpdate(BaseModel):
    """Update a command."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    body: dict | None = None
    priority: int | None = Field(default=None, ge=0)
    status: CommandStatusEnum | None = None
    trigger: str | None = Field(default=None, max_length=255)


class CommandModelResponse(BaseModel):
    """Command model response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    body: dict
    priority: int
    status: CommandStatusEnum
    queued_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    trigger: str | None
    created_at: datetime
    updated_at: datetime


class CommandModelListResponse(BaseModel):
    """List response for commands."""
    items: list[CommandModelResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Queue Item Schemas
# ---------------------------------------------------------------------------

class QueueItemCreate(BaseModel):
    """Create a queue item."""
    course_id: int | None = None
    academic_item_id: int | None = None
    source_path: str = Field(min_length=1, max_length=1024)
    status: QueueItemStatusEnum = QueueItemStatusEnum.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)


class QueueItemUpdate(BaseModel):
    """Update a queue item."""
    course_id: int | None = None
    academic_item_id: int | None = None
    source_path: str | None = Field(default=None, min_length=1, max_length=1024)
    status: QueueItemStatusEnum | None = None
    progress: float | None = Field(default=None, ge=0.0, le=100.0)


class QueueItemResponse(BaseModel):
    """Queue item response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int | None
    academic_item_id: int | None
    source_path: str
    status: QueueItemStatusEnum
    progress: float
    added_at: datetime
    created_at: datetime
    updated_at: datetime


class QueueItemListResponse(BaseModel):
    """List response for queue items."""
    items: list[QueueItemResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Scheduled Task Schemas
# ---------------------------------------------------------------------------

class ScheduledTaskCreate(BaseModel):
    """Create a scheduled task."""
    task_name: str = Field(min_length=1, max_length=255)
    interval_minutes: int = Field(ge=1)
    enabled: bool = True


class ScheduledTaskUpdate(BaseModel):
    """Update a scheduled task."""
    task_name: str | None = Field(default=None, min_length=1, max_length=255)
    interval_minutes: int | None = Field(default=None, ge=1)
    enabled: bool | None = None


class ScheduledTaskResponse(BaseModel):
    """Scheduled task response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_name: str
    interval_minutes: int
    last_execution: datetime | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ScheduledTaskListResponse(BaseModel):
    """List response for scheduled tasks."""
    items: list[ScheduledTaskResponse]
    total: int
    skip: int
    limit: int
