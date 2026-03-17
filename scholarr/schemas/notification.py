"""Notification schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    enabled: bool = True
    implementation: str = Field(min_length=1, max_length=255)
    config_contract: str | None = Field(default=None, max_length=255)
    fields: dict = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    enabled: bool | None = None
    implementation: str | None = Field(default=None, min_length=1, max_length=255)
    config_contract: str | None = Field(default=None, max_length=255)
    fields: dict | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    enabled: bool
    implementation: str
    config_contract: str | None
    fields: dict
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
