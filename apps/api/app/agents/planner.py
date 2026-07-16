"""Planner agent — classify intent and extract a target role."""
from __future__ import annotations

import json
import re

from app.agents.llm.port import LLMClient, Message
from app.agents.state import IntentName

_INTENTS = ("chat", "skill_path", "resume", "github", "interview", "other")

_SYSTEM = (
    "You are a router for a career-guidance assistant. Classify the user's message "
    "into exactly one intent and extract a target job role if present. "
    "Intents: skill_path (how to become / what to learn for a role), resume, github, "
    "interview, chat (general career Q&A), other. "
    'Respond ONLY with compact JSON: {"intent": "...", "target_role": "... or null"}.'
)

_ROLE_HINTS = {
    "ml engineer": "ml-engineer",
    "machine learning": "ml-engineer",
    "data scientist": "data-scientist",
    "ai engineer": "ai-engineer",
    "software engineer": "software-engineer",
    "backend": "backend-developer",
    "frontend": "frontend-developer",
    "full stack": "full-stack-developer",
    "data engineer": "data-engineer",
}


def _heuristic(query: str) -> tuple[IntentName, str | None]:
    q = query.lower()
    role = next((slug for k, slug in _ROLE_HINTS.items() if k in q), None)
    if any(w in q for w in ("become", "how do i get", "learn to", "roadmap", "path to")):
        return "skill_path", role
    if "resume" in q or "cv" in q:
        return "resume", role
    if "github" in q or "repo" in q:
        return "github", role
    if "interview" in q:
        return "interview", role
    return "chat", role


class Planner:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def classify(self, query: str) -> tuple[IntentName, str | None]:
        try:
            raw = self._llm.complete(_SYSTEM, [Message("user", query)], tier="fast", max_tokens=120)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group() if match else raw)
            intent = data.get("intent", "chat")
            if intent not in _INTENTS:
                intent = "chat"
            role = data.get("target_role")
            role = None if role in (None, "null", "") else str(role)
            return intent, role
        except Exception:  # noqa: BLE001 — fall back to heuristic on any LLM/parse failure
            return _heuristic(query)
