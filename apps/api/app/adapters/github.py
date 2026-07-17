"""GitHub REST API adapter (public profile + repos)."""
from __future__ import annotations

from typing import Any

import httpx

_BASE = "https://api.github.com"


class GitHubError(Exception):
    """GitHub API failure (rate limit, network)."""


class GitHubClient:
    def __init__(self, token: str) -> None:
        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "career-copilot",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        try:
            return httpx.get(f"{_BASE}{path}", headers=self._headers, params=params, timeout=20)
        except httpx.HTTPError as e:
            raise GitHubError(str(e)) from e

    def get_user(self, username: str) -> dict[str, Any] | None:
        r = self._get(f"/users/{username}")
        if r.status_code == 404:
            return None
        if r.status_code == 403:
            raise GitHubError("GitHub rate limit or forbidden")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]

    def get_repos(self, username: str, limit: int = 100) -> list[dict[str, Any]]:
        r = self._get(
            f"/users/{username}/repos",
            params={"per_page": min(limit, 100), "sort": "updated", "type": "owner"},
        )
        if r.status_code == 404:
            return []
        if r.status_code == 403:
            raise GitHubError("GitHub rate limit or forbidden")
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]
