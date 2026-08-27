"""
Custom exception classes and FastAPI exception handlers.

All API errors follow a consistent format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message."
    }
}
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AppException(Exception):
    """Base application exception."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found.", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=404)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized.", code: str = "UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=401)


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request.", code: str = "BAD_REQUEST"):
        super().__init__(code=code, message=message, status_code=400)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden.", code: str = "FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=403)


def register_exception_handlers(app: FastAPI):
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"AppException: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # If detail is already structured, pass it through
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {type(exc).__name__}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred.",
                }
            },
        )
