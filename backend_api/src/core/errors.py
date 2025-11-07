from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse
from starlette import status


@dataclass
class AppError(Exception):
    """Application error with HTTP semantics."""

    code: str
    message: str
    http_status: int = status.HTTP_400_BAD_REQUEST
    details: Any | None = None

    @staticmethod
    def bad_request(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="bad_request", message=message, http_status=status.HTTP_400_BAD_REQUEST, details=details)

    @staticmethod
    def unauthorized(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="unauthorized", message=message, http_status=status.HTTP_401_UNAUTHORIZED, details=details)

    @staticmethod
    def forbidden(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="forbidden", message=message, http_status=status.HTTP_403_FORBIDDEN, details=details)

    @staticmethod
    def not_found(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="not_found", message=message, http_status=status.HTTP_404_NOT_FOUND, details=details)

    @staticmethod
    def conflict(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="conflict", message=message, http_status=status.HTTP_409_CONFLICT, details=details)

    @staticmethod
    def internal_server_error(message: str, details: Any | None = None) -> "AppError":
        return AppError(code="internal_server_error", message=message, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


def error_response(err: AppError) -> JSONResponse:
    """Return standardized error envelope."""
    payload = {
        "error": {
            "code": err.code,
            "message": err.message,
            "details": err.details,
        }
    }
    return JSONResponse(status_code=err.http_status, content=payload)
