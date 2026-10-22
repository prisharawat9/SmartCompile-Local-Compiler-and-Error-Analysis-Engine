"""
Configuration management for SmartCompile backend.
Reads settings from environment variables and .env file.
"""

from typing import List, Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # Database
    DATABASE_PATH: str = os.getenv("SMARTCOMPILE_DB_PATH", "smartcompile.db")

    # AI Provider configuration: "mock", "openai", "gemini", "anthropic"
    AI_PROVIDER: str = "mock"

    # Generic AI Model setting (must be explicitly provided if provider=gemini)
    AI_MODEL: Optional[str] = None

    # Timeouts & Retries
    AI_TIMEOUT_SECONDS: float = 30.0
    AI_MAX_RETRIES: int = 2

    # OpenAI / Compatible API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None

    # Anthropic Claude API
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    # AI Request Timeout backward-compatibility alias
    AI_REQUEST_TIMEOUT: float = 30.0

    # Token Baseline Assumptions
    BASELINE_PROMPT_OVERHEAD_TOKENS: int = 250
    BASELINE_EXPECTED_COMPLETION_TOKENS: int = 180

    @property
    def active_provider(self) -> str:
        """Normalized active AI provider name."""
        return self.AI_PROVIDER.lower().strip()

    def get_model_for_provider(self, provider: Optional[str] = None) -> Optional[str]:
        """Get model ID for provider. For Gemini, uses AI_MODEL or GEMINI_MODEL without hardcoded fallback."""
        prov = (provider or self.active_provider).lower()
        if prov == "gemini":
            return self.AI_MODEL or self.GEMINI_MODEL
        elif prov == "openai":
            return self.AI_MODEL or self.OPENAI_MODEL
        elif prov == "anthropic":
            return self.AI_MODEL or self.ANTHROPIC_MODEL
        return self.AI_MODEL or "mock-smartcompile-v1"

    def has_api_key_for_provider(self, provider: Optional[str] = None) -> bool:
        """Check if required API key is present for the requested or active provider."""
        prov = (provider or self.active_provider).lower()
        if prov == "mock":
            return True
        elif prov == "openai":
            return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())
        elif prov == "gemini":
            return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())
        elif prov == "anthropic":
            return bool(self.ANTHROPIC_API_KEY and self.ANTHROPIC_API_KEY.strip())
        return False


settings = Settings()
