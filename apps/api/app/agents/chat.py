"""Chat agent — answer grounded in retrieved context, with citations."""
from __future__ import annotations

from app.agents.llm.port import LLMClient, Message
from app.rag.retriever import Retriever
from app.rag.types import Chunk, Citation

_SYSTEM = (
    "You are an expert AI career mentor. Answer the user's question using ONLY the "
    "provided context. Be concise, practical, and specific. Cite sources inline as "
    "[n] matching the numbered context. If the context is insufficient, say so and "
    "give your best general guidance without inventing facts."
)


def _format_context(chunks: list[Chunk]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        title = c.payload.get("title", "source")
        lines.append(f"[{i}] ({title}) {c.text}")
    return "\n\n".join(lines)


class ChatAgent:
    def __init__(self, llm: LLMClient, retriever: Retriever) -> None:
        self._llm = llm
        self._retriever = retriever

    def answer(
        self, query: str, filters: dict[str, str] | None = None, limit: int = 6
    ) -> tuple[str, list[Chunk], list[Citation]]:
        chunks, citations = self._retriever.retrieve_with_citations(query, limit, filters)
        context = _format_context(chunks)
        user = f"Context:\n{context}\n\nQuestion: {query}"
        answer = self._llm.complete(_SYSTEM, [Message("user", user)], tier="balanced")
        return answer, chunks, citations
