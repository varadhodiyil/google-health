"""Application configuration."""

import logging
import logging.config
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Google Health configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GOOGLE_HEALTH_",
        extra="ignore",
    )

    client_id: str
    client_secret: SecretStr

    access_token: SecretStr = SecretStr("")
    refresh_token: SecretStr = SecretStr("")

    redirect_uri: str = "http://127.0.0.1:8765"
    token_file: Path = Path("tokens.json")

    discovery_url: str = "https://health.googleapis.com/$discovery/rest?version=v4"

    timeout: float = 30.0
    log_level: int = logging.INFO


def configure_logging(
    level: int = logging.INFO,
) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=level,
        format=("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
