"""
Application configuration using pydantic-settings.
All secrets loaded from environment variables — never hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "QueryMind"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── API ───────────────────────────────────────────────────────────────────
    API_PREFIX: str = "/api"
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://querymind:querymind@localhost:5432/querymind"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # SQLite fallback for lightweight demo mode
    USE_SQLITE: bool = False
    SQLITE_URL: str = "sqlite+aiosqlite:///./querymind_demo.db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_TTL_SECONDS: int = 300          # 5 min for query results
    SCHEMA_CACHE_TTL_SECONDS: int = 600   # 10 min for schema metadata

    # ── LLM — Groq (primary) ──────────────────────────────────────────────────
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.0
    GROQ_MAX_TOKENS: int = 4096

    # ── LLM — Gemini (fallback) ───────────────────────────────────────────────
    GOOGLE_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── LangSmith (observability) ─────────────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = Field(default="")
    LANGCHAIN_PROJECT: str = "querymind"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: str = "1/minute"

    # ── Query Execution ───────────────────────────────────────────────────────
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_RESULT_ROWS: int = 1000
    MAX_QUERY_LENGTH: int = 500
    MAX_RETRY_ATTEMPTS: int = 3

    # ── CSV Upload ────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_SCHEMA: str = "uploads"
    UPLOAD_CLEANUP_HOURS: int = 24

    # ── Schema Selector ───────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    TOP_K_TABLES: int = 5

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default="change-me-in-production-use-32-char-random")

    @field_validator("GROQ_API_KEY", "GOOGLE_API_KEY", mode="before")
    @classmethod
    def _strip_quotes(cls, v: str) -> str:
        return v.strip().strip('"').strip("'") if v else v

    @property
    def effective_database_url(self) -> str:
        return self.SQLITE_URL if self.USE_SQLITE else self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton — call get_settings() anywhere in the app."""
    return Settings()


settings = get_settings()
