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


class DashboardAnalyticsResponse(BaseModel):
    """Complete dashboard payload."""
    kpis: ComplianceKPIs
    top_violations: List[ViolationSummaryItem]
    recent_inspections: List[RecentInspectionItem]
