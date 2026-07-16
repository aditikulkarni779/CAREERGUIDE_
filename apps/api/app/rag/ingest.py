"""Ingestion — chunk, embed (dense + sparse), upsert into the vector store."""
from __future__ import annotations

from typing import Any

from app.rag.chunking import chunk_text
from app.rag.ports import DenseEmbedder, SparseEmbedder, VectorStore


def ingest_documents(
    store: VectorStore,
    dense: DenseEmbedder,
    sparse: SparseEmbedder | None,
    collection: str,
    documents: list[dict[str, Any]],
    batch_size: int = 64,
) -> int:
    """documents: [{"text": str, "payload": {...}}]. Returns chunks upserted."""
    store.ensure_collection(collection)

    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_text(doc["text"], doc.get("payload", {})))

    total = 0
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c.text for c in batch]
        dense_vecs = dense.embed(texts)
        sparse_vecs = sparse.embed_sparse(texts) if sparse else None
        store.upsert(
            collection,
            ids=[c.id for c in batch],
            texts=texts,
            dense=dense_vecs,
            sparse=sparse_vecs,
            payloads=[c.payload for c in batch],
        )
        total += len(batch)
    return total
