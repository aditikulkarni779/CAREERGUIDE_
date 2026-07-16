"""Run the retrieval eval against the live roadmap KB and record a baseline.

    python -m data_seed.eval_rag

Ingests the seed docs (idempotent) then reports hit@1 / MRR / recall@k and
writes the metrics to docs/rag_eval_baseline.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.rag.eval import GOLDEN, evaluate
from app.rag.factory import (
    build_dense_embedder,
    build_reranker,
    build_sparse_embedder,
    build_vector_store,
)
from app.rag.ingest import ingest_documents
from app.rag.retriever import Retriever
from data_seed.seed_rag import COLLECTION, DOCS

BASELINE = Path(__file__).resolve().parents[1] / "docs" / "rag_eval_baseline.json"


def main() -> None:
    s = get_settings()
    dense = build_dense_embedder(s)
    sparse = build_sparse_embedder(s)
    store = build_vector_store(s, dense.dim)
    ingest_documents(store, dense, sparse, COLLECTION, DOCS)

    retriever = Retriever(dense, sparse, store, COLLECTION, build_reranker(s), s.rag_top_k)
    metrics = evaluate(retriever, GOLDEN, k=5)

    print("RAG retrieval eval:")
    for key, val in metrics.items():
        print(f"  {key:<10} {val}")

    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(
        json.dumps(
            {"metrics": metrics, "recorded_at": datetime.now(timezone.utc).isoformat()}, indent=2
        ),
        encoding="utf-8",
    )
    print(f"\nbaseline written to {BASELINE}")


if __name__ == "__main__":
    main()
