"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_host: str = "0.0.0.0"  # nosec B104 - Required for Docker
    api_port: int = 8000

    # Groq (free tier - recommended for zero-cost deployment)
    groq_api_key: SecretStr | None = None

    # OpenAI (optional)
    openai_api_key: SecretStr | None = None

    # Azure OpenAI (optional)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: SecretStr | None = None
    azure_openai_deployment: str | None = None
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    azure_openai_api_version: str = "2024-02-01"

    @model_validator(mode="after")
    def validate_llm_config(self) -> "Settings":
        """Ensure at least one LLM provider is configured."""
        has_groq = self.groq_api_key is not None
        has_openai = self.openai_api_key is not None
        has_azure = (
            self.azure_openai_endpoint is not None
            and self.azure_openai_api_key is not None
            and self.azure_openai_deployment is not None
        )
        if not has_groq and not has_openai and not has_azure:  # pragma: no cover
            raise ValueError(
                "At least one LLM provider must be configured: "
                "GROQ_API_KEY (free), OPENAI_API_KEY, or Azure OpenAI"
            )
        return self

    # LangSmith (Optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: SecretStr | None = None
    langchain_project: str = "equity-research-agent"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "sec_filings"

    # Redis
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600  # 1 hour default

    # Companies House (UK)
    companies_house_api_key: SecretStr | None = None

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Telegram Bot
    telegram_bot_token: SecretStr | None = None
    api_base_url: str = "http://localhost:8000"

    # yfinance settings
    yfinance_cache_ttl: int = 300  # 5 minutes for market data

    # SEC EDGAR settings
    sec_user_agent: str = "EquityResearchAgent contact@example.com"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def use_groq(self) -> bool:
        """Check if Groq should be used (free tier priority)."""
        return self.groq_api_key is not None

    @property
    def use_azure_openai(self) -> bool:
        """Check if Azure OpenAI should be used."""
        has_endpoint = bool(self.azure_openai_endpoint)
        has_key = self.azure_openai_api_key is not None and bool(
            self.azure_openai_api_key.get_secret_value()
        )
        return has_endpoint and has_key


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
