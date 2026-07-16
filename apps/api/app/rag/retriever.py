"""Retriever — the single entrypoint agents call to get grounded context.

Pipeline: (rewrite) -> hybrid search (candidate pool) -> rerank -> top-N.
Query rewrite is identity for now; LLM-based rewrite arrives with the chat agent.
"""

from __future__ import annotations

from typing import Any

from app.rag.citations import build_citations
from app.rag.ports import DenseEmbedder, Reranker, SparseEmbedder, VectorStore
from app.rag.types import Chunk, Citation


class Retriever:
    def __init__(
        self,
        dense: DenseEmbedder,
        sparse: SparseEmbedder | None,
        store: VectorStore,
        collection: str,
        reranker: Reranker | None = None,
        candidate_k: int = 20,
    ) -> None:
        self._dense = dense
        self._sparse = sparse
        self._store = store
        self._collection = collection
        self._reranker = reranker
        self._candidate_k = candidate_k

    def _rewrite(self, query: str) -> str:
        return query.strip()

    def retrieve(
        self, query: str, limit: int = 8, filters: dict[str, Any] | None = None
    ) -> list[Chunk]:
        q = self._rewrite(query)
        pool = max(self._candidate_k, limit)
        dense_q = self._dense.embed([q])[0]
        sparse_q = self._sparse.embed_sparse([q])[0] if self._sparse else None
        candidates = self._store.hybrid_search(self._collection, dense_q, sparse_q, pool, filters)
        if self._reranker:
            return self._reranker.rerank(q, candidates, limit)
        return candidates[:limit]

    def retrieve_with_citations(
        self, query: str, limit: int = 8, filters: dict[str, Any] | None = None
    ) -> tuple[list[Chunk], list[Citation]]:
        chunks = self.retrieve(query, limit, filters)
        return chunks, build_citations(chunks)
