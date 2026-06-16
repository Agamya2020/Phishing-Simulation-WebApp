from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/phishguard"
    REDIS_URL: str = "redis://localhost:6379"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    TRACKING_BASE_URL: str = "http://localhost:8000"


settings = Settings()
