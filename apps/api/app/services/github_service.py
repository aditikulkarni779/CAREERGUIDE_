"""GitHub Intelligence — deterministic scoring + skill extraction into the Twin."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.github import GitHubClient, GitHubError
from app.adapters.models import GithubProfile, Profile, SkillSource
from app.agents.github_agent import GithubAgent
from app.agents.llm.port import LLMClient
from app.services.profile_service import ProfileError, upsert_user_skill
from app.services.skill_service import canonicalize


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _repo_quality(repo: dict[str, Any]) -> int:
    stars = repo.get("stargazers_count", 0) or 0
    q = 0
    if repo.get("description"):
        q += 20
    if repo.get("license"):
        q += 15
    if repo.get("topics"):
        q += 15
    if not repo.get("archived"):
        q += 10
    q += min(40, stars * 4)
    return min(100, q)


def compute_scores(user: dict[str, Any], repos: list[dict[str, Any]]) -> dict[str, Any]:
    own = [r for r in repos if not r.get("fork")]
    top = sorted(own, key=lambda r: r.get("stargazers_count", 0) or 0, reverse=True)[:10]
    repo_score = round(sum(_repo_quality(r) for r in top) / len(top)) if top else 0

    langs: dict[str, int] = {}
    for r in own:
        lang = r.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
    diversity_score = min(100, len(langs) * 20)

    now = datetime.now(timezone.utc)
    pushes = [d for d in (_parse_dt(r.get("pushed_at")) for r in own) if d]
    if pushes:
        days = (now - max(pushes)).days
        recency = 100 if days <= 30 else 70 if days <= 90 else 40 if days <= 365 else 15
    else:
        recency = 0
    repo_count_score = min(100, (user.get("public_repos", 0) or 0) * 8)
    created = _parse_dt(user.get("created_at"))
    age_score = min(100, ((now - created).days / 365) * 20) if created else 0
    health_score = round(0.5 * recency + 0.25 * repo_count_score + 0.25 * age_score)

    pc = 0
    if user.get("bio"):
        pc += 40
    if user.get("name"):
        pc += 20
    pc += min(40, (user.get("followers", 0) or 0) * 2)
    profile_completeness = min(100, pc)

    recruiter_score = round(
        0.35 * repo_score
        + 0.25 * diversity_score
        + 0.25 * health_score
        + 0.15 * profile_completeness
    )

    top_repos = [
        {
            "name": r.get("name"),
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0) or 0,
            "url": r.get("html_url"),
        }
        for r in top[:6]
    ]
    languages = sorted(langs, key=lambda k: langs[k], reverse=True)
    return {
        "repo_score": repo_score,
        "diversity_score": diversity_score,
        "health_score": health_score,
        "recruiter_score": recruiter_score,
        "languages": languages,
        "top_repos": top_repos,
    }


def get_cached(db: Session, profile_id: uuid.UUID) -> GithubProfile | None:
    return db.scalar(
        select(GithubProfile)
        .where(GithubProfile.profile_id == profile_id)
        .order_by(GithubProfile.fetched_at.desc())
    )


def analyze(
    db: Session,
    profile: Profile,
    username: str,
    client: GitHubClient,
    llm: LLMClient | None = None,
) -> GithubProfile:
    user = client.get_user(username)
    if user is None:
        raise GitHubError("GitHub user not found")
    repos = client.get_repos(username)
    scores = compute_scores(user, repos)

    for lang in scores["languages"]:
        skill = canonicalize(db, lang)
        if skill is not None:
            try:
                upsert_user_skill(db, profile.id, skill.name, 55, SkillSource.github)
            except ProfileError:
                pass

    summary = ""
    if llm is not None:
        summary = GithubAgent(llm).summarize(username, scores)

    gp = get_cached(db, profile.id) or GithubProfile(profile_id=profile.id)
    gp.username = username
    gp.name = user.get("name")
    gp.bio = user.get("bio")
    gp.followers = user.get("followers", 0) or 0
    gp.public_repos = user.get("public_repos", 0) or 0
    gp.repo_score = scores["repo_score"]
    gp.diversity_score = scores["diversity_score"]
    gp.health_score = scores["health_score"]
    gp.recruiter_score = scores["recruiter_score"]
    gp.languages = scores["languages"]
    gp.top_repos = scores["top_repos"]
    gp.summary = summary
    gp.fetched_at = datetime.now(timezone.utc)
    if gp.id is None:
        db.add(gp)
    db.commit()
    db.refresh(gp)
    return gp


def get_or_analyze(
    db: Session,
    profile: Profile,
    username: str,
    client: GitHubClient,
    llm: LLMClient | None = None,
    max_age_hours: int = 24,
) -> GithubProfile:
    cached = get_cached(db, profile.id)
    if cached is not None and cached.username == username:
        fetched = cached.fetched_at
        if fetched.tzinfo is None:  # SQLite returns naive datetimes
            fetched = fetched.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - fetched < timedelta(hours=max_age_hours):
            return cached
    return analyze(db, profile, username, client, llm)
