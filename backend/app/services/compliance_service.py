"""
Phase 4: Compliance Service

Orchestrates fetching product info, evaluating compliance rules via the engine,
and persisting the results via the repository.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.compliance import ComplianceReport as DBComplianceReport, ComplianceRuleResult as DBRuleResult
from app.repositories.compliance_repository import ComplianceRepository
from app.repositories.product_repository import ProductInfoRepository
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.image_repository import ImageRepository
from app.compliance.engine import ComplianceRuleEngine, ENGINE_VERSION, RULESET_VERSION
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import logger


class ComplianceService:
    def __init__(self, db: Session):
        self.db = db
        self.comp_repo = ComplianceRepository(db)
        self.prod_repo = ProductInfoRepository(db)
        self.insp_repo = InspectionRepository(db)
        self.img_repo = ImageRepository(db)
        self.engine = ComplianceRuleEngine()

    def run_compliance_for_inspection(self, inspection_id: UUID, user_id: UUID) -> dict:
        """
        Runs the compliance engine against all images in an inspection.
        Requires that ProductInfo has already been extracted (Phase 3).
        """
        inspection = self.insp_repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

        images = self.img_repo.list_by_inspection(inspection_id)
        if not images:
            raise BadRequestError(code="NO_IMAGES", message="No images to check.")

        reports_dict = []
        overall_inspection_status = "PASS"
        has_review = False
        has_fail = False

        for image in images:
            # We need the ProductInfo for this image
            # Go through OCR result to get ProductInfo
            from app.repositories.ocr_repository import OCRRepository
            ocr_repo = OCRRepository(self.db)
            db_ocr = ocr_repo.get_by_image_id(image.id)

            if not db_ocr or not db_ocr.product_info:
                logger.warning(f"COMPLIANCE | No ProductInfo found for image {image.id}. Skipping.")
                continue

            product_info = db_ocr.product_info
            
            # Delete old compliance report for this OCR result
            self.comp_repo.delete_for_ocr_result(db_ocr.id)

            # Evaluate rules
            extracted_fields = product_info.get_fields()
            report_schema = self.engine.evaluate(str(inspection_id), str(image.id), extracted_fields)

            # Persist the report
            db_report = DBComplianceReport(
                ocr_result_id=db_ocr.id,
                overall_status=report_schema.overall_status.value,
                total_rules_checked=report_schema.total_rules_checked,
                passed_count=report_schema.passed_count,
                failed_count=report_schema.failed_count,
                review_count=report_schema.review_count,
                not_applicable_count=report_schema.not_applicable_count,
                engine_version=ENGINE_VERSION,
                ruleset_version=RULESET_VERSION,
            )

            for rr in report_schema.rule_results:
                db_rr = DBRuleResult(
                    rule_id=rr.rule_id,
                    rule_name=rr.rule_name,
                    status=rr.status.value,
                    severity=rr.severity.value,
                    message=rr.message,
                    field=rr.field,
                    expected=rr.expected,
                    actual=rr.actual,
                    source_reference=rr.source_reference
                )
                if rr.evidence:
                    db_rr.set_evidence(rr.evidence)
                db_report.rule_results.append(db_rr)

            self.comp_repo.create_report(db_report)
            
            # Aggregate status for overall inspection
            if report_schema.overall_status.value == "FAIL":
                has_fail = True
            elif report_schema.overall_status.value == "REVIEW":
                has_review = True

            reports_dict.append(report_schema.dict())

        self.comp_repo.commit()

        if has_fail:
            overall_inspection_status = "FAIL"
        elif has_review:
            overall_inspection_status = "REVIEW"
        elif not reports_dict:
            overall_inspection_status = "NOT_ANALYSED"

        return {
            "inspection_id": str(inspection_id),
            "overall_status": overall_inspection_status,
            "reports": reports_dict
        }

    def get_compliance_reports(self, inspection_id: UUID, user_id: UUID) -> dict:
        """
        Retrieve persisted compliance reports for an inspection.
        """
        inspection = self.insp_repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

        reports = self.comp_repo.get_reports_by_inspection_id(inspection_id)
        
        reports_dict = []
        has_fail = False
        has_review = False
        
        for rep in reports:
            # We need image_id which is on the ocr_result
            image_id = rep.ocr_result.image_id
            
            if rep.overall_status == "FAIL":
                has_fail = True
            elif rep.overall_status == "REVIEW":
                has_review = True
                
            rule_results_dict = []
            for rr in rep.rule_results:
                rule_results_dict.append({
                    "rule_id": rr.rule_id,
                    "rule_name": rr.rule_name,
                    "status": rr.status,
                    "severity": rr.severity,
                    "message": rr.message,
                    "field": rr.field,
                    "expected": rr.expected,
                    "actual": rr.actual,
                    "evidence": rr.get_evidence(),
                    "source_reference": rr.source_reference
                })
            
            reports_dict.append({
                "inspection_id": str(inspection_id),
                "image_id": str(image_id),
                "overall_status": rep.overall_status,
                "total_rules_checked": rep.total_rules_checked,
                "passed_count": rep.passed_count,
                "failed_count": rep.failed_count,
                "review_count": rep.review_count,
                "not_applicable_count": rep.not_applicable_count,
                "rule_results": rule_results_dict
            })
            
        overall_inspection_status = "PASS"
        if has_fail:
            overall_inspection_status = "FAIL"
        elif has_review:
            overall_inspection_status = "REVIEW"
        elif not reports_dict:
            overall_inspection_status = "NOT_ANALYSED"

        return {
            "inspection_id": str(inspection_id),
            "overall_status": overall_inspection_status,
            "reports": reports_dict
        }
