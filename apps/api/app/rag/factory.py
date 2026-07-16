"""Wire the RAG pipeline from settings (BGE-local dense + sparse, Redis cache, Qdrant)."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.rag.embeddings import BgeDenseEmbedder, BgeSparseEmbedder, CachedDenseEmbedder
from app.rag.ports import DenseEmbedder, SparseEmbedder, VectorStore
from app.rag.retriever import Retriever
from app.rag.vector_store import QdrantVectorStore


def build_dense_embedder(settings: Settings) -> DenseEmbedder:
    base = BgeDenseEmbedder(settings.embed_model_dense)
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url)
        client.ping()
        return CachedDenseEmbedder(
            base, client, settings.embed_model_dense, settings.embed_cache_ttl_sec
        )
    except Exception:  # noqa: BLE001 — cache is optional; fall back to uncached
        return base


def build_sparse_embedder(settings: Settings) -> SparseEmbedder:
    return BgeSparseEmbedder(settings.embed_model_sparse)


def build_vector_store(settings: Settings, dense_dim: int) -> VectorStore:
    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.qdrant_url)
    return QdrantVectorStore(client, settings.qdrant_collection_prefix, dense_dim, use_sparse=True)


@lru_cache
def get_retriever(collection: str = "roadmap_kb") -> Retriever:
    settings = get_settings()
    dense = build_dense_embedder(settings)
    sparse = build_sparse_embedder(settings)
    store = build_vector_store(settings, dense.dim)
    return Retriever(dense, sparse, store, collection)
