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
    embed_provider: Literal["gemini", "voyage", "bge_local"] = "bge_local"
    voyage_api_key: str = ""
    embed_model_dense: str = "BAAI/bge-small-en-v1.5"  # 384-dim
    embed_model_sparse: str = "Qdrant/bm25"
    embed_cache_ttl_sec: int = 604800  # 7 days

    # RAG / vector store
    qdrant_collection_prefix: str = "cc"
    rag_top_k: int = 20
    rag_final_k: int = 8

    # Datastores
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Auth
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 30
    refresh_token_ttl_days: int = 14

    # OAuth
    oauth_github_id: str = ""
    oauth_github_secret: str = ""
    oauth_google_id: str = ""
    oauth_google_secret: str = ""
    frontend_url: str = "http://localhost:3000"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
