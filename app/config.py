"""Application configuration."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "SKU Database Tracker"
    debug: bool = False

    # Database
    # Use /tmp directory for SQLite on cloud platforms (Render, Railway, etc.)
    # This directory is guaranteed to be writable
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:////tmp/sku_tracker.db"
    )

    # Security (add JWT secret, etc. when implementing auth)
    secret_key: str = "change-this-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
