from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
import os
from pathlib import Path


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./marble.db"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Marble Research Assistant"

    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.7

    MAX_ITERATIONS: int = 3
    CRITIQUE_THRESHOLD: int = 8

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()