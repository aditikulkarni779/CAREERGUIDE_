"""Process-wide singleton wiring the compiled graph from real adapters."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.agents.graph import build_graph
from app.agents.llm.factory import get_llm
from app.rag.factory import get_retriever


@lru_cache
def get_graph() -> Any:
    return build_graph(get_llm(), get_retriever())
