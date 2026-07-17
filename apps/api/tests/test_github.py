from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.adapters.models import Profile, Skill, SkillCategory, User
from app.agents.llm.fake import FakeLLM
from app.services.github_service import analyze, compute_scores, get_or_analyze

RECENT = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

USER = {
    "name": "Jane Dev",
    "bio": "ML engineer who loves open source",
    "followers": 30,
    "public_repos": 12,
    "created_at": "2020-01-01T00:00:00Z",
}
REPOS = [
    {
        "name": "ml-project",
        "language": "Python",
        "stargazers_count": 50,
        "description": "an ml project",
        "license": {"key": "mit"},
        "topics": ["ml"],
        "archived": False,
        "fork": False,
        "pushed_at": RECENT,
        "html_url": "https://github.com/jane/ml-project",
    },
    {
        "name": "web-app",
        "language": "TypeScript",
        "stargazers_count": 10,
        "description": "",
        "fork": False,
        "pushed_at": RECENT,
        "html_url": "https://github.com/jane/web-app",
    },
    {"name": "forked", "language": "Go", "fork": True, "pushed_at": RECENT},  # excluded
    {"name": "scripts", "language": "Shell", "fork": False, "pushed_at": RECENT},
]


class FakeGH:
    def __init__(self) -> None:
        self.calls = 0

    def get_user(self, username: str) -> dict:
        self.calls += 1
        return USER

    def get_repos(self, username: str, limit: int = 100) -> list:
        return REPOS


def test_compute_scores() -> None:
    s = compute_scores(USER, REPOS)
    assert 0 <= s["recruiter_score"] <= 100
    # 3 non-fork languages (Python, TypeScript, Shell) -> 60
    assert s["diversity_score"] == 60
    assert set(s["languages"]) == {"Python", "TypeScript", "Shell"}
    # top repos exclude the fork
    assert all(r["name"] != "forked" for r in s["top_repos"])
    assert s["top_repos"][0]["name"] == "ml-project"  # most stars first


def _profile(db: Session) -> Profile:
    user = User(email="gh@example.com")
    db.add(user)
    db.flush()
    prof = Profile(user_id=user.id)
    db.add(prof)
    db.flush()
    db.add_all([
        Skill(name="Python", slug="python", category=SkillCategory.language, aliases=["py"]),
        Skill(name="TypeScript", slug="typescript", category=SkillCategory.language, aliases=["ts"]),
    ])
    db.commit()
    return prof


def test_analyze_persists_and_maps_skills(db_session: Session) -> None:
    prof = _profile(db_session)
    gp = analyze(db_session, prof, "jane", FakeGH(), FakeLLM(lambda s, m, t: "Solid profile."))
    assert gp.username == "jane"
    assert gp.recruiter_score > 0
    assert gp.summary == "Solid profile."
    assert "Python" in gp.languages

    from app.services.profile_service import list_user_skills

    slugs = {us.skill_id: us for us in list_user_skills(db_session, prof.id)}
    assert len(slugs) == 2  # Python + TypeScript mapped (Shell has no taxonomy skill)


def test_cache_avoids_refetch(db_session: Session) -> None:
    prof = _profile(db_session)
    client = FakeGH()
    get_or_analyze(db_session, prof, "jane", client, FakeLLM())
    get_or_analyze(db_session, prof, "jane", client, FakeLLM())
    assert client.calls == 1  # second call served from cache
