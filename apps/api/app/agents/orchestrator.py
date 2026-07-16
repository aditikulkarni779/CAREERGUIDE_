"""Process-wide singleton wiring the compiled graph from real adapters."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.agents.chat_stream import ChatStreamer
from app.agents.graph import build_graph
from app.agents.llm.factory import get_llm
from app.agents.verification import Verifier
from app.core.config import get_settings
from app.rag.factory import build_dense_embedder, build_vector_store, get_retriever
from app.services.memory_service import MemoryService


@lru_cache
def get_graph() -> Any:
    return build_graph(get_llm(), get_retriever())


@lru_cache
def get_streamer() -> ChatStreamer:
    settings = get_settings()
    llm = get_llm()
    retriever = get_retriever()
    verifier = Verifier(llm)
    embedder = build_dense_embedder(settings)
    store = build_vector_store(settings, embedder.dim)
    memory = MemoryService(llm, embedder, store)
    return ChatStreamer(llm, retriever, verifier, memory)
