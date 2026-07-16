import uuid

from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.agents.chat_stream import ChatStreamer
from app.agents.llm.fake import FakeLLM
from app.agents.llm.port import Message, Tier
from app.agents.verification import Verifier
from app.rag.embeddings import FakeDenseEmbedder
from app.rag.ingest import ingest_documents
from app.rag.retriever import Retriever
from app.rag.types import Chunk
from app.rag.vector_store import QdrantVectorStore
from app.services.conversation_service import create_conversation, list_messages
from app.services.memory_service import MemoryService

CREDS = {"email": "chat8@example.com", "password": "supersecret123"}

DOCS = [
    {
        "text": "become a machine learning engineer with python and pytorch",
        "payload": {"role": "ml-engineer", "title": "ML Roadmap", "source": "roadmap"},
    },
]


def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=CREDS)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _retriever() -> Retriever:
    qc = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=64)
    store = QdrantVectorStore(qc, "test", emb.dim, use_sparse=False)
    ingest_documents(store, emb, None, "kb", DOCS)
    return Retriever(emb, None, store, "kb", candidate_k=10)


def _handler(system: str, messages: list[Message], tier: Tier) -> str:
    if "router" in system.lower():
        return '{"intent": "skill_path", "target_role": "ml-engineer"}'
    if "fact-checker" in system.lower():
        return '{"supported": true, "reason": "grounded"}'
    return "Learn Python and ML fundamentals to become an ML engineer. [1]"


# ---- Conversation CRUD (endpoints, no LLM) ----
def test_conversation_crud(client: TestClient) -> None:
    h = _auth(client)
    assert client.get("/api/v1/conversations", headers=h).json() == []

    conv = client.post("/api/v1/conversations", headers=h).json()
    cid = conv["id"]
    assert conv["title"] == "New chat"

    assert len(client.get("/api/v1/conversations", headers=h).json()) == 1
    assert client.get(f"/api/v1/conversations/{cid}/messages", headers=h).json() == []

    assert client.delete(f"/api/v1/conversations/{cid}", headers=h).status_code == 204
    assert client.get("/api/v1/conversations", headers=h).json() == []


def test_conversation_ownership_404(client: TestClient) -> None:
    h = _auth(client)
    random_id = str(uuid.uuid4())
    assert client.get(f"/api/v1/conversations/{random_id}/messages", headers=h).status_code == 404


# ---- Streaming orchestration (direct, FakeLLM) ----
def test_stream_emits_events_and_persists(db_session: Session) -> None:
    from app.adapters.models import User

    user = User(email="s@example.com")
    db_session.add(user)
    db_session.commit()
    conv = create_conversation(db_session, user.id)

    llm = FakeLLM(_handler)
    streamer = ChatStreamer(llm, _retriever(), Verifier(llm), memory=None)
    events = "".join(streamer.stream(db_session, str(user.id), conv.id, "how to become an ML engineer"))

    assert "event: agent_step" in events
    assert "event: token" in events
    assert "event: citation" in events
    assert "event: done" in events
    assert '"verified": true' in events

    msgs = list_messages(db_session, conv.id)
    assert len(msgs) == 2
    assert msgs[0].role.value == "user"
    assert msgs[1].role.value == "assistant"
    assert msgs[1].content
    assert msgs[1].citations


# ---- Verifier ----
def test_verifier_supported() -> None:
    v = Verifier(FakeLLM(_handler))
    ok, _ = v.verify("answer", [Chunk(id="1", text="ctx", payload={})])
    assert ok is True


def test_verifier_empty_answer_rejected() -> None:
    v = Verifier(FakeLLM(_handler))
    ok, _ = v.verify("", [Chunk(id="1", text="ctx", payload={})])
    assert ok is False


# ---- Memory ----
def test_memory_store_and_recall() -> None:
    qc = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=64)
    store = QdrantVectorStore(qc, "mem", emb.dim, use_sparse=False)
    mem = MemoryService(FakeLLM(lambda s, m, t: "User wants to be an ML engineer, knows Python."), emb, store)

    mem.summarize_and_store("user-1", "I know Python and want to be an ML engineer")
    recalled = mem.recall("user-1", "machine learning career", limit=3)
    assert recalled
    assert "ML engineer" in recalled[0]

    # isolation: another user recalls nothing
    assert mem.recall("user-2", "machine learning career") == []
