from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from observatorio.api.bootstrap import bootstrap_backend
from observatorio.api.routes import router
from observatorio.api.schemas import ApiError
from observatorio.config import parse_cors_origins, settings
from observatorio.logging import get_logger

logger = get_logger("observatorio.api.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    bootstrap_task = asyncio.create_task(bootstrap_backend(), name="database-bootstrap")
    try:
        yield
    finally:
        bootstrap_task.cancel()
        try:
            await bootstrap_task
        except asyncio.CancelledError:
            pass


def _error_body(
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict:
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


def create_app(*, allowed_origins: str | list[str] | None = None) -> FastAPI:
    origins = parse_cors_origins(
        settings.cors_allowed_origins if allowed_origins is None else allowed_origins
    )
    application = FastAPI(title="Observatorio sísmico API", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["ngrok-skip-browser-warning", "content-type"],
        allow_credentials=False,
    )
    application.include_router(router)

    @application.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body("invalid_request", "Request parameters are invalid"),
        )

    @application.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.warning("API database request failed: %s", type(exc).__name__)
        if request.url.path == "/api/salud":
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "last_ingestion": None},
            )
        return JSONResponse(
            status_code=503,
            content=_error_body("dependency_unavailable", "A required service is unavailable"),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("API request failed unexpectedly: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "The request could not be completed"),
        )

    return application


app = create_app()
