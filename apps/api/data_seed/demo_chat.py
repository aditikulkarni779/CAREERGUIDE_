"""Live end-to-end demo of the chat orchestrator (real LLM + retriever).

    python -m data_seed.demo_chat
"""
from __future__ import annotations

from app.agents.graph import run_chat
from app.agents.orchestrator import get_graph


def main() -> None:
    graph = get_graph()
    for q in [
        "How do I become an ML engineer?",
        "What should I learn to build applications with LLMs and RAG?",
    ]:
        state = run_chat(graph, q, user_id="demo")
        print(f"Q: {q}")
        print(f"  intent={state['intent']}  role={state.get('target_role')}")
        print(f"  answer: {state['answer'][:400]}")
        print(f"  citations: {[c.title for c in state['citations']]}")
        print()


if __name__ == "__main__":
    main()
