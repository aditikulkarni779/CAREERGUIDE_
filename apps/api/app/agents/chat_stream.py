"""Streaming chat orchestration — emits Server-Sent Events.

Flow: persist user msg -> planner -> recall memory -> retrieve -> stream tokens
-> emit citations -> verify -> persist assistant msg -> done.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.models import MessageRole
from app.agents.llm.port import LLMClient, Message
from app.agents.planner import Planner
from app.agents.verification import Verifier
from app.rag.retriever import Retriever
from app.rag.types import Chunk
from app.services.conversation_service import add_message
from app.services.memory_service import MemoryService
from app.services.skill_service import normalize_slug

_SYSTEM = (
    "You are an expert AI career mentor. Use the provided context and any user "
    "memory to answer. Be concise, practical, specific. Cite sources inline as [n]. "
    "If context is insufficient, say so and give best general guidance without "
    "inventing facts."
)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _format_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(
        f"[{i}] ({c.payload.get('title', 'source')}) {c.text}" for i, c in enumerate(chunks, 1)
    )


class ChatStreamer:
    def __init__(
        self,
        llm: LLMClient,
        retriever: Retriever,
        verifier: Verifier,
        memory: MemoryService | None = None,
    ) -> None:
        self._llm = llm
        self._retriever = retriever
        self._planner = Planner(llm)
        self._verifier = verifier
        self._memory = memory

    def stream(
        self, db: Session, user_id: str, conversation_id: uuid.UUID, query: str
    ) -> Iterator[str]:
        add_message(db, conversation_id, MessageRole.user, query)

        yield _sse("agent_step", {"agent": "planner"})
        intent, role = self._planner.classify(query)
        yield _sse("agent_step", {"agent": "planner", "intent": intent, "role": role})

        memories = self._memory.recall(user_id, query) if self._memory else []

        role_slug = normalize_slug(role) if role else None
        filters = {"role": role_slug} if role_slug else None
        chunks, citations = self._retriever.retrieve_with_citations(query, 6, filters)
        if not chunks and filters:
            chunks, citations = self._retriever.retrieve_with_citations(query, 6)
        yield _sse("agent_step", {"agent": "retriever", "found": len(chunks)})

        mem_text = "\n".join(f"- {m}" for m in memories)
        user_prompt = (
            f"User memory:\n{mem_text or 'none'}\n\n"
            f"Context:\n{_format_context(chunks)}\n\nQuestion: {query}"
        )

        answer_parts: list[str] = []
        for token in self._llm.stream(_SYSTEM, [Message("user", user_prompt)], tier="balanced"):
            answer_parts.append(token)
            yield _sse("token", {"t": token})
        answer = "".join(answer_parts).strip()

        citation_dicts = [
            {"title": c.title, "source": c.source, "url": c.url, "snippet": c.snippet}
            for c in citations
        ]
        for c in citation_dicts:
            yield _sse("citation", c)

        supported, reason = self._verifier.verify(answer, chunks)
        add_message(
            db,
            conversation_id,
            MessageRole.assistant,
            answer,
            citations=citation_dicts,
            agent_trace=[f"planner:{intent}", "retriever", "chat", f"verified:{supported}"],
        )
        yield _sse("done", {"intent": intent, "verified": supported, "reason": reason})
