from qdrant_client import QdrantClient

from app.rag.citations import build_citations
from app.rag.embeddings import FakeDenseEmbedder
from app.rag.eval import GoldenItem, evaluate
from app.rag.ingest import ingest_documents
from app.rag.rerank import FakeReranker
from app.rag.retriever import Retriever
from app.rag.types import Chunk
from app.rag.vector_store import QdrantVectorStore

DOCS = [
    {"text": "python machine learning pytorch model training deep", "payload": {"role": "ml", "title": "ML", "source": "roadmap"}},
    {"text": "javascript react frontend css components interface", "payload": {"role": "fe", "title": "FE", "source": "roadmap"}},
    {"text": "sql postgres data pipeline warehouse engineering", "payload": {"role": "de", "title": "DE", "source": "roadmap"}},
]


def _retriever(reranker: FakeReranker | None) -> Retriever:
    client = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=64)
    store = QdrantVectorStore(client, "test", emb.dim, use_sparse=False)
    ingest_documents(store, emb, None, "kb", DOCS)
    return Retriever(emb, None, store, "kb", reranker, candidate_k=10)


def test_reranker_reorders_and_limits() -> None:
    r = _retriever(FakeReranker())
    res = r.retrieve("python machine learning", limit=2)
    assert len(res) == 2
    assert res[0].payload["role"] == "ml"


def test_citations_dedup_and_snippet() -> None:
    chunks = [
        Chunk(id="1", text="A" * 300, payload={"title": "T1", "source": "roadmap", "url": "u1"}),
        Chunk(id="2", text="B", payload={"title": "T1", "source": "roadmap", "url": "u1"}),
        Chunk(id="3", text="C", payload={"title": "T2", "source": "blog", "url": None}),
    ]
    cites = build_citations(chunks)
    assert len(cites) == 2  # T1 deduped
    assert cites[0].snippet.endswith("…")
    assert cites[0].url == "u1"


def test_evaluate_metrics_reasonable() -> None:
    r = _retriever(FakeReranker())
    golden = [
        GoldenItem("python machine learning pytorch", "ml"),
        GoldenItem("javascript react frontend", "fe"),
        GoldenItem("sql postgres data pipeline", "de"),
    ]
    m = evaluate(r, golden, k=3)
    assert m["hit@1"] == 1.0
    assert m["recall@3"] == 1.0
    assert m["mrr"] == 1.0
