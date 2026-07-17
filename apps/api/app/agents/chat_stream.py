"""Streaming chat orchestration — emits Server-Sent Events.

Flow: persist user msg -> planner -> recall memory -> retrieve -> stream tokens
-> emit citations -> verify -> persist assistant msg -> done.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import MessageRole, Profile
from app.agents.llm.port import LLMClient, Message
from app.agents.planner import Planner
from app.agents.verification import Verifier
from app.rag.retriever import Retriever
from app.rag.types import Chunk
from app.services.conversation_service import add_message, list_messages
from app.services.gap_service import resolve_role
from app.services.memory_service import MemoryService
from app.services.roadmap_service import get_items, get_or_generate_roadmap
from app.services.skill_service import normalize_slug

_HISTORY_TURNS = 6

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

    def _skill_path(
        self, db: Session, user_id: str, role_slug: str | None
    ) -> tuple[list[str], str]:
        """Generate a roadmap for the user's Twin; return (sse_events, summary)."""
        profile = db.scalar(select(Profile).where(Profile.user_id == uuid.UUID(user_id)))
        role = resolve_role(db, role_slug)
        if profile is None or role is None:
            return [], ""
        roadmap = get_or_generate_roadmap(db, profile, role)
        items = get_items(db, roadmap.id)
        event = _sse(
            "roadmap",
            {
                "role": role.name,
                "version": roadmap.version,
                "total_hours": (roadmap.rationale or {}).get("total_hours", 0),
                "items": [
                    {
                        "skill": it.skill_name,
                        "milestone": it.milestone,
                        "est_hours": it.est_hours,
                        "importance": it.importance,
                        "why": (it.explanation or {}).get("why", ""),
                    }
                    for it in items
                ],
            },
        )
        summary = "\n".join(
            f"- Milestone {it.milestone}: {it.skill_name} (~{it.est_hours}h, "
            f"importance {it.importance}/100)"
            for it in items
        )
        return [event], summary

    def stream(
        self, db: Session, user_id: str, conversation_id: uuid.UUID, query: str
    ) -> Iterator[str]:
        add_message(db, conversation_id, MessageRole.user, query)

        yield _sse("agent_step", {"agent": "planner"})
        intent, role = self._planner.classify(query)
        yield _sse("agent_step", {"agent": "planner", "intent": intent, "role": role})

        memories = self._memory.recall(user_id, query) if self._memory else []

        # Semantic retrieval over the real KB (Wikipedia + roadmaps); no role filter needed.
        chunks, citations = self._retriever.retrieve_with_citations(query, 6)
        yield _sse("agent_step", {"agent": "retriever", "found": len(chunks)})

        # Skill-path workflow: compute gaps + generate a roadmap for the user's Twin.
        roadmap_summary = ""
        if intent == "skill_path":
            role_slug = normalize_slug(role) if role else None
            events, roadmap_summary = self._skill_path(db, user_id, role_slug)
            yield from events

        mem_text = "\n".join(f"- {m}" for m in memories)
        user_prompt = (
            f"User memory:\n{mem_text or 'none'}\n\n"
            f"Context:\n{_format_context(chunks)}\n\n"
            f"Roadmap generated for this user (reference it in your answer):\n"
            f"{roadmap_summary or 'none'}\n\n"
            f"Question: {query}"
        )

        # Prior turns for multi-turn follow-ups (exclude the just-persisted current msg).
        history = list_messages(db, conversation_id)[:-1][-_HISTORY_TURNS:]
        llm_messages: list[Message] = [
            Message("assistant" if m.role.value == "assistant" else "user", m.content)
            for m in history
            if m.role.value in ("user", "assistant")
        ]
        llm_messages.append(Message("user", user_prompt))

        answer_parts: list[str] = []
        for token in self._llm.stream(_SYSTEM, llm_messages, tier="balanced"):
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
