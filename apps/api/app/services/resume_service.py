"""Resume Intelligence — skill extraction, ATS scoring, persistence."""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import (
    Profile,
    Resume,
    ResumeScore,
    Role,
    RoleSkillRequirement,
    Skill,
    SkillSource,
)
from app.services.profile_service import upsert_user_skill

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")

_SECTION_HINTS = {
    "contact": None,  # detected via email/phone
    "summary": ("summary", "objective", "profile"),
    "experience": ("experience", "employment", "work history"),
    "education": ("education", "academic"),
    "skills": ("skills", "technologies", "technical"),
    "projects": ("project",),
}


def _word_present(text_lower: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term.lower())}\b", text_lower) is not None


def extract_skills(db: Session, text: str) -> list[Skill]:
    text_lower = text.lower()
    matched: list[Skill] = []
    for skill in db.scalars(select(Skill)):
        names = [skill.name, *(skill.aliases or [])]
        if any(_word_present(text_lower, n) for n in names if len(n) > 1):
            matched.append(skill)
    return matched


def detect_sections(text: str) -> dict[str, bool]:
    tl = text.lower()
    out: dict[str, bool] = {}
    for section, hints in _SECTION_HINTS.items():
        if section == "contact":
            out[section] = bool(_EMAIL.search(text) or _PHONE.search(text))
        else:
            assert hints is not None
            out[section] = any(_word_present(tl, h) for h in hints)
    return out


def _format_score(word_count: int, bullet_count: int) -> float:
    if word_count < 150:
        length = 40.0
    elif word_count > 1200:
        length = 70.0
    else:
        length = 100.0
    bullets = min(bullet_count, 10) / 10 * 100
    return 0.6 * length + 0.4 * bullets


def score_resume(
    db: Session, text: str, role: Role | None
) -> tuple[int, dict[str, bool], list[str]]:
    sections = detect_sections(text)
    sec_score = sum(sections.values()) / len(sections) * 100

    missing: list[str] = []
    keyword_cov = 100.0
    if role is not None:
        tl = text.lower()
        reqs = list(
            db.scalars(select(RoleSkillRequirement).where(RoleSkillRequirement.role_id == role.id))
        )
        present = 0
        for req in reqs:
            skill = db.get(Skill, req.skill_id)
            if skill is None:
                continue
            names = [skill.name, *(skill.aliases or [])]
            if any(_word_present(tl, n) for n in names if len(n) > 1):
                present += 1
            else:
                missing.append(skill.name)
        keyword_cov = (present / len(reqs) * 100) if reqs else 100.0

    words = len(text.split())
    bullets = text.count("•") + len(re.findall(r"(?m)^\s*[-*]\s+", text))
    fmt = _format_score(words, bullets)

    ats = round(0.4 * sec_score + 0.35 * keyword_cov + 0.25 * fmt)
    return ats, sections, missing


def process_resume(
    db: Session,
    profile: Profile,
    filename: str,
    text: str,
    file_key: str,
    role: Role | None,
) -> tuple[Resume, ResumeScore, list[str]]:
    resume = Resume(profile_id=profile.id, filename=filename, file_key=file_key, text=text)
    db.add(resume)
    db.flush()

    detected = extract_skills(db, text)
    added: list[str] = []
    for skill in detected:
        upsert_user_skill(db, profile.id, skill.name, 60, SkillSource.resume)
        added.append(skill.name)

    ats, sections, missing = score_resume(db, text, role)
    score = ResumeScore(
        resume_id=resume.id,
        ats_score=ats,
        sections=sections,
        missing_keywords=missing,
        detected_skills=added,
        suggestions={},
    )
    db.add(score)
    db.commit()
    db.refresh(resume)
    db.refresh(score)
    return resume, score, added


def get_resume(db: Session, profile_id: uuid.UUID, resume_id: uuid.UUID) -> Resume | None:
    return db.scalar(
        select(Resume).where(Resume.id == resume_id, Resume.profile_id == profile_id)
    )


def latest_score(db: Session, resume_id: uuid.UUID) -> ResumeScore | None:
    return db.scalar(
        select(ResumeScore)
        .where(ResumeScore.resume_id == resume_id)
        .order_by(ResumeScore.created_at.desc())
    )
