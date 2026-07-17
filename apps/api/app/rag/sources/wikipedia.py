"""Wikipedia article fetcher.

Uses the REST summary endpoint (CDN-cached, generous limits, follows redirects)
for the lead extract, with an opensearch fallback to resolve ambiguous titles.
Content is CC BY-SA 4.0 — we keep the canonical URL for attribution and surface
it in citations.
"""
from __future__ import annotations

import time
from urllib.parse import quote

import httpx

_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
_ACTION = "https://en.wikipedia.org/w/api.php"
_UA = "AICareerCopilot/0.1 (educational project; contact via github)"
_MAX_CHARS = 5000


def article_url(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"


def fetch_extract(title: str, timeout: float = 20.0) -> tuple[str, str] | None:
    """Return (extract, url) for an exact title via the REST summary endpoint."""
    url = _REST + quote(title.replace(" ", "_"), safe="")
    try:
        r = httpx.get(url, headers={"User-Agent": _UA}, timeout=timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError):
        return None
    if data.get("type") == "disambiguation":
        return None
    extract = (data.get("extract") or "").strip()
    if not extract:
        return None
    page_url = (
        data.get("content_urls", {}).get("desktop", {}).get("page")
        or article_url(data.get("title", title))
    )
    return extract[:_MAX_CHARS], page_url


def search_title(query: str, timeout: float = 20.0) -> str | None:
    """Resolve a free-text query to the best-matching article title (opensearch)."""
    params = {"action": "opensearch", "search": query, "limit": "1", "format": "json"}
    try:
        r = httpx.get(_ACTION, params=params, headers={"User-Agent": _UA}, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError):
        return None
    titles = data[1] if len(data) > 1 else []
    return titles[0] if titles else None


def fetch_best(query: str, override: str | None = None) -> tuple[str, str] | None:
    """Try an exact/override title, then fall back to search resolution."""
    result = fetch_extract(override or query)
    if result is not None:
        return result
    resolved = search_title(query)
    if resolved and resolved != (override or query):
        return fetch_extract(resolved)
    return None


def fetch_extracts_batch(
    titles: list[str], batch_size: int = 20, timeout: float = 30.0
) -> dict[str, tuple[str, str]]:
    """Fetch full-article extracts for many titles in few requests (action API).

    Returns {requested_title: (extract, url)}. Titles that are missing/empty are
    omitted. Handles MediaWiki normalization + redirects so results map back to
    the originally requested titles.
    """
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "exlimit": "max",
            "redirects": "1",
            "titles": "|".join(batch),
            "format": "json",
        }
        try:
            r = httpx.get(_ACTION, params=params, headers={"User-Agent": _UA}, timeout=timeout)
            r.raise_for_status()
            query = r.json().get("query", {})
        except (httpx.HTTPError, ValueError):
            continue

        norm = {n["from"]: n["to"] for n in query.get("normalized", [])}
        redir = {rd["from"]: rd["to"] for rd in query.get("redirects", [])}

        by_resolved: dict[str, str] = {}
        for requested in batch:
            resolved = norm.get(requested, requested)
            resolved = redir.get(resolved, resolved)
            by_resolved[resolved] = requested
        for page in query.get("pages", {}).values():
            if "missing" in page:
                continue
            extract = (page.get("extract") or "").strip()
            if not extract:
                continue
            final = page.get("title", "")
            requested = by_resolved.get(final, final)
            out[requested] = (extract[:_MAX_CHARS], article_url(final))
        time.sleep(0.5)
    return out
