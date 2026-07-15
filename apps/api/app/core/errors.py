"""RFC 7807 problem+json exception handling."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _problem(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"/errors/{status}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(exc.status_code, "HTTP Error", str(exc.detail), str(request.url.path))

    @app.exception_handler(RequestValidationError)
    async def validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem(422, "Validation Error", str(exc.errors()), str(request.url.path))
