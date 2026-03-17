"""System status schemas."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    """Schema for system status response."""

    uptime_seconds: int
    version: str
    database_size: int
    file_count: int
    total_files_size: int
    memory_usage: Optional[dict] = None
    cpu_usage: Optional[float] = None
    timestamp: datetime
