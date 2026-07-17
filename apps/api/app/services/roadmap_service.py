"""Adaptive Roadmap generation — sequence skill gaps into milestones."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.models import Profile, Roadmap, RoadmapItem, RoadmapItemStatus, Role
from app.services.gap_service import SkillGap, compute_gaps


def _next_version(db: Session, profile_id: uuid.UUID) -> int:
    current = db.scalar(
        select(func.max(Roadmap.version)).where(Roadmap.profile_id == profile_id)
    )
    return (current or 0) + 1


def generate_roadmap(db: Session, profile: Profile, role: Role) -> Roadmap:
    gaps: list[SkillGap] = compute_gaps(db, profile, role)
    weekly_hours = profile.weekly_hours or 8
    milestone_capacity = max(weekly_hours * 3, 10)  # ~3 weeks of study per milestone

    roadmap = Roadmap(
        profile_id=profile.id,
        target_role_slug=role.slug,
        target_role_name=role.name,
        version=_next_version(db, profile.id),
        status="active",
        rationale={
            "generated_from": "skill_gap",
            "num_items": len(gaps),
            "total_hours": sum(g.est_hours for g in gaps),
            "weekly_hours": weekly_hours,
            "twin_version": profile.twin_version,
        },
    )
    db.add(roadmap)
    db.flush()

    milestone = 1
    running = 0
    for g in gaps:
        if running + g.est_hours > milestone_capacity and running > 0:
            milestone += 1
            running = 0
        running += g.est_hours
        db.add(
            RoadmapItem(
                roadmap_id=roadmap.id,
                skill_id=g.skill_id,
                skill_name=g.skill_name,
                order_index=g.order_index,
                milestone=milestone,
                est_hours=g.est_hours,
                difficulty=g.difficulty,
                importance=g.importance,
                status=RoadmapItemStatus.todo,
                explanation=g.explanation,
                resources=[],
            )
        )
    db.commit()
    db.refresh(roadmap)
    return roadmap


def get_or_generate_roadmap(db: Session, profile: Profile, role: Role) -> Roadmap:
    """Reuse the latest roadmap if it's for the same role and the Twin is unchanged;
    otherwise generate a new version. Prevents version spam on repeated chats."""
    latest = latest_roadmap(db, profile.id)
    if (
        latest is not None
        and latest.target_role_slug == role.slug
        and (latest.rationale or {}).get("twin_version") == profile.twin_version
    ):
        return latest
    return generate_roadmap(db, profile, role)


def latest_roadmap(db: Session, profile_id: uuid.UUID) -> Roadmap | None:
    return db.scalar(
        select(Roadmap)
        .where(Roadmap.profile_id == profile_id)
        .order_by(Roadmap.version.desc())
    )


def list_versions(db: Session, profile_id: uuid.UUID) -> list[Roadmap]:
    return list(
        db.scalars(
            select(Roadmap)
            .where(Roadmap.profile_id == profile_id)
            .order_by(Roadmap.version.desc())
        )
    )


def get_items(db: Session, roadmap_id: uuid.UUID) -> list[RoadmapItem]:
    return list(
        db.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.roadmap_id == roadmap_id)
            .order_by(RoadmapItem.order_index.asc())
        )
    )


def update_item_status(
    db: Session, profile_id: uuid.UUID, item_id: uuid.UUID, status: RoadmapItemStatus
) -> RoadmapItem | None:
    item = db.get(RoadmapItem, item_id)
    if item is None:
        return None
    roadmap = db.get(Roadmap, item.roadmap_id)
    if roadmap is None or roadmap.profile_id != profile_id:
        return None  # ownership check
    item.status = status
    db.commit()
    db.refresh(item)
    return item
