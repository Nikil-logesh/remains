"""Application configuration loaded from environment variables."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIGNALPOST_", extra="ignore")

    registry_base_url: str = "https://data.brreg.no/enhetsregisteret/api"
    request_timeout_seconds: float = Field(default=10.0, gt=0)
    cache_path: Path = Path("signalpost.sqlite3")
    log_level: str = "INFO"


def get_settings() -> Settings:
    load_dotenv()
    return Settings()
