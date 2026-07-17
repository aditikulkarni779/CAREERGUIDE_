"""GitHub agent — narrates a recruiter impression + improvement tips (scores stay
deterministic; the LLM only summarizes)."""
from __future__ import annotations

from typing import Any

from app.agents.llm.port import LLMClient, Message

_SYSTEM = (
    "You are a technical recruiter reviewing a candidate's GitHub. Given their "
    "computed scores and top languages, write 2-3 sentences on the recruiter "
    "impression, then 2-3 concrete, specific improvement tips. Be honest and brief."
)


class GithubAgent:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def summarize(self, username: str, scores: dict[str, Any]) -> str:
        user = (
            f"GitHub user: {username}\n"
            f"Recruiter score: {scores['recruiter_score']}/100\n"
            f"Repository score: {scores['repo_score']} · Diversity: {scores['diversity_score']} "
            f"· Activity/health: {scores['health_score']}\n"
            f"Top languages: {', '.join(scores['languages'][:6]) or 'none'}\n"
            f"Top repos: {', '.join(r['name'] for r in scores['top_repos']) or 'none'}"
        )
        try:
            return self._llm.complete(
                _SYSTEM, [Message("user", user)], tier="balanced", max_tokens=350
            ).strip()
        except Exception:  # noqa: BLE001 — narration is optional
            return ""
