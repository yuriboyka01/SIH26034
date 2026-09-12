"""
Phase 5: Dashboard reporting and analytics schemas.
"""

from typing import List, Optional
from pydantic import BaseModel


class ComplianceKPIs(BaseModel):
    """Key performance indicators for compliance."""
    total_inspections: int
    compliant_count: int
    non_compliant_count: int
    review_count: int
    not_analysed_count: int
    compliance_rate: float


class ViolationSummaryItem(BaseModel):
    """Aggregate count of a specific rule violation."""
    rule_id: str
    rule_name: str
    count: int


class RecentInspectionItem(BaseModel):
    """Summary of a recent inspection including compliance status."""
    id: str
    inspection_number: str
    product_name: str
    brand: str
    created_at: str
    compliance_status: str  # PASS, FAIL, REVIEW, NOT_ANALYSED


class RepeatOffenderItem(BaseModel):
    """
    A brand with a pattern of repeated compliance failures across separate
    inspections (not separate photos of the same inspection — see
    DashboardService for how per-inspection status is merged before this
    is computed).
    """
    brand: str
    total_inspections: int
    fail_count: int
    review_count: int
    top_violation_rule_id: Optional[str] = None
    top_violation_rule_name: Optional[str] = None
    top_violation_count: int = 0
    latest_inspection_id: str
    latest_inspection_number: str
    latest_inspection_date: str


class GeoPointItem(BaseModel):
    """One geo-tagged inspection, for the violation map. Status is the same
    merged, per-inspection verdict used everywhere else on the dashboard."""
    inspection_id: str
    inspection_number: str
    brand: str
    product_name: str
    establishment_name: Optional[str] = None
    latitude: float
    longitude: float
    compliance_status: str


class DashboardAnalyticsResponse(BaseModel):
    """Complete dashboard payload."""
    kpis: ComplianceKPIs
    top_violations: List[ViolationSummaryItem]
    recent_inspections: List[RecentInspectionItem]
    repeat_offenders: List[RepeatOffenderItem] = []
    geo_points: List[GeoPointItem] = []
