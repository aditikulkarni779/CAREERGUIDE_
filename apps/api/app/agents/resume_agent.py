"""Resume agent — LLM-driven bullet rewrites and keyword suggestions."""

from __future__ import annotations

import json
import re
from typing import Any

from app.agents.llm.port import LLMClient, Message

_SYSTEM = (
    "You are an expert resume coach and ATS optimizer. Given a resume and a target "
    "role, produce concrete improvements. Rewrite weak bullet points to be "
    "achievement-oriented and quantified. Suggest missing keywords relevant to the "
    'role. Respond ONLY with compact JSON: {"improved_bullets": ["..."], '
    '"keyword_suggestions": ["..."], "summary_feedback": "..."}.'
)


class ResumeAgent:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def suggest(
        self, text: str, role_name: str | None, missing_keywords: list[str]
    ) -> dict[str, Any]:
        user = (
            f"Target role: {role_name or 'general software'}\n"
            f"Known missing keywords: {', '.join(missing_keywords) or 'none'}\n\n"
            f"Resume:\n{text[:4000]}"
        )
        try:
            raw = self._llm.complete(
                _SYSTEM, [Message("user", user)], tier="balanced", max_tokens=800
            )
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data: dict[str, Any] = json.loads(match.group() if match else raw)
            keywords = list(data.get("keyword_suggestions", missing_keywords))
            return {
                "improved_bullets": list(data.get("improved_bullets", []))[:8],
                "keyword_suggestions": keywords[:15],
                "summary_feedback": str(data.get("summary_feedback", "")),
            }
        except Exception:  # noqa: BLE001 — degrade gracefully
            return {
                "improved_bullets": [],
                "keyword_suggestions": missing_keywords,
                "summary_feedback": "Automated rewrite unavailable; add the missing keywords.",
            }
