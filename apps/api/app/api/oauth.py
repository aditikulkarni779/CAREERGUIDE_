"""OAuth login (GitHub, Google). Enabled when client creds are configured.

Manual flow via httpx (no extra deps). Endpoints return 503 until the matching
OAUTH_* env vars are set. Password auth is the tested path in Phase 0/1; OAuth
is verified once credentials exist.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.models import AuthProvider
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token
from app.services.auth_service import upsert_oauth_user

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg)


# ---- GitHub ----
@router.get("/github/login")
def github_login() -> RedirectResponse:
    s = get_settings()
    _require(bool(s.oauth_github_id), "GitHub OAuth not configured")
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={s.oauth_github_id}&scope=read:user%20user:email"
        f"&redirect_uri={s.frontend_url}/auth/callback/github"
    )
    return RedirectResponse(url)


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)) -> dict[str, str]:
    s = get_settings()
    _require(bool(s.oauth_github_id and s.oauth_github_secret), "GitHub OAuth not configured")
    token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": s.oauth_github_id,
            "client_secret": s.oauth_github_secret,
            "code": code,
        },
        timeout=15,
    ).json()
    access = token_res.get("access_token")
    _require(bool(access), "GitHub token exchange failed")
    emails = httpx.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access}"},
        timeout=15,
    ).json()
    primary = next((e["email"] for e in emails if e.get("primary")), None)
    _require(bool(primary), "no primary email from GitHub")
    assert primary is not None
    user = upsert_oauth_user(db, str(primary), AuthProvider.github)
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


# ---- Google ----
@router.get("/google/login")
def google_login() -> RedirectResponse:
    s = get_settings()
    _require(bool(s.oauth_google_id), "Google OAuth not configured")
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={s.oauth_google_id}&response_type=code&scope=openid%20email"
        f"&redirect_uri={s.frontend_url}/auth/callback/google"
    )
    return RedirectResponse(url)


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)) -> dict[str, str]:
    s = get_settings()
    _require(bool(s.oauth_google_id and s.oauth_google_secret), "Google OAuth not configured")
    token_res = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": s.oauth_google_id,
            "client_secret": s.oauth_google_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{s.frontend_url}/auth/callback/google",
        },
        timeout=15,
    ).json()
    access = token_res.get("access_token")
    _require(bool(access), "Google token exchange failed")
    info = httpx.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access}"},
        timeout=15,
    ).json()
    email = info.get("email")
    _require(bool(email), "no email from Google")
    assert email is not None
    user = upsert_oauth_user(db, str(email), AuthProvider.google)
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }
