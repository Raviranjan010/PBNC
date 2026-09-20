from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    PROJECT_NAME: str = "PaperMind"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = "papermind-super-secret-key-change-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    # Default to SQLite for easy local dev / testing if PostgreSQL is not active
    DATABASE_URL: str = "sqlite+aiosqlite:///./papermind.db"
    SYNC_DATABASE_URL: Optional[str] = "sqlite:///./papermind.db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False  # Set to True for inline async execution in tests/dev

    # Storage
    STORAGE_DIR: str = os.path.join(os.getcwd(), "storage")
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25MB
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
    ]

    # OCR Settings
    TESSERACT_CMD: Optional[str] = None  # Auto-detected or specified
    OCR_LANG: str = "eng"

    # AI Provider Settings
    AI_PROVIDER: str = "heuristic"  # 'gemini', 'openai', or 'heuristic'
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL_NAME: str = "gemini-1.5-flash"

    # Confidence Thresholds
    CONFIDENCE_VERIFIED_MIN: float = 0.90
    CONFIDENCE_PARTIAL_MIN: float = 0.70

    # Rate Limiting
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 20

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

settings = Settings()
