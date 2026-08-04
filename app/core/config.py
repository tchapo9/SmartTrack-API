from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class Settings(BaseSettings):

    # Application
    APP_NAME: str = "SmartTrack API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    SECRET_KEY: str = secrets.token_urlsafe(32)

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    # Database Neon
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_UNPOOLED: Optional[str] = None
    NEON_BRANCH: Optional[str] = None


    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600


    # Security
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000"
    ]

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60


    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None


    @validator("DATABASE_URL", pre=True)
    def convert_database_url(cls, v):

        if v:

            v = v.strip().strip('"').strip("'")

            # asyncpg n'accepte pas sslmode
            if "sslmode=require" in v:
                v = v.replace(
                    "sslmode=require",
                    "ssl=require"
                )

            # SQLAlchemy async
            if v.startswith("postgresql://"):
                v = v.replace(
                    "postgresql://",
                    "postgresql+asyncpg://",
                    1
                )

            return v

        return v


    class Config:
        env_file = (
            ".env.local",
            ".env"
        )

        env_file_encoding = "utf-8"

        case_sensitive = True



settings = Settings()