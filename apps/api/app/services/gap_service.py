"""Skill Gap analysis — user's Career Twin vs a target role's requirements."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import Profile, Role, RoleSkillRequirement, Skill, UserSkill
from app.services.skill_service import normalize_slug


@dataclass
class SkillGap:
    skill_id: uuid.UUID
    skill_slug: str
    skill_name: str
    importance: int
    current: int
    target: int
    gap: int
    difficulty: int
    est_hours: int
    confidence: float
    order_index: int = 0
    explanation: dict[str, Any] = field(default_factory=dict)


def resolve_role(db: Session, target_role: str | None) -> Role | None:
    if not target_role:
        return None
    return db.scalar(select(Role).where(Role.slug == normalize_slug(target_role)))


def _estimate_hours(gap: int, difficulty: int) -> int:
    # Full 0->100 gap at avg difficulty ≈ 40h; scales with gap and difficulty.
    hours = (gap / 100) * 40 * (0.5 + difficulty / 100)
    return max(2, round(hours))


def compute_gaps(db: Session, profile: Profile, role: Role) -> list[SkillGap]:
    user_prof: dict[uuid.UUID, int] = {
        us.skill_id: us.proficiency
        for us in db.scalars(select(UserSkill).where(UserSkill.profile_id == profile.id))
    }
    reqs = list(
        db.scalars(select(RoleSkillRequirement).where(RoleSkillRequirement.role_id == role.id))
    )

    gaps: list[SkillGap] = []
    for req in reqs:
        target = req.typical_proficiency or 60
        current = user_prof.get(req.skill_id, 0)
        if current >= target:
            continue  # already covered
        skill = db.get(Skill, req.skill_id)
        if skill is None:
            continue
        gap = target - current
        est = _estimate_hours(gap, req.difficulty)
        confidence = 0.9 if req.skill_id in user_prof else 0.7
        gaps.append(
            SkillGap(
                skill_id=skill.id,
                skill_slug=skill.slug,
                skill_name=skill.name,
                importance=req.importance,
                current=current,
                target=target,
                gap=gap,
                difficulty=req.difficulty,
                est_hours=est,
                confidence=confidence,
                explanation={
                    "why": f"{skill.name} is required for {role.name} "
                    f"(importance {req.importance}/100).",
                    "addresses": skill.name,
                    "impact": f"Raises your {skill.name} from {current} toward {target}, "
                    f"closing a {gap}-point gap.",
                    "confidence": confidence,
                },
            )
        )

    # Foundational-first: most important, then easiest within importance band.
    gaps.sort(key=lambda g: (-g.importance, g.difficulty))
    for i, g in enumerate(gaps):
        g.order_index = i
    return gaps
