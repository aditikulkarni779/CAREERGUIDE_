"""LLM port — the interface agents depend on. Adapters live alongside."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

Tier = Literal["fast", "balanced", "deep"]


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


class LLMClient(Protocol):
    def complete(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str: ...

    def stream(
        self,
        system: str,
        messages: list[Message],
        tier: Tier = "balanced",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Iterator[str]: ...
