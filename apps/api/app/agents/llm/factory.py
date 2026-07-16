"""Build the configured LLM client from settings (Gemini | Anthropic)."""
from __future__ import annotations

from functools import lru_cache

from app.agents.llm.anthropic import AnthropicClient
from app.agents.llm.gemini import GeminiClient
from app.agents.llm.groq import GroqClient
from app.agents.llm.port import LLMClient, Tier
from app.core.config import Settings, get_settings


def build_llm(settings: Settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        models: dict[Tier, str] = {
            "fast": settings.gemini_model_fast,
            "balanced": settings.gemini_model_balanced,
            "deep": settings.gemini_model_deep,
        }
        return GeminiClient(settings.gemini_api_key, models)
    if settings.llm_provider == "groq":
        gmodels: dict[Tier, str] = {
            "fast": settings.groq_model_fast,
            "balanced": settings.groq_model_balanced,
            "deep": settings.groq_model_deep,
        }
        return GroqClient(settings.groq_api_key, gmodels)
    if settings.llm_provider == "anthropic":
        amodels: dict[Tier, str] = {
            "fast": settings.anthropic_model_fast,
            "balanced": settings.anthropic_model_balanced,
            "deep": settings.anthropic_model_deep,
        }
        return AnthropicClient(settings.anthropic_api_key, amodels)
    raise ValueError(f"unsupported llm_provider for chat: {settings.llm_provider}")


@lru_cache
def get_llm() -> LLMClient:
    return build_llm(get_settings())
