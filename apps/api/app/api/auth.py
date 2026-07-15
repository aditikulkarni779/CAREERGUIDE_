"""Authentication endpoints (password flow + token refresh)."""
from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.adapters.models import User
from app.api.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas import AccessToken, LoginRequest, RefreshRequest, TokenPair, UserCreate, UserOut
from app.services.auth_service import AuthError, authenticate, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return register_user(db, data)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        user = authenticate(db, data.email, data.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    return _tokens(user)


@router.post("/refresh", response_model=AccessToken)
def refresh(data: RefreshRequest) -> AccessToken:
    try:
        payload = decode_token(data.refresh_token, "refresh")
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token"
        ) from e
    return AccessToken(access_token=create_access_token(payload["sub"]))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    # Stateless JWT: client discards tokens. Blacklist added in a later phase.
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
