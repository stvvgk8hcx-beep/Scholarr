"""Command schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from scholarr.db.models import CommandStatusEnum


class CommandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    body: dict
    priority: int = Field(default=0, ge=0)
    trigger: str | None = Field(default=None, max_length=255)


class CommandResponse(BaseModel):
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


class CommandListResponse(BaseModel):
    items: list[CommandResponse]
    total: int
