"""RAG ports (interfaces). Adapters implement these; the domain depends only here."""
from __future__ import annotations

from typing import Any, Protocol

from app.rag.types import Chunk, SparseVector


class DenseEmbedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SparseEmbedder(Protocol):
    def embed_sparse(self, texts: list[str]) -> list[SparseVector]: ...


class VectorStore(Protocol):
    def ensure_collection(self, name: str) -> None: ...

    def upsert(
        self,
        name: str,
        ids: list[str],
        texts: list[str],
        dense: list[list[float]],
        sparse: list[SparseVector] | None,
        payloads: list[dict[str, Any]],
    ) -> None: ...

    def hybrid_search(
        self,
        name: str,
        dense_query: list[float],
        sparse_query: SparseVector | None,
        limit: int,
        flt: dict[str, Any] | None = None,
    ) -> list[Chunk]: ...


class Reranker(Protocol):
    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]: ...
