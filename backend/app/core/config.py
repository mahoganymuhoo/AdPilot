from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    APP_NAME: str = "AdPilot"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://adpilot:adpilot@localhost:5432/adpilot"
    SYNC_DATABASE_URL: str = "postgresql://adpilot:adpilot@localhost:5432/adpilot"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 gün

    # AI Provider: "claude" veya "openai" — kullanıcı seçer
    DEFAULT_AI_PROVIDER: Literal["claude", "openai"] = "claude"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    OPENAI_MODEL: str = "gpt-4o"

    # Etsy OAuth
    ETSY_API_KEY: str = ""
    ETSY_SHARED_SECRET: str = ""
    ETSY_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/etsy/callback"

    # Celery sync interval (saniye)
    ETSY_SYNC_INTERVAL_SECONDS: int = 900  # 15 dakika

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
