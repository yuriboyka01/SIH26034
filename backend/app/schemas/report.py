"""
Phase 5: Report generation schemas.

Data structures for assembling and rendering compliance reports.
Phase 5 only presents Phase 4 data — it never evaluates compliance.
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel


class ReportRuleResult(BaseModel):
    """Single rule result for the report."""
    rule_id: str
    rule_name: str
    status: str  # PASS, FAIL, REVIEW, NOT_APPLICABLE
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    field: Optional[str] = None
    expected: str
    actual: Optional[str] = None
    source_reference: str
    evidence: Optional[Any] = None


class ReportProductInfo(BaseModel):
    """Product info section of the report."""
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


class ReportImageResult(BaseModel):
    """Compliance results for a single image within the report."""
    image_id: str
    overall_status: str
    total_rules_checked: int
    passed_count: int
    failed_count: int
    review_count: int
    not_applicable_count: int
    rule_results: List[ReportRuleResult] = []


class InspectionReportData(BaseModel):
    """Full compliance report data structure — assembled from Phase 4 results."""
    report_id: str
    inspection_id: str
    inspection_number: str
    inspection_date: str
    product_name: str
    brand: str
    overall_status: str  # aggregated: FAIL > REVIEW > PASS > NOT_ANALYSED
    product_info: Optional[ReportProductInfo] = None
    image_results: List[ReportImageResult] = []

    # Aggregated summary
    total_rules_checked: int = 0
    passed_count: int = 0
    failed_count: int = 0
    review_count: int = 0
    not_applicable_count: int = 0

    # Violations (failed rules only)
    violations: List[ReportRuleResult] = []

    # Report metadata
    generated_at: str
    engine_version: Optional[str] = None
    ruleset_version: Optional[str] = None
