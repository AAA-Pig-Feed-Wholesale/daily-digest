from __future__ import annotations

"""Application configuration.

Loads .env values via pydantic-settings and merges YAML configs in /configs.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"


def _load_yaml(path: Path) -> dict[str, Any]:
    # YAML is optional; return empty dict if not found.
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./data/app.db"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "knowledge_chunks"

    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_EMBEDDING_PROVIDER: str = "openai"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str | None = None

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str | None = None

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str | None = None

    GITHUB_TOKEN: str | None = None
    HF_TOKEN: str | None = None

    MIN_RELEVANCE_SCORE: int = 15

    DAILY_PIPELINE_HOUR: int = 7
    DAILY_PIPELINE_MINUTE: int = 0
    WEEKLY_PIPELINE_WEEKDAY: int = 0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

SOURCES_CONFIG: dict[str, Any] = _load_yaml(CONFIG_DIR / "sources.yaml")
TOPICS_CONFIG: dict[str, Any] = _load_yaml(CONFIG_DIR / "topics.yaml")
PROVIDERS_CONFIG: dict[str, Any] = _load_yaml(CONFIG_DIR / "providers.yaml")
PROMPTS_CONFIG: dict[str, Any] = _load_yaml(CONFIG_DIR / "prompts.yaml")
