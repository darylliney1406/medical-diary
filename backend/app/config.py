from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ANTHROPIC_API_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Initial admin seed (optional — only used on first startup when no users exist)
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_NAME: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
