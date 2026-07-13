from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health() -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready() -> None:
    r = client.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
