"""
Phase 5: Reports API Routes.

GET /api/inspections/{id}/compliance/report.pdf
GET /api/inspections/{id}/compliance/report.docx
"""

from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/inspections", tags=["Reports"])


@router.get("/{inspection_id}/compliance/report.pdf")
def download_pdf_report(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a PDF compliance report."""
    service = ReportService(db)
    report_data = service.generate_report_data(inspection_id, current_user.id)
    pdf_bytes = service.render_pdf(report_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Compliance_Report_{report_data.inspection_number}.pdf"'
        }
    )


@router.get("/{inspection_id}/compliance/report.docx")
def download_docx_report(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a DOCX compliance report."""
    service = ReportService(db)
    report_data = service.generate_report_data(inspection_id, current_user.id)
    docx_bytes = service.render_docx(report_data)
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="Compliance_Report_{report_data.inspection_number}.docx"'
        }
    )


@router.get("/{inspection_id}/show-cause/report.pdf")
def download_show_cause_pdf(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a Show-Cause Notice PDF (DRAFT)."""
    service = ReportService(db)
    report_data = service.generate_report_data(inspection_id, current_user.id)
    pdf_bytes = service.render_show_cause_pdf(report_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="SCN-{report_data.inspection_number}.pdf"'
        }
    )


@router.get("/{inspection_id}/show-cause/report.docx")
def download_show_cause_docx(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a Show-Cause Notice DOCX (DRAFT)."""
    service = ReportService(db)
    report_data = service.generate_report_data(inspection_id, current_user.id)
    docx_bytes = service.render_show_cause_docx(report_data)
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="SCN-{report_data.inspection_number}.docx"'
        }
    )
