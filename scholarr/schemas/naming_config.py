"""Naming Configuration schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NamingConfigUpdate(BaseModel):
    renaming_enabled: bool | None = None
    replace_illegal_characters: bool | None = None
    standard_file_format: str | None = Field(default=None, max_length=255)
    folder_format: str | None = Field(default=None, max_length=255)
    course_folder_format: str | None = Field(default=None, max_length=255)
    semester_folder_format: str | None = Field(default=None, max_length=255)
    colon_replacement_format: str | None = Field(default=None, max_length=10)


class NamingConfigResponse(BaseModel):
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
