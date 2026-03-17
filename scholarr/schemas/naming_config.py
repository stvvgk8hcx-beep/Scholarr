"""Naming Configuration schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NamingConfigUpdate(BaseModel):
    course_folder_pattern: str | None = None
    academic_item_folder_pattern: str | None = None
    file_naming_pattern: str | None = None
    date_format: str | None = None


class NamingConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_folder_pattern: str
    academic_item_folder_pattern: str
    file_naming_pattern: str
    date_format: str
    created_at: datetime
    updated_at: datetime
