"""
Image-related Pydantic schemas.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ImageResponse(BaseModel):
    """Schema for image metadata response."""
    id: UUID
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    image_type: str
    url: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}
