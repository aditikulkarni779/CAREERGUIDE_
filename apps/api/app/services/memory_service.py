"""Long-term conversational memory: summarize past chats, embed, recall.

Best-effort — any failure (LLM, vector store) degrades to no-memory rather than
breaking chat.
"""
from __future__ import annotations

import uuid

from app.agents.llm.port import LLMClient, Message
from app.rag.ports import DenseEmbedder, VectorStore

MEMORY_COLLECTION = "user_memory"

_SUMMARY_SYSTEM = (
    "Summarize the user's goals, skills, and interests from this conversation in "
    "2-3 concise sentences, written as durable notes about the user."
)


class MemoryService:
    def __init__(self, llm: LLMClient, embedder: DenseEmbedder, store: VectorStore) -> None:
        self._llm = llm
        self._embedder = embedder
        self._store = store

    def summarize_and_store(self, user_id: str, transcript: str) -> None:
        try:
            self._store.ensure_collection(MEMORY_COLLECTION)
            summary = self._llm.complete(
                _SUMMARY_SYSTEM, [Message("user", transcript)], tier="fast", max_tokens=200
            )
            if not summary.strip():
                return
            vec = self._embedder.embed([summary])[0]
            self._store.upsert(
                MEMORY_COLLECTION,
                ids=[str(uuid.uuid4())],
                texts=[summary],
                dense=[vec],
                sparse=None,
                payloads=[{"user_id": user_id}],
            )
        except Exception:  # noqa: BLE001 — memory is best-effort
            return

    def recall(self, user_id: str, query: str, limit: int = 3) -> list[str]:
        try:
            self._store.ensure_collection(MEMORY_COLLECTION)
            vec = self._embedder.embed([query])[0]
            chunks = self._store.hybrid_search(
                MEMORY_COLLECTION, vec, None, limit, {"user_id": user_id}
            )
            return [c.text for c in chunks]
        except Exception:  # noqa: BLE001
            return []
