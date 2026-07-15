from fastapi.testclient import TestClient

CREDS = {"email": "alice@example.com", "password": "supersecret123"}


def _register(client: TestClient) -> None:
    r = client.post("/api/v1/auth/register", json=CREDS)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == CREDS["email"]
    assert body["role"] == "user"
    assert "id" in body


def test_register_and_login(client: TestClient) -> None:
    _register(client)
    r = client.post("/api/v1/auth/login", json=CREDS)
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"] and tokens["refresh_token"]


def test_register_duplicate_conflict(client: TestClient) -> None:
    _register(client)
    r = client.post("/api/v1/auth/register", json=CREDS)
    assert r.status_code == 409


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    r = client.post("/api/v1/auth/login", json={**CREDS, "password": "wrongpass1"})
    assert r.status_code == 401


def test_me_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401  # no bearer credentials


def test_me_with_token(client: TestClient) -> None:
    _register(client)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == CREDS["email"]


def test_refresh_flow(client: TestClient) -> None:
    _register(client)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_access_token_rejected_as_refresh(client: TestClient) -> None:
    _register(client)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_validation_error_is_problem_json(client: TestClient) -> None:
    r = client.post("/api/v1/auth/register", json={"email": "bad", "password": "x"})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
