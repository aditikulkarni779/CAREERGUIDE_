"""Document chunking — paragraph-aware, word-budgeted, with overlap."""
from __future__ import annotations

import re
import uuid
from typing import Any

from app.rag.types import Chunk

_PARA = re.compile(r"\n\s*\n")


def _words(text: str) -> list[str]:
    return text.split()


def chunk_text(
    text: str,
    payload: dict[str, Any] | None = None,
    max_words: int = 180,
    overlap: int = 30,
) -> list[Chunk]:
    """Split text into ~max_words chunks with word overlap, never crossing documents."""
    payload = payload or {}
    text = text.strip()
    if not text:
        return []

    # Build word stream while remembering paragraph boundaries loosely.
    paragraphs = [p.strip() for p in _PARA.split(text) if p.strip()]
    words: list[str] = []
    for p in paragraphs:
        words.extend(_words(p))

    if len(words) <= max_words:
        return [Chunk(id=str(uuid.uuid4()), text=" ".join(words), payload=dict(payload))]

    chunks: list[Chunk] = []
    step = max(1, max_words - overlap)
    for start in range(0, len(words), step):
        window = words[start : start + max_words]
        if not window:
            break
        meta = dict(payload)
        meta["chunk_index"] = len(chunks)
        chunks.append(Chunk(id=str(uuid.uuid4()), text=" ".join(window), payload=meta))
        if start + max_words >= len(words):
            break
    return chunks
