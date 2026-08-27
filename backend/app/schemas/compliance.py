"""
Phase 4: Compliance schemas for the Legal Metrology Rules Engine.
"""

from typing import List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleResultSchema(BaseModel):
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    severity: RuleSeverity
    message: str
    field: Optional[str] = None
    expected: str
    actual: Optional[str] = None
    # evidence structure matching the ProductInfo schema
    evidence: Optional[Any] = None
    source_reference: str


class ComplianceReportSchema(BaseModel):
    inspection_id: str
    image_id: str
    overall_status: ComplianceStatus
    
    # Aggregated metrics
    total_rules_checked: int
    passed_count: int
    failed_count: int
    review_count: int
    not_applicable_count: int
    
    rule_results: List[RuleResultSchema] = []


class ComplianceResponse(BaseModel):
    inspection_id: str
    overall_status: ComplianceStatus
    reports: List[ComplianceReportSchema] = []
