from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FastAPI Modular App"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "sqlite+aiosqlite:///./app.db"
    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings loaded from environment variables.

    Returns:
        Settings: Cached settings instance.
    """
    return Settings()
