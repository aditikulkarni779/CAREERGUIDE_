"""RAG value objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SparseVector:
    indices: list[int]
    values: list[float]


@dataclass
class Chunk:
    id: str
    text: str
    payload: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
