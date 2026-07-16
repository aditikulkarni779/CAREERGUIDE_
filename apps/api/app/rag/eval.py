"""Lightweight retrieval evaluation (no LLM required).

Retrieval-only metrics over a golden set of (query -> relevant role). Generation
metrics (faithfulness, answer relevancy) come later once the chat agent exists.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.rag.retriever import Retriever


@dataclass
class GoldenItem:
    query: str
    relevant_role: str


def evaluate(retriever: Retriever, golden: list[GoldenItem], k: int = 5) -> dict[str, float]:
    hits1 = 0
    rr_sum = 0.0
    recall = 0
    for g in golden:
        chunks = retriever.retrieve(g.query, limit=k)
        roles = [c.payload.get("role") for c in chunks]
        if roles and roles[0] == g.relevant_role:
            hits1 += 1
        rank = next((i + 1 for i, r in enumerate(roles) if r == g.relevant_role), 0)
        rr_sum += 1 / rank if rank else 0.0
        if g.relevant_role in roles:
            recall += 1
    n = len(golden) or 1
    return {
        "hit@1": round(hits1 / n, 3),
        "mrr": round(rr_sum / n, 3),
        f"recall@{k}": round(recall / n, 3),
        "n": len(golden),
        "k": k,
    }


GOLDEN: list[GoldenItem] = [
    GoldenItem("how do I become an ML engineer", "ml-engineer"),
    GoldenItem("path to a machine learning engineer role with pytorch", "ml-engineer"),
    GoldenItem("becoming a data scientist", "data-scientist"),
    GoldenItem("statistics and data storytelling career", "data-scientist"),
    GoldenItem("frontend developer roadmap react typescript", "frontend-developer"),
    GoldenItem("building responsive user interfaces with javascript", "frontend-developer"),
    GoldenItem("backend api development with fastapi and postgres", "backend-developer"),
    GoldenItem("building data pipelines and warehouses", "data-engineer"),
    GoldenItem("building applications with LLMs and RAG", "ai-engineer"),
    GoldenItem("prompt design and vector databases with langchain", "ai-engineer"),
]
