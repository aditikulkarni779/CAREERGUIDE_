"""Career Readiness Score.

v1 is skills-only: coverage of a target role's skill requirements, weighted by
importance. Resume / GitHub / interview / market components are placeholders now
and get filled in later phases (the overall stays skills-only until then).
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import (
    Profile,
    ReadinessScore,
    Role,
    RoleSkillRequirement,
    UserSkill,
)
from app.services.skill_service import normalize_slug

COMPONENT_KEYS = ("skills", "resume", "github", "projects", "learning", "interview", "market")


def resolve_role(db: Session, career_goal: str | None) -> Role | None:
    if not career_goal:
        return None
    return db.scalar(select(Role).where(Role.slug == normalize_slug(career_goal)))


def _skills_component(
    db: Session, profile_id: uuid.UUID, role: Role | None
) -> tuple[int, list[str]]:
    """Return (skills_score 0-100, missing_skill_slugs)."""
    user_prof: dict[uuid.UUID, int] = {
        us.skill_id: us.proficiency
        for us in db.scalars(select(UserSkill).where(UserSkill.profile_id == profile_id))
    }
    if role is None:
        if not user_prof:
            return 0, []
        return round(sum(user_prof.values()) / len(user_prof)), []

    reqs = list(
        db.scalars(select(RoleSkillRequirement).where(RoleSkillRequirement.role_id == role.id))
    )
    if not reqs:
        return 0, []
    num = den = 0.0
    missing: list[str] = []
    for req in reqs:
        typical = req.typical_proficiency or 60
        prof = user_prof.get(req.skill_id, 0)
        coverage = min(prof / typical, 1.0) if typical else 0.0
        num += req.importance * coverage
        den += req.importance
        if prof == 0:
            missing.append(str(req.skill_id))
    score = round(num / den * 100) if den else 0
    return score, missing


def compute_readiness(db: Session, profile: Profile) -> ReadinessScore:
    role = resolve_role(db, profile.career_goal)
    skills_score, missing = _skills_component(db, profile.id, role)

    components: dict[str, object] = {k: None for k in COMPONENT_KEYS}
    components["skills"] = skills_score
    components["missing_skill_count"] = len(missing)

    # v1: overall == skills component. Weighting broadens as components land.
    overall = skills_score

    score = ReadinessScore(
        profile_id=profile.id,
        overall=overall,
        components=components,
        target_role_slug=role.slug if role else None,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def latest_readiness(db: Session, profile: Profile) -> ReadinessScore:
    existing = db.scalar(
        select(ReadinessScore)
        .where(ReadinessScore.profile_id == profile.id)
        .order_by(ReadinessScore.computed_at.desc())
    )
    return existing or compute_readiness(db, profile)
