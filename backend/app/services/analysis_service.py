"""
Analysis service — orchestrates quality analysis, preprocessing, OCR, and persistence.

Coordinates:
  image_path → quality check → OCR → persist → extraction → return AnalysisResult

Phase 3: After OCR is persisted, ExtractionService converts text blocks into
structured product information and persists it to product_info table.

This service intentionally stays ignorant of legal rules (Phase 4+).
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import ocr_service
from app.ai.models import AnalysisResult, OCRResult
from app.models.ocr_result import (
    OCRResult as OCRResultModel,
    OCRTextBlock as OCRTextBlockModel,
    QualityStatus,
)
from app.models.inspection import InspectionStatus, Inspection
from app.models.inspection_image import InspectionImage
from app.repositories.ocr_repository import OCRRepository
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.image_repository import ImageRepository
from app.services.extraction_service import ExtractionService
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import logger


class AnalysisService:
    """Coordinates image analysis: OCR + persistence + inspection status update."""

    def __init__(self, db: Session):
        self.db = db
        self.ocr_repo = OCRRepository(db)
        self.insp_repo = InspectionRepository(db)
        self.img_repo = ImageRepository(db)
        self.extraction_svc = ExtractionService(db)

    def analyze_inspection(self, inspection_id: UUID, user_id: UUID) -> dict:
        """
        Run OCR + Phase 3 extraction on every image attached to an inspection.

        Returns a dict matching the API response schema.
        Raises NotFoundError if inspection not found or not owned by user.
        Raises BadRequestError if inspection has no images.
        """
        # --- Guard: inspection exists and belongs to user ---
        inspection = self.insp_repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

        images: List[InspectionImage] = self.img_repo.list_by_inspection(inspection_id)
        if not images:
            raise BadRequestError(
                code="NO_IMAGES",
                message="This inspection has no images to analyse. Upload at least one image first.",
            )

        # --- Mark as PROCESSING ---
        self.insp_repo.update_status(inspection_id, InspectionStatus.PROCESSING)

        image_results = []
        any_poor = False

        for image in images:
            result = self._analyze_image(image, inspection)
            image_results.append(result)
            if result.get("quality", {}).get("status") == "POOR":
                any_poor = True

        # --- Update inspection status ---
        final_status = InspectionStatus.NEEDS_REVIEW if any_poor else InspectionStatus.COMPLETED
        self.insp_repo.update_status(inspection_id, final_status)

        return {
            "inspection_id": str(inspection_id),
            "status": final_status.value,
            "images": image_results,
        }

    def _analyze_image(self, image: InspectionImage, inspection: Optional[Inspection] = None) -> dict:
        """
        Run OCR + Phase 3 extraction on a single image and persist results.

        Returns a dict compatible with the ImageAnalysisResult schema.
        Errors are caught per-image so one bad image doesn't fail the whole inspection.
        """
        image_id = image.id
        image_path = image.file_path

        try:
            logger.info(f"ANALYSIS | starting | image_id={image_id} | path={image_path}")

            # Delete any previous OCR results for this image (re-analysis replaces)
            self.ocr_repo.delete_for_image(image_id)

            # Run OCR
            ocr: OCRResult = ocr_service.extract(image_path)

            # Persist result
            quality_status = QualityStatus(ocr.quality.status)
            db_result = OCRResultModel(
                image_id=image_id,
                engine=ocr.engine,
                engine_version=ocr.engine_version,
                full_text=ocr.full_text,
                processing_time_ms=ocr.processing_time_ms,
                preprocessing_applied=",".join(ocr.preprocessing_applied),
                quality_status=quality_status,
                quality_blur_score=ocr.quality.blur_score,
                quality_brightness_score=ocr.quality.brightness_score,
                quality_issues=",".join(ocr.quality.issues),
            )
            self.ocr_repo.create_result(db_result)

            # Persist text blocks
            for block in ocr.blocks:
                db_block = OCRTextBlockModel(
                    ocr_result_id=db_result.id,
                    raw_text=block.raw_text,
                    normalized_text=block.normalized_text,
                    confidence=block.confidence,
                    bbox_x1=block.bbox[0],
                    bbox_y1=block.bbox[1],
                    bbox_x2=block.bbox[2],
                    bbox_y2=block.bbox[3],
                )
                self.ocr_repo.create_text_block(db_block)

            self.ocr_repo.commit()
            logger.info(
                f"ANALYSIS | OCR done | image_id={image_id} | "
                f"blocks={len(ocr.blocks)} | quality={ocr.quality.status} | "
                f"time={ocr.processing_time_ms}ms"
            )

            # --- Phase 3: Run extraction on the persisted OCR result ---
            product_info_dict = None
            try:
                product_info_dict = self.extraction_svc.extract_and_persist(
                    db_ocr_result=db_result,
                    inspection_product_name=inspection.product_name if inspection else None,
                    inspection_brand=inspection.brand if inspection else None,
                )
                self.ocr_repo.commit()  # commit product_info record
            except Exception as ext_exc:
                logger.warning(f"EXTRACTION | failed (non-fatal) | image_id={image_id} | error={ext_exc}")
                # Extraction failure is non-fatal — OCR results are still returned

            return {
                "image_id": str(image_id),
                "status": "OK",
                "quality": {
                    "status": ocr.quality.status,
                    "blur_score": round(ocr.quality.blur_score, 2),
                    "brightness_score": round(ocr.quality.brightness_score, 3),
                    "issues": ocr.quality.issues,
                },
                "ocr": {
                    "engine": ocr.engine,
                    "engine_version": ocr.engine_version,
                    "full_text": ocr.full_text,
                    "processing_time_ms": ocr.processing_time_ms,
                    "preprocessing_applied": ocr.preprocessing_applied,
                    "blocks": [
                        {
                            "text": b.normalized_text,
                            "raw_text": b.raw_text,
                            "confidence": round(b.confidence, 4),
                            "bbox": [round(v, 1) for v in b.bbox],
                        }
                        for b in ocr.blocks
                    ],
                },
                "product_info": product_info_dict,
            }

        except Exception as exc:
            logger.exception(f"ANALYSIS | failed | image_id={image_id} | error={exc}")
            # Roll back any partial writes for this image
            self.db.rollback()
            return {
                "image_id": str(image_id),
                "status": "ERROR",
                "error": str(exc),
                "quality": None,
                "ocr": None,
                "product_info": None,
            }

    def get_analysis_results(self, inspection_id: UUID, user_id: UUID) -> dict:
        """
        Return the persisted OCR results for an inspection without re-running OCR.
        """
        inspection = self.insp_repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

        images = self.img_repo.list_by_inspection(inspection_id)
        image_results = []

        for image in images:
            db_result = self.ocr_repo.get_by_image_id(image.id)
            if db_result is None:
                image_results.append({
                    "image_id": str(image.id),
                    "status": "NOT_ANALYSED",
                    "quality": None,
                    "ocr": None,
                    "product_info": None,
                })
                continue

            # Load product_info if available
            product_info_dict = None
            if db_result.product_info:
                pi = db_result.product_info
                product_info_dict = {
                    "product_name": pi.product_name,
                    "brand_name": pi.brand_name,
                    "manufacturer": pi.manufacturer,
                    "net_quantity": pi.net_quantity,
                    "mrp": pi.mrp,
                    "manufacturing_date": pi.manufacturing_date,
                    "expiry_date": pi.expiry_date,
                    "batch_number": pi.batch_number,
                    "country_of_origin": pi.country_of_origin,
                    "ingredients": pi.ingredients,
                    "license_number": pi.license_number,
                    "customer_care": pi.customer_care,
                    "warnings": pi.warnings,
                    "fields": pi.get_fields(),
                    "total_blocks_processed": pi.total_blocks_processed,
                    "extraction_version": pi.extraction_version,
                }

            image_results.append({
                "image_id": str(image.id),
                "status": "OK",
                "quality": {
                    "status": db_result.quality_status.value,
                    "blur_score": db_result.quality_blur_score,
                    "brightness_score": db_result.quality_brightness_score,
                    "issues": db_result.quality_issues.split(",") if db_result.quality_issues else [],
                },
                "ocr": {
                    "engine": db_result.engine,
                    "engine_version": db_result.engine_version,
                    "full_text": db_result.full_text,
                    "processing_time_ms": db_result.processing_time_ms,
                    "preprocessing_applied": (
                        db_result.preprocessing_applied.split(",")
                        if db_result.preprocessing_applied else []
                    ),
                    "blocks": [
                        {
                            "text": b.normalized_text,
                            "raw_text": b.raw_text,
                            "confidence": round(b.confidence, 4),
                            "bbox": b.bbox,
                        }
                        for b in db_result.text_blocks
                    ],
                },
                "product_info": product_info_dict,
            })

        return {
            "inspection_id": str(inspection_id),
            "status": inspection.status.value,
            "images": image_results,
        }
