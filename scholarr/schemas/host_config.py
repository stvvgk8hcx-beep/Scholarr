"""Host Configuration schemas — backed by application settings."""

from pydantic import BaseModel, Field


class HostConfigUpdate(BaseModel):
    debug: bool | None = None
    log_level: str | None = Field(default=None, max_length=20)
    enable_scheduler: bool | None = None
    enable_file_watcher: bool | None = None
    inbox_path: str | None = None


class HostConfigResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    debug: bool
    log_level: str
    enable_scheduler: bool
    enable_file_watcher: bool
    inbox_path: str | None
