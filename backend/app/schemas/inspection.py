"""
Inspection-related Pydantic schemas.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.schemas.image import ImageResponse


class InspectionCreate(BaseModel):
    """Schema for creating a new inspection."""
    product_name: str = Field(..., min_length=1, max_length=500, examples=["Example Rice"])
    brand: str = Field(..., min_length=1, max_length=255, examples=["Example Brand"])


class InspectionResponse(BaseModel):
    """Schema for inspection response."""
    id: UUID
    inspection_number: str
    product_name: str
    brand: str
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    images: List[ImageResponse] = []

    model_config = {"from_attributes": True}


class InspectionListResponse(BaseModel):
    """Schema for inspection list response (without images)."""
    id: UUID
    inspection_number: str
    product_name: str
    brand: str
    status: str
    created_at: datetime
    image_count: int = 0

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total: int = 0
    created: int = 0
    images_uploaded: int = 0
    processing: int = 0
    completed: int = 0
    needs_review: int = 0
