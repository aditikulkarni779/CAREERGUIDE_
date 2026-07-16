"""LangGraph orchestration: planner -> chat. Specialist routes expand in later weeks."""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.chat import ChatAgent
from app.agents.llm.port import LLMClient
from app.agents.planner import Planner
from app.agents.state import CopilotState
from app.rag.retriever import Retriever


def build_graph(llm: LLMClient, retriever: Retriever) -> Any:
    planner = Planner(llm)
    chat = ChatAgent(llm, retriever)

    def planner_node(state: CopilotState) -> dict[str, Any]:
        intent, role = planner.classify(state["query"])
        return {"intent": intent, "target_role": role, "trace": [f"planner:{intent}"]}

    def chat_node(state: CopilotState) -> dict[str, Any]:
        # role-aware filter when the planner found a target role
        role = state.get("target_role")
        filters: dict[str, str] | None = {"role": role} if role else None
        answer, chunks, citations = chat.answer(state["query"], filters=filters)
        # fall back to unfiltered retrieval if the role filter returned nothing
        if not chunks and filters:
            answer, chunks, citations = chat.answer(state["query"])
        return {
            "answer": answer,
            "retrieved": chunks,
            "citations": citations,
            "trace": [*state.get("trace", []), "chat"],
        }

    g: StateGraph[CopilotState] = StateGraph(CopilotState)
    g.add_node("planner", planner_node)
    g.add_node("chat", chat_node)
    g.add_edge(START, "planner")
    g.add_edge("planner", "chat")
    g.add_edge("chat", END)
    return g.compile()


def run_chat(graph: Any, query: str, user_id: str) -> CopilotState:
    result: CopilotState = graph.invoke({"query": query, "user_id": user_id, "trace": []})
    return result
