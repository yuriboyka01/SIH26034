"""
Phase 5: Dashboard analytics service.

Provides aggregation and metrics over compliance data for the dashboard.
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from sqlalchemy.orm import aliased

from app.models.inspection import Inspection, InspectionStatus
from app.models.compliance import ComplianceReport, ComplianceRuleResult
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.schemas.dashboard import (
    DashboardAnalyticsResponse,
    ComplianceKPIs,
    ViolationSummaryItem,
    RecentInspectionItem
)

# FAIL > REVIEW > PASS > NOT_APPLICABLE
STATUS_PRIORITY = {
    "FAIL": 4,
    "REVIEW": 3,
    "PASS": 2,
    "NOT_APPLICABLE": 1,
    "NOT_ANALYSED": 0
}


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_analytics(self) -> DashboardAnalyticsResponse:
        """
        Calculates compliance KPIs, top violations, and recent inspections across all users.
        NOTE: In a multi-tenant system this might be filtered by user_id, but the enforcement
        dashboard usually sees all data or department data. We will query all for the demo.
        """
        
        # 1. Fetch all inspections and their compliance reports to calculate overall status
        inspections = self.db.query(Inspection).order_by(Inspection.created_at.desc()).all()
        
        total_inspections = len(inspections)
        compliant_count = 0
        non_compliant_count = 0
        review_count = 0
        not_analysed_count = 0
        
        recent_inspections: List[RecentInspectionItem] = []
        
        # To avoid N+1 queries, we could use subqueries, but since this is a SQLite demo
        # and we need to apply the FAIL > REVIEW > PASS priority per inspection, we can
        # fetch the reports. In a real massive DB, we'd do a complex GROUP BY query.
        
        # Fetch all reports
        all_reports = (
            self.db.query(
                Inspection.id.label('inspection_id'),
                ComplianceReport.overall_status
            )
            .join(InspectionImage, Inspection.id == InspectionImage.inspection_id)
            .join(OCRResult, InspectionImage.id == OCRResult.image_id)
            .join(ComplianceReport, OCRResult.id == ComplianceReport.ocr_result_id)
            .all()
        )
        
        # Group reports by inspection_id
        insp_reports_map = {}
        for row in all_reports:
            insp_id = str(row.inspection_id)
            if insp_id not in insp_reports_map:
                insp_reports_map[insp_id] = []
            insp_reports_map[insp_id].append(row.overall_status)
            
        # Process inspections
        for insp in inspections:
            insp_id = str(insp.id)
            overall_status = "NOT_ANALYSED"
            
            if insp_id in insp_reports_map:
                reports = insp_reports_map[insp_id]
                for status in reports:
                    if STATUS_PRIORITY.get(status, 0) > STATUS_PRIORITY.get(overall_status, 0):
                        overall_status = status
            
            if overall_status == "PASS":
                compliant_count += 1
            elif overall_status == "FAIL":
                non_compliant_count += 1
            elif overall_status == "REVIEW":
                review_count += 1
            else:
                not_analysed_count += 1
                
            # Add to recent if we have less than 10
            if len(recent_inspections) < 10:
                recent_inspections.append(
                    RecentInspectionItem(
                        id=insp_id,
                        inspection_number=insp.inspection_number,
                        product_name=insp.product_name,
                        brand=insp.brand,
                        created_at=insp.created_at.isoformat(),
                        compliance_status=overall_status
                    )
                )

        compliance_rate = 0.0
        analysed = total_inspections - not_analysed_count
        if analysed > 0:
            compliance_rate = round((compliant_count / analysed) * 100, 1)

        kpis = ComplianceKPIs(
            total_inspections=total_inspections,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            review_count=review_count,
            not_analysed_count=not_analysed_count,
            compliance_rate=compliance_rate
        )

        # 2. Top Violations Aggregation
        violation_counts = (
            self.db.query(
                ComplianceRuleResult.rule_id,
                ComplianceRuleResult.rule_name,
                func.count(ComplianceRuleResult.id).label('count')
            )
            .filter(ComplianceRuleResult.status == 'FAIL')
            .group_by(ComplianceRuleResult.rule_id, ComplianceRuleResult.rule_name)
            .order_by(desc('count'))
            .limit(10)
            .all()
        )

        top_violations = [
            ViolationSummaryItem(
                rule_id=row.rule_id,
                rule_name=row.rule_name,
                count=row.count
            )
            for row in violation_counts
        ]

        return DashboardAnalyticsResponse(
            kpis=kpis,
            top_violations=top_violations,
            recent_inspections=recent_inspections
        )
