from qdrant_client import QdrantClient

from app.agents.chat import ChatAgent
from app.agents.graph import build_graph, run_chat
from app.agents.llm.fake import FakeLLM
from app.agents.llm.port import Message, Tier
from app.agents.planner import Planner
from app.rag.embeddings import FakeDenseEmbedder
from app.rag.ingest import ingest_documents
from app.rag.retriever import Retriever
from app.rag.vector_store import QdrantVectorStore

DOCS = [
    {
        "text": "become a machine learning engineer with python pytorch and mlops",
        "payload": {"role": "ml-engineer", "title": "ML Roadmap", "source": "roadmap"},
    },
    {
        "text": "frontend developer react javascript typescript css",
        "payload": {"role": "frontend-developer", "title": "FE Roadmap", "source": "roadmap"},
    },
]


def _retriever() -> Retriever:
    client = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=64)
    store = QdrantVectorStore(client, "test", emb.dim, use_sparse=False)
    ingest_documents(store, emb, None, "kb", DOCS)
    return Retriever(emb, None, store, "kb", candidate_k=10)


def _router_handler(system: str, messages: list[Message], tier: Tier) -> str:
    if "router" in system.lower():
        return '{"intent": "skill_path", "target_role": "ml-engineer"}'
    return "To become an ML engineer, learn Python and ML fundamentals. [1]"


def test_planner_parses_llm_json() -> None:
    p = Planner(FakeLLM(_router_handler))
    intent, role = p.classify("how do I become an ML engineer?")
    assert intent == "skill_path"
    assert role == "ml-engineer"


def test_planner_heuristic_fallback_on_bad_json() -> None:
    p = Planner(FakeLLM(lambda s, m, t: "not json at all"))
    intent, role = p.classify("what roadmap to become a data scientist?")
    assert intent == "skill_path"
    assert role == "data-scientist"


def test_chat_agent_grounds_and_cites() -> None:
    chat = ChatAgent(FakeLLM(_router_handler), _retriever())
    answer, chunks, citations = chat.answer("how to become an ML engineer")
    assert answer
    assert chunks
    assert any(c.title == "ML Roadmap" for c in citations)


def test_graph_planner_routes_and_chat_answers() -> None:
    graph = build_graph(FakeLLM(_router_handler), _retriever())
    state = run_chat(graph, "how do I become an ML engineer?", user_id="u1")
    assert state["intent"] == "skill_path"
    assert state["target_role"] == "ml-engineer"
    assert state["answer"]
    assert state["citations"]
    assert "planner:skill_path" in state["trace"]
    assert "chat" in state["trace"]
