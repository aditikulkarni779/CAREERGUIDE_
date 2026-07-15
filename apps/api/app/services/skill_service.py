"""Skill canonicalization.

Week 3: normalized string + alias matching. Embedding-based fuzzy matching is
added in Phase 2 (RAG) behind the same `canonicalize` entrypoint.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import Skill


def normalize_slug(name: str) -> str:
    """Lowercase, trim, collapse non-alphanumerics to single hyphens."""
    s = name.strip().lower()
    s = re.sub(r"[+#.]", lambda m: {"+": "p", "#": "sharp", ".": ""}[m.group()], s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def canonicalize(db: Session, name: str) -> Skill | None:
    """Map a free-text skill name to a canonical Skill, or None if unknown."""
    slug = normalize_slug(name)
    if not slug:
        return None
    skill = db.scalar(select(Skill).where(Skill.slug == slug))
    if skill:
        return skill
    # alias fallback: scan skills whose aliases contain the normalized form
    for candidate in db.scalars(select(Skill)):
        for alias in candidate.aliases or []:
            if normalize_slug(alias) == slug:
                return candidate
    return None
