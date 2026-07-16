"""Groq LLM adapter (OpenAI-compatible chat completions, via httpx)."""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.agents.llm.port import Message, Tier

_URL = "https://api.groq.com/openai/v1/chat/completions"
_RETRY_STATUS = {429, 503}
_MAX_RETRIES = 4


class GroqClient:
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
        chat: list[dict[str, str]] = []
        if system:
            chat.append({"role": "system", "content": system})
        chat.extend({"role": m.role, "content": m.content} for m in messages)
        body = {
            "model": self._models[tier],
            "messages": chat,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = self._post_with_retry(body)
        choices = data.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", "")).strip()

    def _post_with_retry(self, body: dict[str, Any]) -> dict[str, Any]:
        last: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            r = httpx.post(
                _URL,
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=60,
            )
            if r.status_code in _RETRY_STATUS and attempt < _MAX_RETRIES - 1:
                time.sleep(2**attempt)
                continue
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                last = e
                break
            return r.json()  # type: ignore[no-any-return]
        raise last if last else RuntimeError("groq request failed")
