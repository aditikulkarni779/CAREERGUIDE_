"""Profile (Career Twin) endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.models import Skill, User
from app.api.deps import get_current_user
from app.schemas import ProfileOut, ProfileUpdate, UserSkillCreate, UserSkillOut
from app.services.profile_service import (
    ProfileError,
    get_or_create_profile,
    list_user_skills,
    update_profile,
    upsert_user_skill,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProfileOut:
    return ProfileOut.model_validate(get_or_create_profile(db, user.id))


@router.put("", response_model=ProfileOut)
def put_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = update_profile(db, user.id, data.model_dump(exclude_unset=True))
    return ProfileOut.model_validate(profile)


@router.get("/skills", response_model=list[UserSkillOut])
def get_skills(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UserSkillOut]:
    profile = get_or_create_profile(db, user.id)
    out: list[UserSkillOut] = []
    for us in list_user_skills(db, profile.id):
        skill = db.get(Skill, us.skill_id)
        if skill is None:
            continue
        out.append(
            UserSkillOut(
                skill_id=skill.id,
                name=skill.name,
                slug=skill.slug,
                category=skill.category,
                proficiency=us.proficiency,
                source=us.source,
            )
        )
    return out


@router.post("/skills", response_model=UserSkillOut, status_code=status.HTTP_201_CREATED)
def add_skill(
    data: UserSkillCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSkillOut:
    profile = get_or_create_profile(db, user.id)
    try:
        us = upsert_user_skill(db, profile.id, data.skill_name, data.proficiency, data.source)
    except ProfileError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    skill = db.get(Skill, us.skill_id)
    assert skill is not None
    return UserSkillOut(
        skill_id=skill.id,
        name=skill.name,
        slug=skill.slug,
        category=skill.category,
        proficiency=us.proficiency,
        source=us.source,
    )
