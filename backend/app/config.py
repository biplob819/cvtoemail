"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (SQLite for local dev, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./autojobapply.db"
    database_url_sync: str = "sqlite:///./autojobapply.db"

    # OpenAI
    openai_api_key: Optional[str] = None

    # SMTP / Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    notification_email: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # App
    app_name: str = "Auto Job Apply"
    debug: bool = True
    cors_origins: str = "http://localhost:5173"

    # File storage
    upload_dir: str = "uploads"
    cv_output_dir: str = "cv_output"

    # Scraper
    proxy_url: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
