"""Shared agent graph state."""
from __future__ import annotations

from typing import Literal, TypedDict

from app.rag.types import Chunk, Citation

IntentName = Literal["chat", "skill_path", "resume", "github", "interview", "other"]


class CopilotState(TypedDict, total=False):
    user_id: str
    query: str
    intent: IntentName
    target_role: str | None
    retrieved: list[Chunk]
    citations: list[Citation]
    answer: str
    trace: list[str]
