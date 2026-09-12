from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./dc_ai_reports.db"
    REPORT_TEMPLATE_PATH: str = ""
    GMAIL_USER: Optional[str] = None
    GMAIL_APP_PASSWORD: Optional[str] = None
    JIRA_CSV_PATH: Optional[str] = None

    # Microsoft Graph
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/outlook/callback"

    # AI Providers
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    DEFAULT_AI_PROVIDER: str = "none"

    # Storage
    REPORT_STORAGE_PATH: str = "./generated_reports"
    MAX_UPLOAD_SIZE_MB: int = 20

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)
os.makedirs("./uploads", exist_ok=True)
