"""Gemini LLM adapter (REST via httpx — no SDK dependency)."""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.agents.llm.port import Message, Tier

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_RETRY_STATUS = {429, 503}
_MAX_RETRIES = 4


class GeminiClient:
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
        model = self._models[tier]
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
        ]
        body = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}

        data = self._post_with_retry(model, body)
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()

    def _post_with_retry(self, model: str, body: dict[str, Any]) -> dict[str, Any]:
        last: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            r = httpx.post(
                f"{_BASE}/{model}:generateContent",
                params={"key": self._key},
                json=body,
                timeout=60,
            )
            if r.status_code in _RETRY_STATUS and attempt < _MAX_RETRIES - 1:
                time.sleep(2**attempt)  # 1, 2, 4s backoff
                continue
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                last = e
                break
            return r.json()  # type: ignore[no-any-return]
        raise last if last else RuntimeError("gemini request failed")
