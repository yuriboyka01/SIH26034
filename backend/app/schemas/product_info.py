"""
Phase 3: Pydantic schemas for structured product information.

These are the API-facing types for the /product-info endpoint
and the product_info field embedded in AnalysisResponse.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FieldEvidenceSchema(BaseModel):
    source_text: str
    confidence: float
    bbox: Optional[List[float]] = None


class ExtractedFieldSchema(BaseModel):
    field_name: str
    value: Optional[str] = None
    detection_status: str  # DETECTED | NOT_DETECTED | UNCERTAIN
    evidence: Optional[FieldEvidenceSchema] = None


class ProductInfoSchema(BaseModel):
    """
    Structured product information extracted from OCR text blocks.

    All fields are Optional — None means the field was NOT detected.
    detection_status per field is in the 'fields' list.
    """
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    batch_number: Optional[str] = None
    country_of_origin: Optional[str] = None
    ingredients: Optional[str] = None
    license_number: Optional[str] = None
    customer_care: Optional[str] = None
    warnings: Optional[str] = None
    # New fields from real-package analysis
    email: Optional[str] = None
    unit_sale_price: Optional[str] = None
    packaging_date: Optional[str] = None
    commodity: Optional[str] = None
    storage_instructions: Optional[str] = None
    sale_restrictions: Optional[str] = None

    # Evidence-linked fields list (for Phase 4 rules engine)
    fields: List[ExtractedFieldSchema] = []

    # Metadata
    total_blocks_processed: Optional[int] = None
    extraction_version: Optional[str] = None


class ProductInfoResponse(BaseModel):
    """Response for GET /api/inspections/{id}/product-info."""
    inspection_id: str
    status: str
    product_info_list: List[ProductInfoSchema] = []
