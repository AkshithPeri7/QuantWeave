import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate .env file: check current directory, apps/api parent, or repo root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent

env_files = [
    str(BASE_DIR / ".env"),
    str(REPO_ROOT / ".env"),
    str(REPO_ROOT.parent / ".env"),
]
env_file_path = next((f for f in env_files if os.path.exists(f)), str(REPO_ROOT / ".env"))


class Settings(BaseSettings):
    app_name: str = "QuantWeave API"
    app_version: str = "0.1.0"
    environment: str = "development"
    demo_mode: bool = True
    
    # Database
    database_url: str = Field(
        default="postgresql+psycopg://quantweave:quantweave_dev@localhost:5432/quantweave"
    )
    # Optional fallback for local dev when PostgreSQL is not running
    sqlite_fallback_url: str = "sqlite:///./quantweave_dev.db"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Security / JWT
    secret_key: str = Field(
        default="quantweave-super-secure-dev-secret-key-min-32-chars-long-2026",
        description="Secret key for JWT generation and verification. Must be at least 32 characters in production."
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    cookie_name: str = "access_token"
    cookie_secure: bool = False  # Set True in production (HTTPS)
    cookie_samesite: str = "lax"

    # AI Financial Copilot
    ai_provider: str = Field(
        default="mock",
        description="AI Provider: mock (default/offline/testing), gemini, openai",
    )
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key (optional for live AI)",
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional for live AI)",
    )
    ai_model_name: str = Field(
        default="gemini-1.5-flash",
        description="Model identifier for completion",
    )
    ai_max_tool_calls: int = Field(
        default=5,
        description="Maximum tool calls per turn to prevent recursive loops",
    )
    ai_timeout_seconds: int = Field(
        default=30,
        description="Maximum seconds to wait for AI provider",
    )

    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
