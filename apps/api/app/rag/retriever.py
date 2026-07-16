"""Retriever — the single entrypoint agents call to get grounded context."""
from __future__ import annotations

from typing import Any

from app.rag.ports import DenseEmbedder, SparseEmbedder, VectorStore
from app.rag.types import Chunk


class Retriever:
    def __init__(
        self,
        dense: DenseEmbedder,
        sparse: SparseEmbedder | None,
        store: VectorStore,
        collection: str,
    ) -> None:
        self._dense = dense
        self._sparse = sparse
        self._store = store
        self._collection = collection

    def retrieve(
        self, query: str, limit: int = 8, filters: dict[str, Any] | None = None
    ) -> list[Chunk]:
        dense_q = self._dense.embed([query])[0]
        sparse_q = self._sparse.embed_sparse([query])[0] if self._sparse else None
        return self._store.hybrid_search(self._collection, dense_q, sparse_q, limit, filters)
