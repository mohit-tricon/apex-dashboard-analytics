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

    # Database (PostgreSQL).
    # Either set ``database_url`` directly, or the individual components below.
    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "apex_analytics"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_auto_create_tables: bool = False

    # Outbound integrations (team services).
    integration_timeout_seconds: float = 30.0
    skill_profiler_base_url: str = "http://skill-profiler-service:8001"
    assessment_base_url: str = "http://assessment-service:8004"
    learning_assistant_base_url: str = "http://learning-assistant-service:8002"

    @property
    def is_production(self):
        return self.environment == "production"

    @property
    def sqlalchemy_dsn(self) -> str:
        """SQLAlchemy connection string (sync psycopg driver)."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
