"""GitHub Intelligence endpoints — analyze + cached fetch."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.github import GitHubClient, GitHubError
from app.adapters.models import User
from app.agents.llm.factory import get_llm
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.schemas import GithubAnalyzeRequest, GithubOut
from app.services.github_service import get_cached, get_or_analyze
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/analyze", response_model=GithubOut)
def analyze_github(
    data: GithubAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GithubOut:
    profile = get_or_create_profile(db, user.id)
    client = GitHubClient(get_settings().github_token)
    try:
        gp = get_or_analyze(db, profile, data.username, client, get_llm())
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return GithubOut.model_validate(gp)


@router.get("", response_model=GithubOut)
def get_github(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> GithubOut:
    profile = get_or_create_profile(db, user.id)
    gp = get_cached(db, profile.id)
    if gp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no github analysis yet")
    return GithubOut.model_validate(gp)
