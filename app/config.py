"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "SKU Database Tracker"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./sku_tracker.db"

    # Security (add JWT secret, etc. when implementing auth)
    secret_key: str = "change-this-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
