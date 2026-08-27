"""
Compliance module placeholder interfaces.

These abstract classes define the contracts for future Legal Metrology
compliance checking and reporting services.

Phase 4 will implement the ComplianceService.
Phase 5 will implement the ReportService.

DO NOT add fake/mock implementations. These are interface contracts only.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from uuid import UUID


class ComplianceService(ABC):
    """
    Interface for Legal Metrology compliance checking.

    Phase 4 will implement:
    - Declaration completeness validation
    - Font size compliance checks
    - Net quantity declaration validation
    - MRP declaration validation
    - Manufacturer information validation
    - Date marking validation
    - Language requirement checks
    """

    @abstractmethod
    def check_compliance(
        self, inspection_id: UUID, declarations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check extracted declarations against Legal Metrology rules.

        Args:
            inspection_id: UUID of the inspection.
            declarations: Extracted declaration fields from AI analysis.

        Returns:
            Compliance report with pass/fail for each rule and evidence references.
        """
        raise NotImplementedError("Phase 4: Compliance checking not yet implemented.")


class ReportService(ABC):
    """
    Interface for generating inspection reports.

    Phase 5 will implement:
    - PDF report generation
    - Evidence highlighting on images
    - Compliance summary
    - Detailed findings
    - Inspector notes
    """

    @abstractmethod
    def generate_report(self, inspection_id: UUID) -> bytes:
        """
        Generate a compliance report for an inspection.

        Args:
            inspection_id: UUID of the inspection.

        Returns:
            Report file bytes (PDF).
        """
        raise NotImplementedError("Phase 5: Report generation not yet implemented.")
