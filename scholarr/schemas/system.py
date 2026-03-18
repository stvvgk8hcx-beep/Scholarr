"""System status schemas."""

from datetime import datetime

from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    """Schema for system status response."""

    uptime_seconds: int
    version: str
    database_size: int
    file_count: int
    total_files_size: int
    memory_usage: dict | None = None
    cpu_usage: float | None = None
    timestamp: datetime
