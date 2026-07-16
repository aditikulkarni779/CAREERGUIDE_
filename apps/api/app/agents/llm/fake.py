"""Deterministic fake LLM for tests and offline runs."""
from __future__ import annotations

from collections.abc import Callable, Iterator

from app.agents.llm.port import Message, Tier


class FakeLLM:
    """handler(system, messages, tier) -> str. Defaults to echoing the last message."""

    def __init__(self, handler: Callable[[str, list[Message], Tier], str] | None = None) -> None:
        self._handler = handler

    def complete(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        if self._handler:
            return self._handler(system, messages, tier)
        return f"echo: {messages[-1].content}" if messages else ""

    def stream(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        text = self.complete(system, messages, tier, max_tokens, temperature)
        for word in text.split(" "):
            yield word + " "
