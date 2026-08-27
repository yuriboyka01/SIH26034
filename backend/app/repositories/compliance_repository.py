"""
Phase 4: Compliance Repository

Handles persistence and retrieval of compliance reports and rule results.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.compliance import ComplianceReport, ComplianceRuleResult


class ComplianceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report: ComplianceReport) -> ComplianceReport:
        """
        Creates a new compliance report (with its rule results).
        """
        self.db.add(report)
        self.db.flush()
        return report

    def get_report_by_ocr_result_id(self, ocr_result_id: UUID) -> Optional[ComplianceReport]:
        """
        Retrieves the compliance report for a specific OCR result.
        """
        return (
            self.db.query(ComplianceReport)
            .filter(ComplianceReport.ocr_result_id == ocr_result_id)
            .first()
        )

    def get_reports_by_inspection_id(self, inspection_id: UUID) -> List[ComplianceReport]:
        """
        Retrieves all compliance reports for an inspection.
        """
        from app.models.ocr_result import OCRResult
        from app.models.inspection_image import InspectionImage

        return (
            self.db.query(ComplianceReport)
            .join(OCRResult, ComplianceReport.ocr_result_id == OCRResult.id)
            .join(InspectionImage, OCRResult.image_id == InspectionImage.id)
            .filter(InspectionImage.inspection_id == inspection_id)
            .all()
        )

    def delete_for_ocr_result(self, ocr_result_id: UUID) -> None:
        """
        Deletes the compliance report for a given OCR result (used during re-analysis).
        """
        self.db.query(ComplianceReport).filter(
            ComplianceReport.ocr_result_id == ocr_result_id
        ).delete()

    def commit(self) -> None:
        self.db.commit()
