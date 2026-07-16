from qdrant_client import QdrantClient

from app.rag.chunking import chunk_text
from app.rag.embeddings import FakeDenseEmbedder
from app.rag.ingest import ingest_documents
from app.rag.retriever import Retriever
from app.rag.vector_store import QdrantVectorStore


def test_chunking_overlap_and_payload() -> None:
    text = " ".join(f"w{i}" for i in range(400))
    chunks = chunk_text(text, {"src": "roadmap"}, max_words=100, overlap=20)
    assert len(chunks) >= 4
    assert all(c.payload["src"] == "roadmap" for c in chunks)
    assert all(len(c.text.split()) <= 100 for c in chunks)


def test_short_text_single_chunk() -> None:
    chunks = chunk_text("just a few words", {"a": 1})
    assert len(chunks) == 1
    assert chunks[0].payload["a"] == 1


def _fresh() -> tuple[FakeDenseEmbedder, QdrantVectorStore]:
    client = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=64)
    store = QdrantVectorStore(client, "test", emb.dim, use_sparse=False)
    return emb, store


def test_retrieve_ranks_relevant_first() -> None:
    emb, store = _fresh()
    docs = [
        {"text": "python machine learning pytorch model training", "payload": {"role": "ml"}},
        {"text": "javascript react frontend css components layout", "payload": {"role": "fe"}},
        {"text": "sql database postgres indexing query tuning", "payload": {"role": "data"}},
    ]
    n = ingest_documents(store, emb, None, "kb", docs)
    assert n == 3

    r = Retriever(emb, None, store, "kb")
    res = r.retrieve("python machine learning engineer", limit=3)
    assert res
    assert res[0].payload["role"] == "ml"
    assert res[0].text  # text round-trips from payload


def test_retrieve_metadata_filter() -> None:
    emb, store = _fresh()
    ingest_documents(
        store,
        emb,
        None,
        "kb",
        [
            {"text": "python machine learning", "payload": {"role": "ml"}},
            {"text": "python data engineering", "payload": {"role": "data"}},
        ],
    )
    r = Retriever(emb, None, store, "kb")
    res = r.retrieve("python", limit=5, filters={"role": "data"})
    assert res
    assert all(c.payload["role"] == "data" for c in res)
