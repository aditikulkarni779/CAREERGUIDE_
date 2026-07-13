"""Health and readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    # Phase 0: no external checks yet. Extended in later phases.
    return {"status": "ready"}
