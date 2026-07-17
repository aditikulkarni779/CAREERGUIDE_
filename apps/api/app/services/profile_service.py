"""Profile (Career Twin) use-cases."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import Profile, SkillSource, UserSkill
from app.services.skill_service import canonicalize


class ProfileError(Exception):
    """Domain error mapped to HTTP by the router."""


def get_or_create_profile(db: Session, user_id: uuid.UUID) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, user_id: uuid.UUID, fields: dict[str, Any]) -> Profile:
    profile = get_or_create_profile(db, user_id)
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    profile.twin_version += 1
    db.commit()
    db.refresh(profile)
    return profile


def list_user_skills(db: Session, profile_id: uuid.UUID) -> list[UserSkill]:
    return list(db.scalars(select(UserSkill).where(UserSkill.profile_id == profile_id)))


def upsert_user_skill(
    db: Session,
    profile_id: uuid.UUID,
    skill_name: str,
    proficiency: int,
    source: SkillSource,
) -> UserSkill:
    skill = canonicalize(db, skill_name)
    if skill is None:
        raise ProfileError(f"unknown skill: {skill_name!r}")
    # Skill changes alter the Career Twin -> bump version so roadmaps re-generate.
    twin = db.get(Profile, profile_id)
    if twin is not None:
        twin.twin_version += 1
    existing = db.scalar(
        select(UserSkill).where(
            UserSkill.profile_id == profile_id, UserSkill.skill_id == skill.id
        )
    )
    if existing:
        existing.proficiency = proficiency
        existing.source = source
        existing.last_seen_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    us = UserSkill(
        profile_id=profile_id,
        skill_id=skill.id,
        proficiency=proficiency,
        source=source,
    )
    db.add(us)
    db.commit()
    db.refresh(us)
    return us
