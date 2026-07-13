"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    get_logger().info("api.startup", env=settings.env, llm_provider=settings.llm_provider)
    yield
    get_logger().info("api.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title="AI Career Copilot API", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
