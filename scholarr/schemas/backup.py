"""Backup schemas."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel


class BackupResponse(BaseModel):
    """Schema for backup response."""

    id: str
    filename: str
    size: int
    created_at: datetime
    description: Optional[str] = None


class BackupListResponse(BaseModel):
    """Schema for backup list response."""

    backups: list[BackupResponse]
    total_count: int
    total_size: int


class BackupRestoreResponse(BaseModel):
    """Schema for backup restore response."""

    success: bool
    message: str
    details: Optional[dict[str, Any]] = None
