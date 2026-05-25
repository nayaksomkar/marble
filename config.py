"""
Configuration loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Marble"

    # Database
    DATABASE_URL: str = "sqlite:///./marble.db"

    # LLM API keys
    GROQ_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None

    # LLM defaults
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.7
    MAX_ITERATIONS: int = 3

    # Security
    SECRET_KEY: str = "dev-secret-key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()