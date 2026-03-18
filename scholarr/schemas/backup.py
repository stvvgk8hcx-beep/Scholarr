"""Backup schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BackupResponse(BaseModel):
    """Schema for backup response."""

    id: str
    filename: str
    size: int
    created_at: datetime
    description: str | None = None


class BackupListResponse(BaseModel):
    """Schema for backup list response."""

    backups: list[BackupResponse]
    total_count: int
    total_size: int


class BackupRestoreResponse(BaseModel):
    """Schema for backup restore response."""

    success: bool
    message: str
    details: dict[str, Any] | None = None
