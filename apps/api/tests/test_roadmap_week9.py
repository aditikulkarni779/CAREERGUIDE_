from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.models import (
    Profile,
    Role,
    RoleSkillRequirement,
    Skill,
    SkillCategory,
    User,
    UserSkill,
)
from app.services.gap_service import compute_gaps, resolve_role
from app.services.roadmap_service import generate_roadmap, get_items, get_or_generate_roadmap

CREDS = {"email": "rm9@example.com", "password": "supersecret123"}


def _seed_role(db: Session) -> dict[str, Skill]:
    py = Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"])
    ml = Skill(name="Machine Learning", slug="machine-learning", category=SkillCategory.ai)
    dk = Skill(name="Docker", slug="docker", category=SkillCategory.tool)
    role = Role(name="ML Engineer", slug="ml-engineer")
    db.add_all([py, ml, dk, role])
    db.flush()
    db.add_all([
        RoleSkillRequirement(role_id=role.id, skill_id=py.id, importance=90, typical_proficiency=80, difficulty=40),
        RoleSkillRequirement(role_id=role.id, skill_id=ml.id, importance=90, typical_proficiency=80, difficulty=70),
        RoleSkillRequirement(role_id=role.id, skill_id=dk.id, importance=60, typical_proficiency=60, difficulty=45),
    ])
    db.commit()
    return {"python": py, "ml": ml, "docker": dk, "role": role}  # type: ignore[dict-item]


def _profile_with(db: Session, skills: dict[str, Skill], py_prof: int) -> Profile:
    user = User(email="x@example.com")
    db.add(user)
    db.flush()
    prof = Profile(user_id=user.id, career_goal="ML Engineer", weekly_hours=8)
    db.add(prof)
    db.flush()
    db.add(UserSkill(profile_id=prof.id, skill_id=skills["python"].id, proficiency=py_prof))
    db.commit()
    return prof


# ---- Gap math ----
def test_compute_gaps_scoring_and_order(db_session: Session) -> None:
    skills = _seed_role(db_session)
    prof = _profile_with(db_session, skills, py_prof=50)
    role = resolve_role(db_session, "ml-engineer")
    assert role is not None

    gaps = compute_gaps(db_session, prof, role)
    # python 50<80 gap, ml 0<80 gap, docker 0<60 gap -> 3 gaps
    assert len(gaps) == 3
    # sorted by importance desc then difficulty asc: python(90,40) before ml(90,70) before docker(60)
    assert [g.skill_slug for g in gaps] == ["python", "machine-learning", "docker"]
    py_gap = gaps[0]
    assert py_gap.current == 50 and py_gap.target == 80 and py_gap.gap == 30
    assert py_gap.est_hours > 0
    assert "why" in py_gap.explanation


def test_covered_skill_not_a_gap(db_session: Session) -> None:
    skills = _seed_role(db_session)
    prof = _profile_with(db_session, skills, py_prof=90)  # >= target 80
    role = resolve_role(db_session, "ml-engineer")
    assert role is not None
    gaps = compute_gaps(db_session, prof, role)
    assert "python" not in [g.skill_slug for g in gaps]


# ---- Roadmap generation + versioning ----
def test_generate_roadmap_milestones_and_versions(db_session: Session) -> None:
    skills = _seed_role(db_session)
    prof = _profile_with(db_session, skills, py_prof=50)
    role = resolve_role(db_session, "ml-engineer")
    assert role is not None

    rm1 = generate_roadmap(db_session, prof, role)
    items = get_items(db_session, rm1.id)
    assert len(items) == 3
    assert items[0].skill_name == "Python"
    assert [i.milestone for i in items] == sorted(i.milestone for i in items)  # non-decreasing
    assert rm1.version == 1
    assert rm1.rationale["num_items"] == 3

    rm2 = generate_roadmap(db_session, prof, role)
    assert rm2.version == 2


def test_get_or_generate_dedupes_until_twin_changes(db_session: Session) -> None:
    skills = _seed_role(db_session)
    prof = _profile_with(db_session, skills, py_prof=50)
    role = resolve_role(db_session, "ml-engineer")
    assert role is not None

    r1 = get_or_generate_roadmap(db_session, prof, role)
    r2 = get_or_generate_roadmap(db_session, prof, role)  # same twin -> reuse
    assert r1.id == r2.id
    assert r2.version == 1

    prof.twin_version += 1  # Twin changed
    db_session.commit()
    r3 = get_or_generate_roadmap(db_session, prof, role)
    assert r3.version == 2


# ---- Endpoints ----
def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=CREDS)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_gap_and_roadmap_endpoints(client: TestClient, db_session: Session) -> None:
    _seed_role(db_session)
    h = _auth(client)
    client.put("/api/v1/profile", headers=h, json={"career_goal": "ML Engineer", "weekly_hours": 8})
    client.post("/api/v1/profile/skills", headers=h, json={"skill_name": "python", "proficiency": 50})

    gaps = client.post("/api/v1/gap-analysis", headers=h, json={}).json()
    assert len(gaps) == 3
    assert gaps[0]["skill_slug"] == "python"

    rm = client.post("/api/v1/roadmap/generate", headers=h, json={})
    assert rm.status_code == 201
    body = rm.json()
    assert body["target_role_slug"] == "ml-engineer"
    assert len(body["items"]) == 3

    got = client.get("/api/v1/roadmap", headers=h).json()
    assert got["version"] == 1

    item_id = body["items"][0]["id"]
    patched = client.patch(f"/api/v1/roadmap/items/{item_id}", headers=h, json={"status": "done"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "done"


def test_gap_analysis_unknown_role_422(client: TestClient, db_session: Session) -> None:
    h = _auth(client)  # no career goal, no role passed
    r = client.post("/api/v1/gap-analysis", headers=h, json={})
    assert r.status_code == 422
