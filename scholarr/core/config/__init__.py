"""Configuration management for Scholarr."""

import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden with SCHOLARR_ prefixed env vars,
    e.g. SCHOLARR_DATABASE_URL, SCHOLARR_DEBUG, etc.
    """

    # App info
    app_name: str = "Scholarr"
    version: str = "0.1.0"

    # Server
    debug: bool = False
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8787
    log_level: str = "INFO"

    # Database — default to MySQL, fall back to SQLite for dev
    database_url: str = "mysql+aiomysql://scholarr:scholarr@localhost:3306/scholarr"

    # Security
    api_key: str = ""
    secret_key: str = "change-this-in-production"

    # CORS and trusted hosts
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8787"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]

    # Feature flags
    enable_scheduler: bool = True
    enable_file_watcher: bool = True

    # Sentry (optional)
    sentry_dsn: Optional[str] = None

    # File paths
    data_dir: str = "./data"
    upload_dir: str = "./data/uploads"
    backup_dir: str = "./data/backups"
    inbox_path: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="SCHOLARR_",
        env_file=".env",
        case_sensitive=False,
    )

    def __init__(self, **data):
        """Initialize settings. Auto-generates API key if not set."""
        super().__init__(**data)
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings()


# Global instance for easy import
settings = get_settings()
