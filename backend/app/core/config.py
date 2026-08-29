"""
SIH26034 - Legal Metrology Compliance System
Core configuration module.

Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

# Ensure .env (repo root) is loaded into the real process environment.
# pydantic-settings only feeds .env values into THIS Settings object; it does
# NOT set os.environ. Modules that call os.getenv(...) directly (e.g. Groq
# extraction in app/ai/extraction.py) need this explicit load or they silently
# see None and fall back to regex-only extraction.
load_dotenv()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://sih26034:sih26034_password@localhost:5432/sih26034"

    # JWT Authentication
    JWT_SECRET: str = "change-this-to-a-long-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # File Upload
    UPLOAD_DIR: str = "../data/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # AI extraction (Groq) — optional, falls back to regex extraction if unset
    GROQ_API_KEY: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
