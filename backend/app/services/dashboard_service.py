"""
Phase 5: Dashboard analytics service.

Provides aggregation and metrics over compliance data for the dashboard.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.inspection import Inspection
from app.models.compliance import ComplianceReport, ComplianceRuleResult
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.schemas.dashboard import (
    DashboardAnalyticsResponse,
    ComplianceKPIs,
    ViolationSummaryItem,
    RecentInspectionItem,
    RepeatOffenderItem,
    GeoPointItem,
)

# A package is usually photographed more than once (front + back), and each
# photo is OCR'd and rule-checked independently (see compliance_service.py).
# Before any per-inspection status can be trusted -- for KPIs, "top
# violations", or repeat-offender grouping -- the per-photo results for a
# given rule must be merged into one verdict: PASS if the requirement was
# satisfied on ANY photo, otherwise the least-bad outcome seen. This mirrors
# frontend/src/api/compliance.ts's mergeComplianceReports() and must stay
# in sync with it.
STATUS_RANK = {"PASS": 0, "NOT_APPLICABLE": 1, "REVIEW": 2, "FAIL": 3}

# A rule_id -> (rule_name, status, severity) merged verdict for one inspection.
MergedRules = Dict[str, Tuple[str, str, str]]


def _merge_rule_rows(rows: List[Tuple[str, str, str, str]]) -> MergedRules:
    """rows: list of (rule_id, rule_name, status, severity) from every photo of one inspection."""
    best: MergedRules = {}
    for rule_id, rule_name, status, severity in rows:
        current = best.get(rule_id)
        if current is None or STATUS_RANK[status] < STATUS_RANK[current[1]]:
            best[rule_id] = (rule_name, status, severity)
    return best


def _overall_status(merged: MergedRules) -> str:
    """Mirrors ComplianceRuleEngine.evaluate()'s overall-status formula exactly (app/compliance/engine.py)."""
    if not merged:
        return "NOT_ANALYSED"
    has_high_critical_fail = any(
        status == "FAIL" and severity in ("CRITICAL", "HIGH") for _, status, severity in merged.values()
    )
    if has_high_critical_fail:
        return "FAIL"
    if any(status in ("FAIL", "REVIEW") for _, status, _ in merged.values()):
        return "REVIEW"
    return "PASS"


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_analytics(self, user_id: UUID) -> DashboardAnalyticsResponse:
        """
        Calculates compliance KPIs, top violations, repeat offenders, and
        recent inspections for the user -- all derived from per-inspection
        merged rule verdicts rather than raw per-photo rows.
        """
        inspections = (
            self.db.query(Inspection)
            .filter(Inspection.created_by == user_id)
            .order_by(Inspection.created_at.desc())
            .all()
        )

        # One wide query: every rule result for every photo of every one of this
        # user's inspections, tagged with which inspection and brand it belongs to.
        rows = (
            self.db.query(
                Inspection.id.label("inspection_id"),
                ComplianceRuleResult.rule_id,
                ComplianceRuleResult.rule_name,
                ComplianceRuleResult.status,
                ComplianceRuleResult.severity,
            )
            .filter(Inspection.created_by == user_id)
            .join(InspectionImage, Inspection.id == InspectionImage.inspection_id)
            .join(OCRResult, InspectionImage.id == OCRResult.image_id)
            .join(ComplianceReport, OCRResult.id == ComplianceReport.ocr_result_id)
            .join(ComplianceRuleResult, ComplianceReport.id == ComplianceRuleResult.report_id)
            .all()
        )

        raw_rows_by_inspection: Dict[str, List[Tuple[str, str, str, str]]] = defaultdict(list)
        for row in rows:
            raw_rows_by_inspection[str(row.inspection_id)].append(
                (row.rule_id, row.rule_name, row.status, row.severity)
            )

        merged_by_inspection: Dict[str, MergedRules] = {
            insp_id: _merge_rule_rows(raw_rows) for insp_id, raw_rows in raw_rows_by_inspection.items()
        }

        # --- KPIs + recent inspections, from the corrected per-inspection status ---
        compliant_count = non_compliant_count = review_count = not_analysed_count = 0
        recent_inspections: List[RecentInspectionItem] = []

        for insp in inspections:
            insp_id = str(insp.id)
            status = _overall_status(merged_by_inspection.get(insp_id, {}))

            if status == "PASS":
                compliant_count += 1
            elif status == "FAIL":
                non_compliant_count += 1
            elif status == "REVIEW":
                review_count += 1
            else:
                not_analysed_count += 1

            if len(recent_inspections) < 10:
                recent_inspections.append(
                    RecentInspectionItem(
                        id=insp_id,
                        inspection_number=insp.inspection_number,
                        product_name=insp.product_name,
                        brand=insp.brand,
                        created_at=insp.created_at.isoformat(),
                        compliance_status=status,
                    )
                )

        total_inspections = len(inspections)
        analysed = total_inspections - not_analysed_count
        compliance_rate = round((compliant_count / analysed) * 100, 1) if analysed > 0 else 0.0

        kpis = ComplianceKPIs(
            total_inspections=total_inspections,
            compliant_count=compliant_count,
            non_compliant_count=non_compliant_count,
            review_count=review_count,
            not_analysed_count=not_analysed_count,
            compliance_rate=compliance_rate,
        )

        # --- Top violations: count each FAILED rule once per inspection, not once per photo ---
        violation_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        for merged in merged_by_inspection.values():
            for rule_id, (rule_name, status, _severity) in merged.items():
                if status == "FAIL":
                    violation_counts[(rule_id, rule_name)] += 1

        top_violations = [
            ViolationSummaryItem(rule_id=rule_id, rule_name=rule_name, count=count)
            for (rule_id, rule_name), count in sorted(violation_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ]

        # --- Repeat offenders: brands with a pattern of FAILs across separate inspections ---
        repeat_offenders = self._compute_repeat_offenders(inspections, merged_by_inspection)

        # --- Geo points: any inspection with a captured location, for the violation map ---
        geo_points = [
            GeoPointItem(
                inspection_id=str(insp.id),
                inspection_number=insp.inspection_number,
                brand=insp.brand,
                product_name=insp.product_name,
                establishment_name=insp.establishment_name,
                latitude=insp.latitude,
                longitude=insp.longitude,
                compliance_status=_overall_status(merged_by_inspection.get(str(insp.id), {})),
            )
            for insp in inspections
            if insp.latitude is not None and insp.longitude is not None
        ]

        return DashboardAnalyticsResponse(
            kpis=kpis,
            top_violations=top_violations,
            recent_inspections=recent_inspections,
            repeat_offenders=repeat_offenders,
            geo_points=geo_points,
        )

    def _compute_repeat_offenders(
        self,
        inspections: List[Inspection],
        merged_by_inspection: Dict[str, MergedRules],
        min_fails: int = 2,
        limit: int = 8,
    ) -> List[RepeatOffenderItem]:
        """
        Groups inspections by brand (case/whitespace-insensitive) and surfaces
        brands that have FAILed compliance on 2+ separate inspections -- a
        signal worth escalating beyond a one-off correction, since it points
        at a labeling problem in the manufacturer's process rather than a
        single mislabeled unit.
        """
        # brand_key -> list of (inspection, status, rule_fail_counts)
        groups: Dict[str, List[Inspection]] = defaultdict(list)
        for insp in inspections:
            brand_key = (insp.brand or "").strip().lower()
            if brand_key:
                groups[brand_key].append(insp)

        offenders: List[RepeatOffenderItem] = []
        for brand_key, group_inspections in groups.items():
            fail_count = 0
            review_count = 0
            rule_fail_counts: Dict[Tuple[str, str], int] = defaultdict(int)

            for insp in group_inspections:
                merged = merged_by_inspection.get(str(insp.id), {})
                status = _overall_status(merged)
                if status == "FAIL":
                    fail_count += 1
                    for rule_id, (rule_name, rule_status, _severity) in merged.items():
                        if rule_status == "FAIL":
                            rule_fail_counts[(rule_id, rule_name)] += 1
                elif status == "REVIEW":
                    review_count += 1

            if fail_count < min_fails:
                continue

            top_rule_id: Optional[str] = None
            top_rule_name: Optional[str] = None
            top_rule_count = 0
            if rule_fail_counts:
                (top_rule_id, top_rule_name), top_rule_count = max(rule_fail_counts.items(), key=lambda kv: kv[1])

            latest = max(group_inspections, key=lambda i: i.created_at)

            offenders.append(
                RepeatOffenderItem(
                    brand=latest.brand,  # display using the most recently entered casing
                    total_inspections=len(group_inspections),
                    fail_count=fail_count,
                    review_count=review_count,
                    top_violation_rule_id=top_rule_id,
                    top_violation_rule_name=top_rule_name,
                    top_violation_count=top_rule_count,
                    latest_inspection_id=str(latest.id),
                    latest_inspection_number=latest.inspection_number,
                    latest_inspection_date=latest.created_at.isoformat(),
                )
            )

        offenders.sort(key=lambda o: (o.fail_count, o.total_inspections), reverse=True)
        return offenders[:limit]
