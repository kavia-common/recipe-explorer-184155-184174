from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.errors import AppError, error_response
from src.core.logging_config import configure_logging
from src.core.security import get_current_user_optional

# Configure logging at import time for the app process
configure_logging()
logger = logging.getLogger("api")


def create_app() -> FastAPI:
    """
    PUBLIC_INTERFACE
    Create and configure the FastAPI application instance.

    Returns:
        FastAPI: Configured FastAPI app with routers, middleware, and error handlers registered.
    """
    settings = get_settings()

    app = FastAPI(
        title="Recipe Explorer API",
        description="Backend API for managing recipes, users, authentication and search.",
        version="0.1.0",
        openapi_tags=[
            {"name": "health", "description": "Service health and diagnostics"},
            {"name": "auth", "description": "Authentication and authorization"},
            {"name": "users", "description": "User operations"},
            {"name": "recipes", "description": "Recipe CRUD and rating"},
            {"name": "search", "description": "Search recipes"},
        ],
    )

    # CORS (permissive for now)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handler for AppError -> JSON structure with proper status
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc)

    # Error handler for generic Exceptions
    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        app_error = AppError.internal_server_error("Internal Server Error")
        return error_response(app_error)

    # Request/Response logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        user = None
        try:
            # Try to get user if auth header exists, but do not fail the request here.
            user = await get_current_user_optional(request)
        except Exception:  # noqa: BLE001
            user = None

        response: Optional[Response] = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            status = response.status_code if response is not None else 500
            logger.info(
                "request_log method=%s path=%s status=%s duration_ms=%.2f user_id=%s",
                request.method,
                request.url.path,
                status,
                duration_ms,
                getattr(user, "id", None),
            )

    # Health route
    @app.get("/", tags=["health"], summary="Health Check")
    def health_check() -> dict[str, str]:
        """
        PUBLIC_INTERFACE
        Health check endpoint.

        Returns:
            dict[str, str]: {"message": "Healthy"}
        """
        return {"message": "Healthy"}

    # Routers
    from src.api.routers.recipes import router as recipes_router
    from src.api.routers.search import router as search_router
    from src.api.routers.users import router as users_router

    app.include_router(users_router)
    app.include_router(recipes_router)
    app.include_router(search_router)

    return app


app = create_app()
