from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.models import (
    Role,
    RoleSkillRequirement,
    Skill,
    SkillCategory,
)
from app.agents.llm.fake import FakeLLM
from app.agents.resume_agent import ResumeAgent
from app.services.gap_service import resolve_role
from app.services.resume_service import extract_skills, score_resume

CREDS = {"email": "res@example.com", "password": "supersecret123"}

RESUME = """John Doe
john@example.com | 555-123-4567
Summary: Backend software engineer.
Experience: Built REST APIs with Python and SQL. Deployed with Docker.
Education: BS Computer Science.
Skills: Python, SQL, Docker
"""


def _seed(db: Session) -> None:
    py = Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"])
    sql = Skill(name="SQL", slug="sql", category=SkillCategory.language)
    dk = Skill(name="Docker", slug="docker", category=SkillCategory.tool)
    ml = Skill(name="Machine Learning", slug="machine-learning", category=SkillCategory.ai, aliases=["ml"])
    role = Role(name="ML Engineer", slug="ml-engineer")
    db.add_all([py, sql, dk, ml, role])
    db.flush()
    db.add_all([
        RoleSkillRequirement(role_id=role.id, skill_id=py.id, importance=90, typical_proficiency=80, difficulty=40),
        RoleSkillRequirement(role_id=role.id, skill_id=ml.id, importance=90, typical_proficiency=80, difficulty=70),
    ])
    db.commit()


def test_extract_skills(db_session: Session) -> None:
    _seed(db_session)
    found = {s.slug for s in extract_skills(db_session, RESUME)}
    assert {"python", "sql", "docker"} <= found
    assert "machine-learning" not in found  # not mentioned


def test_score_resume_sections_and_missing(db_session: Session) -> None:
    _seed(db_session)
    role = resolve_role(db_session, "ml-engineer")
    ats, sections, missing = score_resume(db_session, RESUME, role)
    assert 0 <= ats <= 100
    assert sections["contact"] and sections["experience"] and sections["education"]
    assert not sections["projects"]
    assert "Machine Learning" in missing  # role needs ML, resume lacks it


def test_resume_agent_suggest(db_session: Session) -> None:
    def handler(system: str, messages: list, tier: str) -> str:
        return '{"improved_bullets": ["Built scalable APIs serving 1M requests/day"], "keyword_suggestions": ["pytorch"], "summary_feedback": "Add metrics."}'

    agent = ResumeAgent(FakeLLM(handler))
    out = agent.suggest(RESUME, "ML Engineer", ["Machine Learning"])
    assert out["improved_bullets"]
    assert out["keyword_suggestions"] == ["pytorch"]
    assert "metrics" in out["summary_feedback"].lower()


def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=CREDS)
    tokens = client.post("/api/v1/auth/login", json=CREDS).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_upload_score_and_detail(client: TestClient, db_session: Session) -> None:
    _seed(db_session)
    h = _auth(client)
    client.put("/api/v1/profile", headers=h, json={"career_goal": "ML Engineer"})

    r = client.post(
        "/api/v1/resume",
        headers=h,
        files={"file": ("resume.txt", RESUME.encode(), "text/plain")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ats_score"] > 0
    assert "Python" in body["detected_skills"]
    assert "Machine Learning" in body["missing_keywords"]

    rid = body["resume_id"]
    detail = client.get(f"/api/v1/resume/{rid}", headers=h).json()
    assert detail["filename"] == "resume.txt"
    assert detail["score"]["ats_score"] == body["ats_score"]

    # resume skills flowed into the Twin
    skills = client.get("/api/v1/profile/skills", headers=h).json()
    assert any(s["slug"] == "python" and s["source"] == "resume" for s in skills)


def test_upload_unsupported_type_422(client: TestClient) -> None:
    h = _auth(client)
    r = client.post(
        "/api/v1/resume",
        headers=h,
        files={"file": ("photo.png", b"\x89PNG", "image/png")},
    )
    assert r.status_code == 422
