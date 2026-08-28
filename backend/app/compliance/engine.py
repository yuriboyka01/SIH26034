"""
Phase 4: Compliance Engine
Orchestrates the evaluation of all registered rules against extracted product information.
"""

from typing import List, Dict, Any

from app.schemas.compliance import (
    ComplianceStatus,
    ComplianceReportSchema,
    RuleResultSchema,
    RuleSeverity
)
from app.compliance.rules import REGISTERED_RULES

# Auditable version constants
ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "LM-2011-v1"


class ComplianceRuleEngine:
    """
    Evaluates Legal Metrology Rules against extracted fields.
    """
    
    def __init__(self):
        self.rules = REGISTERED_RULES

    def evaluate(self, inspection_id: str, image_id: str, extracted_fields: List[Dict[str, Any]]) -> ComplianceReportSchema:
        """
        Run all registered rules against the extracted fields.
        Returns a complete ComplianceReportSchema.
        """
        results: List[RuleResultSchema] = []
        
        passed = 0
        failed = 0
        review = 0
        not_applicable = 0
        
        has_high_critical_fail = False
        
        for rule in self.rules:
            result = rule.evaluate(extracted_fields)
            results.append(result)
            
            if result.status == ComplianceStatus.PASS:
                passed += 1
            elif result.status == ComplianceStatus.FAIL:
                failed += 1
                if result.severity in [RuleSeverity.CRITICAL, RuleSeverity.HIGH]:
                    has_high_critical_fail = True
            elif result.status == ComplianceStatus.REVIEW:
                review += 1
            elif result.status == ComplianceStatus.NOT_APPLICABLE:
                not_applicable += 1

        # Determine overall status
        if has_high_critical_fail:
            overall_status = ComplianceStatus.FAIL
        elif review > 0:
            overall_status = ComplianceStatus.REVIEW
        elif failed > 0:
            overall_status = ComplianceStatus.REVIEW  # Only fail outright on HIGH/CRITICAL
        else:
            overall_status = ComplianceStatus.PASS

        return ComplianceReportSchema(
            inspection_id=inspection_id,
            image_id=image_id,
            overall_status=overall_status,
            total_rules_checked=len(self.rules),
            passed_count=passed,
            failed_count=failed,
            review_count=review,
            not_applicable_count=not_applicable,
            rule_results=results
        )
