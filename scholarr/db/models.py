"""SQLAlchemy ORM models for Scholarr."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


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


# Association table for Course <-> Tag (many-to-many)
course_tags = Table(
    "course_tags",
    Base.metadata,
    Column(
        "course_id",
        Integer,
        ForeignKey("course.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Semester(Base):
    """Represents an academic semester."""
    __tablename__ = "semester"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    term: Mapped[TermEnum] = mapped_column(
        SQLEnum(TermEnum),
        nullable=False,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="semester",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_semester_year_term", "year", "term"),
        UniqueConstraint("year", "term", name="uq_semester_year_term"),
    )


class Tag(Base):
    """Represents a tag for categorizing courses."""
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    courses: Mapped[List["Course"]] = relationship(
        "Course",
        secondary=course_tags,
        back_populates="tags",
    )


class Course(Base):
    """Represents a course."""
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    professor: Mapped[Optional[str]] = mapped_column(String(255))
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semester.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[Optional[str]] = mapped_column(String(50))
    credits: Mapped[Optional[float]] = mapped_column(Float)
    color: Mapped[Optional[str]] = mapped_column(String(7))
    root_folder_path: Mapped[Optional[str]] = mapped_column(String(1024))
    monitored: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_name: Mapped[Optional[str]] = mapped_column(String(255))
    clean_name: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    schedule: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [{day, start, end}]
    notes: Mapped[Optional[str]] = mapped_column(Text)
    grade_weights: Mapped[Optional[str]] = mapped_column(Text)  # JSON: {type: weight%}
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    semester: Mapped["Semester"] = relationship(
        "Semester",
        back_populates="courses",
    )
    academic_items: Mapped[List["AcademicItem"]] = relationship(
        "AcademicItem",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=course_tags,
        back_populates="courses",
    )
    history_entries: Mapped[List["HistoryEntry"]] = relationship(
        "HistoryEntry",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_course_semester_id", "semester_id"),
        Index("ix_course_code", "code"),
        UniqueConstraint("code", "semester_id", name="uq_course_code_semester"),
    )


class AcademicItem(Base):
    """Represents an academic item (assignment, exam, etc.)."""
    __tablename__ = "academic_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[AcademicItemTypeEnum] = mapped_column(
        SQLEnum(AcademicItemTypeEnum),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[Optional[str]] = mapped_column(String(50))
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_received: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[AcademicItemStatusEnum] = mapped_column(
        SQLEnum(AcademicItemStatusEnum),
        default=AcademicItemStatusEnum.NOT_STARTED,
        nullable=False,
    )
    grade: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    monitored: Mapped[bool] = mapped_column(Boolean, default=True)
    clean_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="academic_items",
    )
    files: Mapped[List["ManagedFile"]] = relationship(
        "ManagedFile",
        back_populates="academic_item",
        cascade="all, delete-orphan",
    )
    history_entries: Mapped[List["HistoryEntry"]] = relationship(
        "HistoryEntry",
        back_populates="academic_item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_academic_item_course_id", "course_id"),
        Index("ix_academic_item_type", "type"),
        Index("ix_academic_item_status", "status"),
    )


class ManagedFile(Base):
    """Represents a file managed by Scholarr."""
    __tablename__ = "managed_file"

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_item_id: Mapped[int] = mapped_column(
        ForeignKey("academic_item.id", ondelete="CASCADE"),
        nullable=False,
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_path: Mapped[Optional[str]] = mapped_column(String(1024))
    size: Mapped[Optional[int]] = mapped_column(Integer)
    format: Mapped[Optional[str]] = mapped_column(String(50))
    quality: Mapped[Optional[str]] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer, default=1)
    date_imported: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    academic_item: Mapped["AcademicItem"] = relationship(
        "AcademicItem",
        back_populates="files",
    )
    history_entries: Mapped[List["HistoryEntry"]] = relationship(
        "HistoryEntry",
        back_populates="managed_file",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_managed_file_academic_item_id", "academic_item_id"),
        Index("ix_managed_file_hash", "hash"),
    )


class FileProfile(Base):
    """Represents file format preferences."""
    __tablename__ = "file_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cutoff_format_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("custom_format.id", ondelete="SET NULL")
    )
    upgrade_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    allowed_formats: Mapped[List["CustomFormat"]] = relationship(
        "CustomFormat",
        back_populates="allowed_in_profiles",
        foreign_keys="CustomFormat.profile_id",
    )
    preferred_formats: Mapped[List["CustomFormat"]] = relationship(
        "CustomFormat",
        back_populates="preferred_in_profiles",
        foreign_keys="CustomFormat.preferred_profile_id",
    )


class CustomFormat(Base):
    """Represents custom file format specifications."""
    __tablename__ = "custom_format"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    include_when_renaming: Mapped[bool] = mapped_column(Boolean, default=True)
    specifications: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("file_profile.id", ondelete="SET NULL")
    )
    preferred_profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("file_profile.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    allowed_in_profiles: Mapped[List["FileProfile"]] = relationship(
        "FileProfile",
        back_populates="allowed_formats",
        foreign_keys="CustomFormat.profile_id",
    )
    preferred_in_profiles: Mapped[List["FileProfile"]] = relationship(
        "FileProfile",
        back_populates="preferred_formats",
        foreign_keys="CustomFormat.preferred_profile_id",
    )


class RootFolder(Base):
    """Represents a monitored root folder."""
    __tablename__ = "root_folder"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_file_profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("file_profile.id", ondelete="SET NULL")
    )
    default_monitored: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class HistoryEntry(Base):
    """Represents a historical event."""
    __tablename__ = "history_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE")
    )
    academic_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("academic_item.id", ondelete="CASCADE")
    )
    managed_file_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("managed_file.id", ondelete="CASCADE")
    )
    source_path: Mapped[Optional[str]] = mapped_column(String(1024))
    destination_path: Mapped[Optional[str]] = mapped_column(String(1024))
    date: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    event_type: Mapped[HistoryEventTypeEnum] = mapped_column(
        SQLEnum(HistoryEventTypeEnum),
        nullable=False,
    )
    data: Mapped[Optional[dict]] = mapped_column(JSON)

    course: Mapped[Optional["Course"]] = relationship(
        "Course",
        back_populates="history_entries",
    )
    academic_item: Mapped[Optional["AcademicItem"]] = relationship(
        "AcademicItem",
        back_populates="history_entries",
    )
    managed_file: Mapped[Optional["ManagedFile"]] = relationship(
        "ManagedFile",
        back_populates="history_entries",
    )

    __table_args__ = (
        Index("ix_history_entry_date", "date"),
        Index("ix_history_entry_event_type", "event_type"),
        Index("ix_history_entry_course_id", "course_id"),
    )


class NamingConfig(Base):
    """Singleton for global naming configuration."""
    __tablename__ = "naming_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    renaming_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    replace_illegal_characters: Mapped[bool] = mapped_column(Boolean, default=True)
    standard_file_format: Mapped[Optional[str]] = mapped_column(String(255))
    folder_format: Mapped[Optional[str]] = mapped_column(String(255))
    course_folder_format: Mapped[Optional[str]] = mapped_column(String(255))
    semester_folder_format: Mapped[Optional[str]] = mapped_column(String(255))
    colon_replacement_format: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ImportSource(Base):
    """Represents a source for importing academic items."""
    __tablename__ = "import_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_type: Mapped[ImportSourceTypeEnum] = mapped_column(
        SQLEnum(ImportSourceTypeEnum),
        nullable=False,
    )
    watch_path: Mapped[Optional[str]] = mapped_column(String(1024))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("course.id", ondelete="SET NULL")
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class NotificationDefinition(Base):
    """Represents a notification configuration."""
    __tablename__ = "notification_definition"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    implementation: Mapped[str] = mapped_column(String(255), nullable=False)
    config_contract: Mapped[Optional[str]] = mapped_column(String(255))
    fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CommandModel(Base):
    """Represents a queued command for processing."""
    __tablename__ = "command_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[CommandStatusEnum] = mapped_column(
        SQLEnum(CommandStatusEnum),
        default=CommandStatusEnum.QUEUED,
        nullable=False,
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    trigger: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_command_model_status", "status"),
        Index("ix_command_model_priority", "priority"),
    )


class QueueItem(Base):
    """Represents an item in the processing queue."""
    __tablename__ = "queue_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("course.id", ondelete="CASCADE")
    )
    academic_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("academic_item.id", ondelete="CASCADE")
    )
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[QueueItemStatusEnum] = mapped_column(
        SQLEnum(QueueItemStatusEnum),
        default=QueueItemStatusEnum.PENDING,
        nullable=False,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_queue_item_status", "status"),
        Index("ix_queue_item_course_id", "course_id"),
    )


class ScheduledTask(Base):
    """Represents a scheduled background task."""
    __tablename__ = "scheduled_task"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    last_execution: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Note(Base):
    """Represents a class note / writing session."""
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("course.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    preferences: Mapped[Optional[str]] = mapped_column(Text)  # JSON: bg, font, sounds
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    course: Mapped[Optional["Course"]] = relationship("Course")

    __table_args__ = (
        Index("ix_note_course_id", "course_id"),
    )
