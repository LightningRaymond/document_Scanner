"""Application configuration utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI service."""

    app_name: str = Field(
        default="Investor Document Intelligence API",
        description="Human-readable name exposed via the health endpoint.",
    )
    environment: str = Field(
        default="local",
        description="Environment label used for logging and telemetry.",
    )
    enable_mock_processing: bool = Field(
        default=False,
        description=(
            "Toggle mock implementations of pipeline dependencies to simplify early "
            "development and testing."
        ),
    )
    document_store_path: Path = Field(
        default=BASE_DIR / "data" / "documents.json",
        description="Filesystem location for persisted document metadata.",
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


def settings_summary() -> dict[str, Any]:
    """Provide a serialisable summary of key runtime settings."""

    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "enable_mock_processing": settings.enable_mock_processing,
        "document_store_path": str(settings.document_store_path),
    }
