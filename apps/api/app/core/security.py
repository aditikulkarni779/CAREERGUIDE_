"""Password hashing and JWT token helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import get_settings

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _create_token(subject: str, token_type: TokenType, expires: timedelta) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_access_token(subject: str) -> str:
    s = get_settings()
    return _create_token(subject, "access", timedelta(minutes=s.access_token_ttl_min))


def create_refresh_token(subject: str) -> str:
    s = get_settings()
    return _create_token(subject, "refresh", timedelta(days=s.refresh_token_ttl_days))


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt exceptions on failure."""
    s = get_settings()
    payload: dict[str, Any] = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload
