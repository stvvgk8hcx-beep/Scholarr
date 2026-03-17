"""Health check schemas."""

from typing import Optional, Any
from pydantic import BaseModel


class HealthCheckComponent(BaseModel):
    """Schema for a health check component."""

    name: str
    status: str  # healthy, warning, critical
    message: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str  # healthy, warning, critical
    timestamp: str
    components: list[HealthCheckComponent]


class DiskSpaceInfo(BaseModel):
    """Schema for disk space information."""

    total_gb: Optional[float] = None
    used_gb: Optional[float] = None
    available_gb: Optional[float] = None
    percent_used: Optional[float] = None


class DatabaseInfo(BaseModel):
    """Schema for database status."""

    connected: bool
    url: str


class SystemInfo(BaseModel):
    """Schema for system information."""

    python_version: str
    platform: str
    app_version: str


class SchedulerInfo(BaseModel):
    """Schema for scheduler status."""

    enabled: bool


class ErrorStats(BaseModel):
    """Schema for error statistics."""

    last_hour: int
    last_day: int


class HealthStatusResponse(BaseModel):
    """Detailed health status response with system diagnostics."""

    status: str  # healthy, warning, critical
    timestamp: str
    database: DatabaseInfo
    disk_space: DiskSpaceInfo
    system: SystemInfo
    scheduler: SchedulerInfo
    file_watcher: SchedulerInfo
    recent_errors: ErrorStats
