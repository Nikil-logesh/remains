"""Application settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SIGNALPOST_", extra="ignore"
    )

    registry_base_url: str = "https://data.brreg.no/enhetsregisteret/api"
    request_timeout_seconds: float = Field(default=10.0, gt=0)
    cache_path: Path = Path("signalpost.sqlite3")
    log_level: str = "INFO"
    financial_dataset_path: Path | None = None
    nvidia_api_key: str | None = None
    nvidia_model: str = "google/gemma-4-31b-it"
    max_requests: int = Field(default=20, gt=0)
    concurrency: int = Field(default=4, gt=0)


def get_settings() -> Settings:
    return Settings()
