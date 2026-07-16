"""Onboarding — build the Career Twin from the wizard payload."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.models import ReadinessScore, SkillSource
from app.services.profile_service import (
    ProfileError,
    get_or_create_profile,
    update_profile,
    upsert_user_skill,
)
from app.services.readiness_service import compute_readiness


@dataclass
class OnboardingResult:
    profile_id: uuid.UUID
    readiness: ReadinessScore
    added_skills: list[str] = field(default_factory=list)
    skipped_skills: list[str] = field(default_factory=list)


def run_onboarding(
    db: Session,
    user_id: uuid.UUID,
    profile_fields: dict[str, Any],
    skills: list[tuple[str, int]],
) -> OnboardingResult:
    profile = get_or_create_profile(db, user_id)
    if profile_fields:
        profile = update_profile(db, user_id, profile_fields)

    added: list[str] = []
    skipped: list[str] = []
    for name, proficiency in skills:
        try:
            upsert_user_skill(db, profile.id, name, proficiency, SkillSource.manual)
            added.append(name)
        except ProfileError:
            skipped.append(name)

    readiness = compute_readiness(db, profile)
    return OnboardingResult(
        profile_id=profile.id,
        readiness=readiness,
        added_skills=added,
        skipped_skills=skipped,
    )
