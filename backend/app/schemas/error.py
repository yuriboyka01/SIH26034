"""
Error response schemas for consistent API error format.
"""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    error: ErrorDetail
