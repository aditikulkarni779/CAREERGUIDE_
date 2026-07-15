from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.models import Skill, SkillCategory

CREDS = {"email": "prof@example.com", "password": "supersecret123"}


def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=CREDS)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_python(db: Session) -> None:
    db.add(Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"]))
    db.commit()


def test_get_profile_autocreates(client: TestClient) -> None:
    r = client.get("/api/v1/profile", headers=_auth(client))
    assert r.status_code == 200
    body = r.json()
    assert body["twin_version"] == 1
    assert body["user_id"]


def test_update_profile_bumps_twin_version(client: TestClient) -> None:
    h = _auth(client)
    r = client.put(
        "/api/v1/profile",
        headers=h,
        json={"weekly_hours": 10, "career_goal": "ML Engineer", "interests": ["ai"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["weekly_hours"] == 10
    assert body["career_goal"] == "ML Engineer"
    assert body["interests"] == ["ai"]
    assert body["twin_version"] == 2


def test_add_skill_by_alias_and_list(client: TestClient, db_session: Session) -> None:
    _seed_python(db_session)
    h = _auth(client)
    r = client.post(
        "/api/v1/profile/skills",
        headers=h,
        json={"skill_name": "py", "proficiency": 60},  # alias of Python
    )
    assert r.status_code == 201, r.text
    assert r.json()["slug"] == "python"
    assert r.json()["proficiency"] == 60

    lst = client.get("/api/v1/profile/skills", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["slug"] == "python"


def test_add_skill_upsert_updates_proficiency(client: TestClient, db_session: Session) -> None:
    _seed_python(db_session)
    h = _auth(client)
    client.post("/api/v1/profile/skills", headers=h, json={"skill_name": "python", "proficiency": 30})
    client.post("/api/v1/profile/skills", headers=h, json={"skill_name": "python", "proficiency": 80})
    lst = client.get("/api/v1/profile/skills", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["proficiency"] == 80


def test_add_unknown_skill_422(client: TestClient) -> None:
    r = client.post(
        "/api/v1/profile/skills",
        headers=_auth(client),
        json={"skill_name": "Cobol", "proficiency": 50},
    )
    assert r.status_code == 422


def test_profile_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/profile").status_code == 401
