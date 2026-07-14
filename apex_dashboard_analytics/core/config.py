"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and/or a .env file.

    Environment variables are prefixed with ``APEX_`` (e.g. ``APEX_LOG_LEVEL``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "apex-dashboard-analytics"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = False

    # File logging: logs are always written as JSON for easy parsing.
    log_to_file: bool = True
    log_file: str = "logs/app.log"
    log_file_max_bytes: int = 10 * 1024 * 1024  # 10 MiB per file
    log_file_backup_count: int = 5

    @property
    def is_production(self):
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
