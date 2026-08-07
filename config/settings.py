from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ERR_INVALID_URL: str = "OLLAMA_BASE_URL must start with http:// or https://"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama server base URL"
    )
    ollama_model: str = Field(default="llama3.1:8b", description="Ollama model name")
    ollama_timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")
    ollama_max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
    ollama_retry_base_delay: float = Field(
        default=1.0, gt=0, description="Base delay for exponential backoff"
    )
    ollama_retry_max_delay: float = Field(default=10.0, gt=0, description="Max delay for retries")

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of workers")

    log_file: str = Field(default="negotiation_log.json", description="Log file path")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_format: Literal["json", "text"] = Field(default="json")

    default_rounds: int = Field(default=5, ge=1, le=10, description="Default negotiation rounds")
    max_rounds: int = Field(default=10, ge=1, le=20, description="Maximum allowed rounds")
    min_rounds: int = Field(default=1, ge=1, le=10, description="Minimum allowed rounds")

    secret_key: str = Field(default="change-me-in-production", description="Secret key for API")
    api_key_enabled: bool = Field(default=False, description="Enable API key authentication")

    http_client_pool_limit: int = Field(default=10, ge=1, description="HTTP connection pool limit")
    http_client_keepalive: int = Field(default=30, ge=1, description="HTTP keepalive seconds")

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(ERR_INVALID_URL)
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
