from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.models import Role, RoleSkillRequirement, Skill, SkillCategory

CREDS = {"email": "onb@example.com", "password": "supersecret123"}


def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=CREDS)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed_ml_role(db: Session) -> None:
    py = Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"])
    ml = Skill(name="Machine Learning", slug="machine-learning", category=SkillCategory.ai)
    role = Role(name="ML Engineer", slug="ml-engineer")
    db.add_all([py, ml, role])
    db.flush()
    db.add_all([
        RoleSkillRequirement(
            role_id=role.id, skill_id=py.id, importance=90, typical_proficiency=80, difficulty=40
        ),
        RoleSkillRequirement(
            role_id=role.id, skill_id=ml.id, importance=90, typical_proficiency=80, difficulty=70
        ),
    ])
    db.commit()


def test_onboarding_builds_twin_and_readiness(client: TestClient, db_session: Session) -> None:
    _seed_ml_role(db_session)
    h = _auth(client)
    r = client.post(
        "/api/v1/profile/onboarding",
        headers=h,
        json={
            "career_goal": "ML Engineer",
            "weekly_hours": 10,
            "skills": [{"name": "python", "proficiency": 80}],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "python" in body["added_skills"]
    assert body["readiness"]["target_role_slug"] == "ml-engineer"
    # python fully covered (80/80), ML missing -> ~50 with equal importance
    assert 40 <= body["readiness"]["overall"] <= 60
    assert body["readiness"]["components"]["skills"] == body["readiness"]["overall"]


def test_onboarding_skips_unknown_skills(client: TestClient, db_session: Session) -> None:
    _seed_ml_role(db_session)
    h = _auth(client)
    r = client.post(
        "/api/v1/profile/onboarding",
        headers=h,
        json={"career_goal": "ML Engineer", "skills": [{"name": "Cobol", "proficiency": 90}]},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["skipped_skills"] == ["Cobol"]
    assert body["added_skills"] == []


def test_onboarding_persists_profile_fields(client: TestClient, db_session: Session) -> None:
    _seed_ml_role(db_session)
    h = _auth(client)
    client.post(
        "/api/v1/profile/onboarding",
        headers=h,
        json={"career_goal": "ML Engineer", "weekly_hours": 15, "interests": ["ai", "nlp"]},
    )
    prof = client.get("/api/v1/profile", headers=h).json()
    assert prof["weekly_hours"] == 15
    assert prof["interests"] == ["ai", "nlp"]
    assert prof["career_goal"] == "ML Engineer"


def test_readiness_endpoint_full_coverage(client: TestClient, db_session: Session) -> None:
    _seed_ml_role(db_session)
    h = _auth(client)
    client.post(
        "/api/v1/profile/onboarding",
        headers=h,
        json={
            "career_goal": "ML Engineer",
            "skills": [
                {"name": "python", "proficiency": 80},
                {"name": "machine-learning", "proficiency": 80},
            ],
        },
    )
    r = client.get("/api/v1/profile/readiness", headers=h)
    assert r.status_code == 200
    assert r.json()["overall"] == 100


def test_readiness_no_goal_uses_average(client: TestClient, db_session: Session) -> None:
    db_session.add(
        Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"])
    )
    db_session.commit()
    h = _auth(client)
    client.post(
        "/api/v1/profile/onboarding",
        headers=h,
        json={"skills": [{"name": "python", "proficiency": 60}]},
    )
    r = client.get("/api/v1/profile/readiness", headers=h)
    assert r.status_code == 200
    assert r.json()["overall"] == 60
    assert r.json()["target_role_slug"] is None
