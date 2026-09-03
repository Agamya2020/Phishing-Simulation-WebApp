from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis (reserved for future queues, caching, or rate limiting)
    REDIS_URL: str = "redis://localhost:6379"

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False

    # Tracking
    TRACKING_BASE_URL: str = "http://localhost:8000"

    # Admin authentication
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-this-password"
    JWT_SECRET_KEY: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.APP_ENV.lower() != "production":
            return self

        insecure_values = {
            "change-this-password",
            "change-this-secret-key",
            "replace-this-with-a-long-random-secret",
            "replace-with-a-long-random-secret",
        }

        if self.ADMIN_PASSWORD in insecure_values:
            raise ValueError("ADMIN_PASSWORD must be changed in production.")
        if self.JWT_SECRET_KEY in insecure_values:
            raise ValueError("JWT_SECRET_KEY must be changed in production.")
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters in production."
            )
        if not self.TRACKING_BASE_URL.startswith("https://"):
            raise ValueError("TRACKING_BASE_URL must use HTTPS in production.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
