"""Skill-gap analysis + adaptive roadmap endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.models import User
from app.api.deps import get_current_user
from app.schemas import (
    ItemStatusUpdate,
    RoadmapItemOut,
    RoadmapOut,
    RoadmapVersionOut,
    SkillGapOut,
    TargetRoleRequest,
)
from app.services.gap_service import compute_gaps, resolve_role
from app.services.profile_service import get_or_create_profile
from app.services.roadmap_service import (
    generate_roadmap,
    get_items,
    latest_roadmap,
    list_versions,
    update_item_status,
)

router = APIRouter(tags=["roadmap"])


def _resolve_or_400(db: Session, profile_goal: str | None, requested: str | None):  # type: ignore[no-untyped-def]
    role = resolve_role(db, requested or profile_goal)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="unknown target role; set a career goal or pass a known role",
        )
    return role


def _roadmap_out(db: Session, roadmap) -> RoadmapOut:  # type: ignore[no-untyped-def]
    items = [RoadmapItemOut.model_validate(i) for i in get_items(db, roadmap.id)]
    return RoadmapOut(
        id=roadmap.id,
        target_role_slug=roadmap.target_role_slug,
        target_role_name=roadmap.target_role_name,
        version=roadmap.version,
        status=roadmap.status,
        rationale=roadmap.rationale or {},
        items=items,
    )


@router.post("/gap-analysis", response_model=list[SkillGapOut])
def gap_analysis(
    data: TargetRoleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SkillGapOut]:
    profile = get_or_create_profile(db, user.id)
    role = _resolve_or_400(db, profile.career_goal, data.target_role)
    return [
        SkillGapOut(
            skill_slug=g.skill_slug,
            skill_name=g.skill_name,
            importance=g.importance,
            current=g.current,
            target=g.target,
            gap=g.gap,
            difficulty=g.difficulty,
            est_hours=g.est_hours,
            confidence=g.confidence,
            order_index=g.order_index,
            explanation=g.explanation,
        )
        for g in compute_gaps(db, profile, role)
    ]


@router.post("/roadmap/generate", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED)
def roadmap_generate(
    data: TargetRoleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    profile = get_or_create_profile(db, user.id)
    role = _resolve_or_400(db, profile.career_goal, data.target_role)
    roadmap = generate_roadmap(db, profile, role)
    return _roadmap_out(db, roadmap)


@router.get("/roadmap", response_model=RoadmapOut)
def roadmap_get(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> RoadmapOut:
    profile = get_or_create_profile(db, user.id)
    roadmap = latest_roadmap(db, profile.id)
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no roadmap yet")
    return _roadmap_out(db, roadmap)


@router.get("/roadmap/versions", response_model=list[RoadmapVersionOut])
def roadmap_versions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RoadmapVersionOut]:
    profile = get_or_create_profile(db, user.id)
    return [RoadmapVersionOut.model_validate(r) for r in list_versions(db, profile.id)]


@router.patch("/roadmap/items/{item_id}", response_model=RoadmapItemOut)
def roadmap_item_patch(
    item_id: uuid.UUID,
    data: ItemStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapItemOut:
    profile = get_or_create_profile(db, user.id)
    item = update_item_status(db, profile.id, item_id, data.status)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")
    return RoadmapItemOut.model_validate(item)
