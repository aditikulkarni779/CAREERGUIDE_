import uuid

import httpx
import pytest
from qdrant_client import QdrantClient

from app.rag.embeddings import FakeDenseEmbedder
from app.rag.sources import wikipedia
from app.rag.vector_store import QdrantVectorStore


def _rest_response(payload: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status, json=payload, request=httpx.Request("GET", "https://en.wikipedia.org/x")
    )


def test_fetch_extract_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "type": "standard",
        "title": "Machine learning",
        "extract": "ML is a field.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Machine_learning"}},
    }
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _rest_response(payload))
    result = wikipedia.fetch_extract("Machine learning")
    assert result is not None
    text, url = result
    assert text == "ML is a field."
    assert url == "https://en.wikipedia.org/wiki/Machine_learning"


def test_fetch_extract_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _rest_response({}, status=404))
    assert wikipedia.fetch_extract("Nonexistent Topic XYZ") is None


def test_fetch_extract_disambiguation(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"type": "disambiguation", "title": "Docker", "extract": "several meanings"}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _rest_response(payload))
    assert wikipedia.fetch_extract("Docker") is None


def test_fetch_extract_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object, **k: object) -> httpx.Response:
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", boom)
    assert wikipedia.fetch_extract("Anything") is None


def test_fetch_best_falls_back_to_search(monkeypatch: pytest.MonkeyPatch) -> None:
    def router(url: str, params: dict | None = None, **k: object) -> httpx.Response:
        if params and params.get("action") == "opensearch":
            return httpx.Response(
                200,
                json=["Docker", ["Docker (software)"], [], []],
                request=httpx.Request("GET", wikipedia._ACTION),
            )
        # REST summary: bad title 404s, resolved title returns content
        if url.endswith("Docker"):
            return _rest_response({}, status=404)
        return _rest_response(
            {"type": "standard", "title": "Docker (software)", "extract": "Docker packages apps."}
        )

    monkeypatch.setattr(httpx, "get", router)
    result = wikipedia.fetch_best("Docker")
    assert result is not None
    assert result[0] == "Docker packages apps."


def test_fetch_extracts_batch_maps_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "query": {
            "normalized": [{"from": "docker", "to": "Docker"}],
            "redirects": [{"from": "Docker", "to": "Docker (software)"}],
            "pages": {
                "1": {"title": "Docker (software)", "extract": "Docker packages apps."},
                "2": {"title": "Python (programming language)", "extract": "Python is a language."},
                "3": {"title": "Missing", "missing": ""},
            },
        }
    }
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _rest_response(payload))
    out = wikipedia.fetch_extracts_batch(["docker", "Python (programming language)"])
    # "docker" -> normalized "Docker" -> redirect "Docker (software)"
    assert out["docker"][0] == "Docker packages apps."
    assert out["Python (programming language)"][0] == "Python is a language."


def test_recreate_collection_is_empty() -> None:
    client = QdrantClient(":memory:")
    emb = FakeDenseEmbedder(dim=32)
    store = QdrantVectorStore(client, "test", emb.dim, use_sparse=False)
    store.ensure_collection("kb")
    store.upsert("kb", [str(uuid.uuid4())], ["hello"], emb.embed(["hello"]), None, [{}])
    store.recreate_collection("kb")
    res = store.hybrid_search("kb", emb.embed(["hello"])[0], None, 5)
    assert res == []
