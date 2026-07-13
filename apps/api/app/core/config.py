"""Application settings loaded from environment (12-factor)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    env: Literal["local", "staging", "prod"] = "local"
    log_level: str = "INFO"

    # LLM
    llm_provider: Literal["gemini", "groq", "openrouter", "anthropic"] = "gemini"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""

    # Embeddings
    embed_provider: Literal["gemini", "voyage", "bge_local"] = "gemini"
    voyage_api_key: str = ""

    # Datastores
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Auth
    jwt_secret: str = "change-me-in-prod"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
