"""
Phase 3: Extraction service.

Orchestrates calling the extraction engine and persisting structured product data.
Called by AnalysisService after OCR text blocks are persisted.

Responsibilities:
  - Accept an OCRResult DB model + Inspection metadata
  - Call app.ai.extraction.extract_product_info()
  - Persist a ProductInfo record
  - Return the structured data dict for inclusion in the API response

This service does NOT modify or replace OCR results.
"""

import json
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.extraction import extract_product_info
from app.models.product_info import ProductInfo
from app.models.ocr_result import OCRResult as OCRResultModel
from app.repositories.product_repository import ProductInfoRepository
from app.core.logging import logger


class ExtractionService:
    """Runs extraction engine on OCR results and persists structured product info."""

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductInfoRepository(db)

    def extract_and_persist(
        self,
        db_ocr_result: OCRResultModel,
        inspection_product_name: Optional[str] = None,
        inspection_brand: Optional[str] = None,
    ) -> dict:
        """
        Run extraction on the text blocks of a DB OCRResult and persist to product_info.

        Args:
            db_ocr_result: The persisted OCRResult whose text_blocks are loaded.
            inspection_product_name: From Inspection.product_name (fallback).
            inspection_brand: From Inspection.brand (fallback).

        Returns:
            dict representation of the extracted product information.
        """
        ocr_result_id = db_ocr_result.id
        logger.info(f"EXTRACTION | ocr_result_id={ocr_result_id}")

        # Build the block list from DB text_blocks
        ocr_blocks = [
            {
                "text": block.normalized_text,
                "confidence": block.confidence,
                "bbox": block.bbox,
            }
            for block in (db_ocr_result.text_blocks or [])
        ]

        # Also include the full_text as a single block for broader pattern matching
        if db_ocr_result.full_text and not ocr_blocks:
            # Fallback when text_blocks aren't loaded but full_text is available
            lines = [line.strip() for line in db_ocr_result.full_text.split("\n") if line.strip()]
            ocr_blocks = [{"text": line, "confidence": 0.5, "bbox": None} for line in lines]

        # Run extraction
        structured = extract_product_info(
            ocr_blocks=ocr_blocks,
            inspection_product_name=inspection_product_name,
            inspection_brand=inspection_brand,
        )

        # Delete any previous product_info for this OCR result (re-analysis)
        self.product_repo.delete_for_ocr_result(ocr_result_id)

        # Persist
        db_record = ProductInfo(
            ocr_result_id=ocr_result_id,
            product_name=structured.product_name,
            brand_name=structured.brand_name,
            manufacturer=structured.manufacturer,
            net_quantity=structured.net_quantity,
            mrp=structured.mrp,
            manufacturing_date=structured.manufacturing_date,
            expiry_date=structured.expiry_date,
            batch_number=structured.batch_number,
            country_of_origin=structured.country_of_origin,
            ingredients=structured.ingredients,
            license_number=structured.license_number,
            customer_care=structured.customer_care,
            warnings=structured.warnings,
            total_blocks_processed=structured.total_blocks_processed,
            extraction_version=structured.extraction_version,
        )
        db_record.set_fields(structured.to_dict()["fields"])
        self.product_repo.create(db_record)

        logger.info(
            f"EXTRACTION | persisted | ocr_result_id={ocr_result_id} "
            f"| mrp={structured.mrp} | qty={structured.net_quantity}"
        )

        return structured.to_dict()

    def get_for_inspection(self, inspection_id: UUID) -> list:
        """
        Return serialized product_info records for all images of an inspection.
        Used by the GET /product-info endpoint.
        """
        records = self.product_repo.get_by_inspection_id(inspection_id)
        result = []
        for rec in records:
            result.append({
                "ocr_result_id": str(rec.ocr_result_id),
                "product_name": rec.product_name,
                "brand_name": rec.brand_name,
                "manufacturer": rec.manufacturer,
                "net_quantity": rec.net_quantity,
                "mrp": rec.mrp,
                "manufacturing_date": rec.manufacturing_date,
                "expiry_date": rec.expiry_date,
                "batch_number": rec.batch_number,
                "country_of_origin": rec.country_of_origin,
                "ingredients": rec.ingredients,
                "license_number": rec.license_number,
                "customer_care": rec.customer_care,
                "warnings": rec.warnings,
                "fields": rec.get_fields(),
                "total_blocks_processed": rec.total_blocks_processed,
                "extraction_version": rec.extraction_version,
            })
        return result
