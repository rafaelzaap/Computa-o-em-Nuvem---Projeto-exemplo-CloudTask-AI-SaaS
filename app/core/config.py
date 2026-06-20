"""Application settings loaded from environment variables.

Aula 4 introduces one rule that keeps cloud projects sane: configuration stays
outside the source code. Local values may live in `.env`; production values
should come from the platform, secrets manager or orchestration layer.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for CloudTask AI SaaS."""

    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "cloudtask-ai-saas"
    app_port: int = 8000
    secret_key: str = "change-me-please"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://cloudtask:cloudtask@db:5432/cloudtask"

    storage_mode: Literal["local", "s3"] = "local"
    local_uploads_dir: str = "local_uploads"
    aws_region: str = "us-east-1"
    s3_bucket_name: str = ""
    s3_presigned_url_expires: int = Field(default=3600, ge=60, le=604800)

    force_https: bool = False
    trusted_hosts: str = "localhost,127.0.0.1,*"
    hsts_max_age_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        """Return whether the app is running in local development mode."""
        return self.app_env == "development"

    @property
    def trusted_host_list(self) -> list[str]:
        """Return trusted hosts from a comma-separated environment variable."""
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so every module sees the same configuration."""
    return Settings()
