"""Resume Intelligence endpoints — upload, parse, score, rewrite."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.models import User
from app.adapters.storage import get_object_store
from app.agents.llm.factory import get_llm
from app.agents.resume_agent import ResumeAgent
from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.schemas import (
    ResumeDetailOut,
    ResumeRewriteOut,
    ResumeScoreOut,
    ResumeUploadOut,
)
from app.services.gap_service import resolve_role
from app.services.profile_service import get_or_create_profile
from app.services.resume_parser import ResumeParseError, parse_resume
from app.services.resume_service import (
    get_resume,
    latest_score,
    process_resume,
)

router = APIRouter(prefix="/resume", tags=["resume"])

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("", response_model=ResumeUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeUploadOut:
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="file too large (max 5 MB)")
    filename = file.filename or "resume"
    try:
        text = parse_resume(filename, data)
    except ResumeParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if not text.strip():
        raise HTTPException(status_code=422, detail="no extractable text in file")

    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "bin"
    file_key = f"resumes/{uuid.uuid4()}.{ext}"
    try:
        get_object_store().put(file_key, data, file.content_type or "application/octet-stream")
    except Exception as e:  # noqa: BLE001 — storage is best-effort; text already parsed
        get_logger().warning("resume.storage_failed", error=str(e)[:120])

    profile = get_or_create_profile(db, user.id)
    role = resolve_role(db, profile.career_goal)
    resume, score, added = process_resume(db, profile, filename, text, file_key, role)
    return ResumeUploadOut(
        resume_id=resume.id,
        filename=resume.filename,
        ats_score=score.ats_score,
        detected_skills=added,
        missing_keywords=score.missing_keywords or [],
    )


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def resume_detail(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeDetailOut:
    profile = get_or_create_profile(db, user.id)
    resume = get_resume(db, profile.id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    score = latest_score(db, resume.id)
    return ResumeDetailOut(
        id=resume.id,
        filename=resume.filename,
        text_excerpt=resume.text[:600],
        score=ResumeScoreOut.model_validate(score) if score else None,
    )


@router.get("/{resume_id}/score", response_model=ResumeScoreOut)
def resume_score(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeScoreOut:
    profile = get_or_create_profile(db, user.id)
    resume = get_resume(db, profile.id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    score = latest_score(db, resume.id)
    if score is None:
        raise HTTPException(status_code=404, detail="no score for resume")
    return ResumeScoreOut.model_validate(score)


@router.post("/{resume_id}/rewrite", response_model=ResumeRewriteOut)
def resume_rewrite(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeRewriteOut:
    profile = get_or_create_profile(db, user.id)
    resume = get_resume(db, profile.id, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="resume not found")
    score = latest_score(db, resume.id)
    missing = (score.missing_keywords or []) if score else []
    role = resolve_role(db, profile.career_goal)
    agent = ResumeAgent(get_llm())
    result = agent.suggest(resume.text, role.name if role else None, list(missing))
    if score is not None:
        score.suggestions = result
        db.commit()
    return ResumeRewriteOut(**result)
