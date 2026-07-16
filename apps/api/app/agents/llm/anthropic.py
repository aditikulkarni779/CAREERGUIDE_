"""Anthropic Claude LLM adapter (REST via httpx)."""
from __future__ import annotations

from collections.abc import Iterator

import httpx

from app.agents.llm.port import Message, Tier

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"


class AnthropicClient:
    def __init__(self, api_key: str, models: dict[Tier, str]) -> None:
        self._key = api_key
        self._models = models

    def complete(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        body = {
            "model": self._models[tier],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        r = httpx.post(
            _URL,
            headers={
                "x-api-key": self._key,
                "anthropic-version": _VERSION,
                "content-type": "application/json",
            },
            json=body,
            timeout=60,
        )
        r.raise_for_status()
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()

    def stream(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        # Non-streaming fallback: yield the full completion once.
        yield self.complete(system, messages, tier, max_tokens, temperature)
