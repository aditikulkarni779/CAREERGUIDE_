"""Reranker adapters — local cross-encoder (fastembed) + a fake for tests."""
from __future__ import annotations

from app.rag.types import Chunk


class BgeReranker:
    """Local cross-encoder reranker via fastembed (no API key)."""

    def __init__(self, model: str) -> None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self._m = TextCrossEncoder(model_name=model)

    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        if not chunks:
            return []
        scores = list(self._m.rerank(query, [c.text for c in chunks]))
        for chunk, score in zip(chunks, scores, strict=True):
            chunk.score = float(score)
        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
        return ranked[:top_n]


class FakeReranker:
    """Deterministic reranker for tests: scores by query-term overlap."""

    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        terms = set(query.lower().split())
        for c in chunks:
            words = c.text.lower().split()
            c.score = sum(1 for w in words if w in terms) / (len(words) or 1)
        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
        return ranked[:top_n]
