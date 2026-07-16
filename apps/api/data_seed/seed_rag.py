"""Seed a tiny roadmap knowledge base and demo retrieval (live, BGE + Qdrant).

python -m data_seed.seed_rag
"""

from __future__ import annotations

from app.core.config import get_settings
from app.rag.factory import build_dense_embedder, build_sparse_embedder, build_vector_store
from app.rag.ingest import ingest_documents
from app.rag.retriever import Retriever

COLLECTION = "roadmap_kb"

DOCS: list[dict] = [
    {
        "text": (
            "To become a Machine Learning Engineer, master Python and strong fundamentals in "
            "statistics and linear algebra. Learn classical ML with scikit-learn, then deep "
            "learning with PyTorch. Build end-to-end projects: data pipeline, model training, "
            "evaluation, and deployment. Study MLOps: Docker, model serving, and experiment "
            "tracking. Cloud experience on AWS or GCP is a strong differentiator."
        ),
        "payload": {"title": "ML Engineer Roadmap", "role": "ml-engineer", "source": "roadmap"},
    },
    {
        "text": (
            "A Data Scientist path centers on Python, SQL, pandas, and NumPy for data wrangling. "
            "Learn statistics, hypothesis testing, and machine learning. Practice storytelling "
            "with data visualization and clear communication of results to stakeholders."
        ),
        "payload": {
            "title": "Data Scientist Roadmap",
            "role": "data-scientist",
            "source": "roadmap",
        },
    },
    {
        "text": (
            "Frontend Developers focus on JavaScript and TypeScript, the React framework, and "
            "modern CSS. Learn component architecture, state management, accessibility, and "
            "performance. Ship polished, responsive interfaces and use Git for collaboration."
        ),
        "payload": {"title": "Frontend Roadmap", "role": "frontend-developer", "source": "roadmap"},
    },
    {
        "text": (
            "Backend Developers build APIs with frameworks like FastAPI, model data in "
            "PostgreSQL, and cache with Redis. Learn authentication, testing, Docker, and CI/CD. "
            "Understand system design, scaling, and observability."
        ),
        "payload": {"title": "Backend Roadmap", "role": "backend-developer", "source": "roadmap"},
    },
    {
        "text": (
            "Data Engineers specialize in SQL and Python, building reliable data pipelines. "
            "Work with warehouses, orchestration, and batch and streaming processing. "
            "Containerize with Docker and deploy on cloud platforms like AWS."
        ),
        "payload": {"title": "Data Engineer Roadmap", "role": "data-engineer", "source": "roadmap"},
    },
    {
        "text": (
            "AI Engineers build applications on top of large language models. Learn prompt "
            "design, retrieval-augmented generation with vector databases, and orchestration "
            "with LangChain or LangGraph. Serve models behind FastAPI and evaluate output quality."
        ),
        "payload": {"title": "AI Engineer Roadmap", "role": "ai-engineer", "source": "roadmap"},
    },
]


def main() -> None:
    s = get_settings()
    dense = build_dense_embedder(s)
    sparse = build_sparse_embedder(s)
    store = build_vector_store(s, dense.dim)

    n = ingest_documents(store, dense, sparse, COLLECTION, DOCS)
    print(f"ingested {n} chunks into {s.qdrant_collection_prefix}_{COLLECTION}\n")

    retriever = Retriever(dense, sparse, store, COLLECTION)
    for query in ["how do I become an ML engineer?", "building apps with LLMs and RAG"]:
        print(f"Q: {query}")
        for c in retriever.retrieve(query, limit=3):
            print(f"  {c.score:.3f}  {c.payload.get('title'):<24} {c.text[:70]}...")
        print()


if __name__ == "__main__":
    main()
