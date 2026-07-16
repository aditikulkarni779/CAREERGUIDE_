"""Turn retrieved chunks into citations for grounded, sourced answers."""
from __future__ import annotations

from app.rag.types import Chunk, Citation

_SNIPPET_LEN = 180


def build_citations(chunks: list[Chunk]) -> list[Citation]:
    """Dedup by (title, url); keep first (highest-ranked) occurrence."""
    seen: set[tuple[str, str | None]] = set()
    citations: list[Citation] = []
    for c in chunks:
        title = str(c.payload.get("title", "Untitled"))
        source = str(c.payload.get("source", "unknown"))
        url = c.payload.get("url")
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        snippet = c.text[:_SNIPPET_LEN].rstrip()
        if len(c.text) > _SNIPPET_LEN:
            snippet += "…"
        citations.append(Citation(title=title, source=source, url=url, snippet=snippet))
    return citations
