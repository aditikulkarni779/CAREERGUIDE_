"""Authentication use-cases."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.models import AuthProvider, User
from app.core.security import hash_password, verify_password
from app.schemas import UserCreate


class AuthError(Exception):
    """Raised for auth failures (mapped to HTTP by the router)."""


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise AuthError("email already registered")
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        auth_provider=AuthProvider.password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise AuthError("invalid credentials")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    return user


def upsert_oauth_user(db: Session, email: str, provider: AuthProvider) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        user = User(email=email.lower(), auth_provider=provider)
        db.add(user)
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
