"""Chat endpoint — runs the LangGraph orchestrator (non-streaming for now).

Streaming (SSE) + conversation persistence arrive in Week 8.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.adapters.models import User
from app.agents.graph import run_chat
from app.agents.orchestrator import get_graph
from app.api.deps import get_current_user
from app.schemas import ChatAsk, ChatResponse, CitationOut

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask(data: ChatAsk, user: User = Depends(get_current_user)) -> ChatResponse:
    graph: Any = get_graph()
    state = run_chat(graph, data.query, str(user.id))
    citations = [
        CitationOut(title=c.title, source=c.source, url=c.url, snippet=c.snippet)
        for c in state.get("citations", [])
    ]
    return ChatResponse(
        answer=state.get("answer", ""),
        intent=state.get("intent", "chat"),
        target_role=state.get("target_role"),
        citations=citations,
    )
