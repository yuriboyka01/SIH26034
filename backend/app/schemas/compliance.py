"""
Phase 4 (+ Rule Engine v2): Compliance schemas for the Legal Metrology Rules Engine.
"""

from typing import List, Optional, Any
from pydantic import BaseModel
from enum import Enum


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ANALYSED = "NOT_ANALYSED"


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleCategory(str, Enum):
    """
    Report-facing grouping for findings. Deliberately a small, fixed set so the
    frontend can render a stable set of sections regardless of how many rules
    are registered in the engine.
    """
    MANDATORY_DECLARATIONS = "MANDATORY_DECLARATIONS"
    QUANTITY_UNITS = "QUANTITY_UNITS"
    PRICING_MRP = "PRICING_MRP"
    PRODUCT_SPECIFIC = "PRODUCT_SPECIFIC"
    PRESENTATION_LABEL = "PRESENTATION_LABEL"
    CONDITIONAL_ADDITIONAL = "CONDITIONAL_ADDITIONAL"


RULE_CATEGORY_LABELS = {
    RuleCategory.MANDATORY_DECLARATIONS: "Mandatory Declarations",
    RuleCategory.QUANTITY_UNITS: "Quantity & Units",
    RuleCategory.PRICING_MRP: "Pricing / MRP",
    RuleCategory.PRODUCT_SPECIFIC: "Product-Specific Requirements",
    RuleCategory.PRESENTATION_LABEL: "Presentation / Label Requirements",
    RuleCategory.CONDITIONAL_ADDITIONAL: "Additional / Conditional Checks",
}


class RuleResultSchema(BaseModel):
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    severity: RuleSeverity
    category: RuleCategory = RuleCategory.MANDATORY_DECLARATIONS
    message: str
    field: Optional[str] = None
    expected: str
    actual: Optional[str] = None
    # evidence structure matching the ProductInfo schema
    evidence: Optional[Any] = None
    source_reference: str
    # Rule engine v2 additions — all optional so older persisted rows still validate.
    confidence: Optional[float] = None
    remediation: Optional[str] = None


class CategorySummarySchema(BaseModel):
    """Aggregated counts for one report category — powers the grouped findings UI."""
    category: RuleCategory
    label: str
    passed_count: int = 0
    failed_count: int = 0
    review_count: int = 0
    not_applicable_count: int = 0
    total: int = 0


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
    # Rule engine v2: precomputed grouping so the frontend doesn't need to
    # duplicate category logic.
    category_breakdown: List[CategorySummarySchema] = []


class ComplianceResponse(BaseModel):
    inspection_id: str
    overall_status: ComplianceStatus
    reports: List[ComplianceReportSchema] = []
