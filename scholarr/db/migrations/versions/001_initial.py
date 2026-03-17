"""Initial migration - create all tables.

Revision ID: 001
Revises:
Create Date: 2026-03-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables."""
    op.create_table(
        "semester",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("term", sa.Enum("Winter", "Spring", "Summer", "Fall", name="termenum"), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "term", name="uq_semester_year_term"),
    )
    op.create_index("ix_semester_year_term", "semester", ["year", "term"])

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )

    op.create_table(
        "file_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cutoff_format_id", sa.Integer(), nullable=True),
        sa.Column("upgrade_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "custom_format",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("include_when_renaming", sa.Boolean(), nullable=False),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("preferred_profile_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["file_profile.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["preferred_profile_id"], ["file_profile.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "root_folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_file_profile_id", sa.Integer(), nullable=True),
        sa.Column("default_monitored", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["default_file_profile_id"], ["file_profile.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )

    op.create_table(
        "import_source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.Enum("Manual", "FileWatcher", "LmsImport", "CsvImport", "EmailAttachment", name="importsourcetypeenum"), nullable=False),
        sa.Column("watch_path", sa.String(1024), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("default_course_id", sa.Integer(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "naming_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("renaming_enabled", sa.Boolean(), nullable=False),
        sa.Column("replace_illegal_characters", sa.Boolean(), nullable=False),
        sa.Column("standard_file_format", sa.String(255), nullable=True),
        sa.Column("folder_format", sa.String(255), nullable=True),
        sa.Column("course_folder_format", sa.String(255), nullable=True),
        sa.Column("semester_folder_format", sa.String(255), nullable=True),
        sa.Column("colon_replacement_format", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notification_definition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("implementation", sa.String(255), nullable=False),
        sa.Column("config_contract", sa.String(255), nullable=True),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "scheduled_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("last_execution", sa.DateTime(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_name"),
    )

    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("professor", sa.String(255), nullable=True),
        sa.Column("semester_id", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(50), nullable=True),
        sa.Column("credits", sa.Float(), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("root_folder_path", sa.String(1024), nullable=True),
        sa.Column("monitored", sa.Boolean(), nullable=False),
        sa.Column("sort_name", sa.String(255), nullable=True),
        sa.Column("clean_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["semester_id"], ["semester.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "semester_id", name="uq_course_code_semester"),
    )
    op.create_index("ix_course_semester_id", "course", ["semester_id"])
    op.create_index("ix_course_code", "course", ["code"])

    op.create_table(
        "course_tags",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("course_id", "tag_id"),
    )

    op.create_table(
        "academic_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Enum("Assignment", "Lab", "Lecture", "Exam", "Paper", "Project", "Notes", "Syllabus", "Textbook", "Slides", "Tutorial", "Quiz", "Other", name="academicitemtypeenum"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("number", sa.String(50), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("date_received", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("NotStarted", "InProgress", "Submitted", "Graded", "Late", "Incomplete", "Complete", name="academicitemstatusenum"), nullable=False),
        sa.Column("grade", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("monitored", sa.Boolean(), nullable=False),
        sa.Column("clean_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_academic_item_course_id", "academic_item", ["course_id"])
    op.create_index("ix_academic_item_type", "academic_item", ["type"])
    op.create_index("ix_academic_item_status", "academic_item", ["status"])

    op.create_table(
        "managed_file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("academic_item_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("original_path", sa.String(1024), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("quality", sa.String(50), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("date_imported", sa.DateTime(), nullable=False),
        sa.Column("hash", sa.String(64), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["academic_item_id"], ["academic_item.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash"),
    )
    op.create_index("ix_managed_file_academic_item_id", "managed_file", ["academic_item_id"])
    op.create_index("ix_managed_file_hash", "managed_file", ["hash"])

    op.create_table(
        "history_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("academic_item_id", sa.Integer(), nullable=True),
        sa.Column("managed_file_id", sa.Integer(), nullable=True),
        sa.Column("source_path", sa.String(1024), nullable=True),
        sa.Column("destination_path", sa.String(1024), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.Enum("Import", "Rename", "Move", "Delete", "GradeChange", "StatusChange", "Archive", "Extract", "Duplicate", name="historyeventtypeenum"), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["academic_item_id"], ["academic_item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["managed_file_id"], ["managed_file.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_history_entry_date", "history_entry", ["date"])
    op.create_index("ix_history_entry_event_type", "history_entry", ["event_type"])
    op.create_index("ix_history_entry_course_id", "history_entry", ["course_id"])

    op.create_table(
        "command_model",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("Queued", "Started", "Completed", "Failed", "Aborted", name="commandstatusenum"), nullable=False),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("trigger", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_command_model_status", "command_model", ["status"])
    op.create_index("ix_command_model_priority", "command_model", ["priority"])

    op.create_table(
        "queue_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("academic_item_id", sa.Integer(), nullable=True),
        sa.Column("source_path", sa.String(1024), nullable=False),
        sa.Column("status", sa.Enum("Pending", "Processing", "Completed", "Failed", "Skipped", name="queueitemstatusenum"), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["academic_item_id"], ["academic_item.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_queue_item_status", "queue_item", ["status"])
    op.create_index("ix_queue_item_course_id", "queue_item", ["course_id"])

    op.add_foreign_key(
        "import_source",
        "course",
        ["default_course_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_queue_item_course_id", table_name="queue_item")
    op.drop_index("ix_queue_item_status", table_name="queue_item")
    op.drop_table("queue_item")

    op.drop_index("ix_command_model_priority", table_name="command_model")
    op.drop_index("ix_command_model_status", table_name="command_model")
    op.drop_table("command_model")

    op.drop_index("ix_history_entry_course_id", table_name="history_entry")
    op.drop_index("ix_history_entry_event_type", table_name="history_entry")
    op.drop_index("ix_history_entry_date", table_name="history_entry")
    op.drop_table("history_entry")

    op.drop_index("ix_managed_file_hash", table_name="managed_file")
    op.drop_index("ix_managed_file_academic_item_id", table_name="managed_file")
    op.drop_table("managed_file")

    op.drop_index("ix_academic_item_status", table_name="academic_item")
    op.drop_index("ix_academic_item_type", table_name="academic_item")
    op.drop_index("ix_academic_item_course_id", table_name="academic_item")
    op.drop_table("academic_item")

    op.drop_table("course_tags")

    op.drop_index("ix_course_code", table_name="course")
    op.drop_index("ix_course_semester_id", table_name="course")
    op.drop_table("course")

    op.drop_table("scheduled_task")

    op.drop_table("notification_definition")

    op.drop_table("naming_config")

    op.drop_foreign_key("import_source", "course", ["default_course_id"])
    op.drop_table("import_source")

    op.drop_table("root_folder")

    op.drop_table("custom_format")

    op.drop_table("file_profile")

    op.drop_table("tag")

    op.drop_index("ix_semester_year_term", table_name="semester")
    op.drop_table("semester")
