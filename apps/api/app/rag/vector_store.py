"""Qdrant vector store adapter — hybrid (dense + sparse) with RRF fusion."""
from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient, models

from app.rag.types import Chunk, SparseVector

DENSE = "dense"
SPARSE = "sparse"


class QdrantVectorStore:
    def __init__(
        self,
        client: QdrantClient,
        prefix: str,
        dense_dim: int,
        use_sparse: bool = True,
    ) -> None:
        self._c = client
        self._prefix = prefix
        self._dim = dense_dim
        self._use_sparse = use_sparse

    def _name(self, name: str) -> str:
        return f"{self._prefix}_{name}"

    def ensure_collection(self, name: str) -> None:
        full = self._name(name)
        if self._c.collection_exists(full):
            return
        sparse_cfg = {SPARSE: models.SparseVectorParams()} if self._use_sparse else None
        self._c.create_collection(
            collection_name=full,
            vectors_config={
                DENSE: models.VectorParams(size=self._dim, distance=models.Distance.COSINE)
            },
            sparse_vectors_config=sparse_cfg,
        )

    def upsert(
        self,
        name: str,
        ids: list[str],
        texts: list[str],
        dense: list[list[float]],
        sparse: list[SparseVector] | None,
        payloads: list[dict[str, Any]],
    ) -> None:
        points: list[models.PointStruct] = []
        for i, pid in enumerate(ids):
            vectors: dict[str, Any] = {DENSE: dense[i]}
            if self._use_sparse and sparse is not None:
                vectors[SPARSE] = models.SparseVector(
                    indices=sparse[i].indices, values=sparse[i].values
                )
            payload = dict(payloads[i])
            payload["text"] = texts[i]
            points.append(models.PointStruct(id=pid, vector=vectors, payload=payload))
        self._c.upsert(collection_name=self._name(name), points=points)

    def _filter(self, flt: dict[str, Any] | None) -> models.Filter | None:
        if not flt:
            return None
        conditions: list[models.Condition] = [
            models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in flt.items()
        ]
        return models.Filter(must=conditions)

    def hybrid_search(
        self,
        name: str,
        dense_query: list[float],
        sparse_query: SparseVector | None,
        limit: int,
        flt: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        full = self._name(name)
        qfilter = self._filter(flt)

        if self._use_sparse and sparse_query is not None:
            prefetch = [
                models.Prefetch(query=dense_query, using=DENSE, limit=limit * 2, filter=qfilter),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_query.indices, values=sparse_query.values
                    ),
                    using=SPARSE,
                    limit=limit * 2,
                    filter=qfilter,
                ),
            ]
            res = self._c.query_points(
                collection_name=full,
                prefetch=prefetch,
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=limit,
                with_payload=True,
            )
        else:
            res = self._c.query_points(
                collection_name=full,
                query=dense_query,
                using=DENSE,
                limit=limit,
                query_filter=qfilter,
                with_payload=True,
            )

        chunks: list[Chunk] = []
        for p in res.points:
            payload = dict(p.payload or {})
            text = payload.pop("text", "")
            chunks.append(Chunk(id=str(p.id), text=text, payload=payload, score=p.score or 0.0))
        return chunks
