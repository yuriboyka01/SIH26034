"""
Phase 5: Report generation service.

Generates PDF and DOCX reports from Phase 4 compliance data.
"""

import io
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.core.exceptions import NotFoundError, BadRequestError
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.compliance_repository import ComplianceRepository
from app.schemas.report import (
    InspectionReportData,
    ReportProductInfo,
    ReportImageResult,
    ReportRuleResult
)

# Status ordering as per requirements: FAIL > REVIEW > PASS > NOT_APPLICABLE
STATUS_PRIORITY = {
    "FAIL": 4,
    "REVIEW": 3,
    "PASS": 2,
    "NOT_APPLICABLE": 1,
    "NOT_ANALYSED": 0
}


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.insp_repo = InspectionRepository(db)
        self.comp_repo = ComplianceRepository(db)

    def generate_report_data(self, inspection_id: UUID, user_id: UUID) -> InspectionReportData:
        """Assembles the full compliance report data from the database."""
        inspection = self.insp_repo.get_by_id(inspection_id)
        if not inspection or inspection.created_by != user_id:
            raise NotFoundError(code="INSPECTION_NOT_FOUND", message="Inspection not found.")

        reports = self.comp_repo.get_reports_by_inspection_id(inspection_id)
        
        overall_inspection_status = "NOT_ANALYSED"
        
        total_rules = 0
        passed = 0
        failed = 0
        review = 0
        not_applicable = 0
        
        image_results = []
        violations = []
        
        # Determine engine and ruleset versions based on the first report, or default if empty
        engine_version = "1.0.0"
        ruleset_version = "LM-2011-v1"
        if reports:
            engine_version = reports[0].engine_version or "1.0.0"
            ruleset_version = reports[0].ruleset_version or "LM-2011-v1"
            
        product_info_data = ReportProductInfo()
        
        for rep in reports:
            # Aggregate status logic: FAIL > REVIEW > PASS > NOT_APPLICABLE
            if STATUS_PRIORITY.get(rep.overall_status, 0) > STATUS_PRIORITY.get(overall_inspection_status, 0):
                overall_inspection_status = rep.overall_status
                
            total_rules += rep.total_rules_checked
            passed += rep.passed_count
            failed += rep.failed_count
            review += rep.review_count
            not_applicable += rep.not_applicable_count
            
            # Map rule results
            rule_results_mapped = []
            for rr in rep.rule_results:
                mapped_rr = ReportRuleResult(
                    rule_id=rr.rule_id,
                    rule_name=rr.rule_name,
                    status=rr.status,
                    severity=rr.severity,
                    message=rr.message,
                    field=rr.field,
                    expected=rr.expected,
                    actual=rr.actual,
                    source_reference=rr.source_reference,
                    evidence=rr.get_evidence()
                )
                rule_results_mapped.append(mapped_rr)
                if rr.status == "FAIL":
                    violations.append(mapped_rr)
                    
            image_results.append(
                ReportImageResult(
                    image_id=str(rep.ocr_result.image_id),
                    overall_status=rep.overall_status,
                    total_rules_checked=rep.total_rules_checked,
                    passed_count=rep.passed_count,
                    failed_count=rep.failed_count,
                    review_count=rep.review_count,
                    not_applicable_count=rep.not_applicable_count,
                    rule_results=rule_results_mapped
                )
            )
            
            # Populate product info if available
            if rep.ocr_result and rep.ocr_result.product_info:
                pinfo = rep.ocr_result.product_info
                # Only take first non-null values if multiple images
                product_info_data.product_name = product_info_data.product_name or pinfo.product_name
                product_info_data.brand_name = product_info_data.brand_name or pinfo.brand_name
                product_info_data.manufacturer = product_info_data.manufacturer or pinfo.manufacturer
                product_info_data.net_quantity = product_info_data.net_quantity or pinfo.net_quantity
                product_info_data.mrp = product_info_data.mrp or pinfo.mrp
                product_info_data.manufacturing_date = product_info_data.manufacturing_date or pinfo.manufacturing_date
                product_info_data.expiry_date = product_info_data.expiry_date or pinfo.expiry_date
                product_info_data.batch_number = product_info_data.batch_number or pinfo.batch_number
                product_info_data.country_of_origin = product_info_data.country_of_origin or pinfo.country_of_origin
                product_info_data.ingredients = product_info_data.ingredients or pinfo.ingredients
                product_info_data.license_number = product_info_data.license_number or pinfo.license_number
                product_info_data.customer_care = product_info_data.customer_care or pinfo.customer_care

        return InspectionReportData(
            report_id=f"REP-{inspection.inspection_number}",
            inspection_id=str(inspection_id),
            inspection_number=inspection.inspection_number,
            inspection_date=inspection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            product_name=inspection.product_name,
            brand=inspection.brand,
            overall_status=overall_inspection_status,
            product_info=product_info_data,
            image_results=image_results,
            total_rules_checked=total_rules,
            passed_count=passed,
            failed_count=failed,
            review_count=review,
            not_applicable_count=not_applicable,
            violations=violations,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            engine_version=engine_version,
            ruleset_version=ruleset_version
        )

    def render_pdf(self, report_data: InspectionReportData) -> bytes:
        """Generates a PDF report using reportlab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=inch, 
            leftMargin=inch, 
            topMargin=inch, 
            bottomMargin=inch
        )
        
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        h2_style = styles['Heading2']
        h3_style = styles['Heading3']
        normal_style = styles['Normal']
        
        bold_style = ParagraphStyle(
            'BoldStyle',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )
        
        elements = []
        
        # Header
        elements.append(Paragraph("SIH26034 COMPLIANCE INSPECTION REPORT", title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Inspection Info
        elements.append(Paragraph("Inspection Information", h2_style))
        info_data = [
            ["Inspection ID:", report_data.inspection_number],
            ["Date:", report_data.inspection_date],
            ["Product:", f"{report_data.product_name} ({report_data.brand})"],
            ["Overall Status:", report_data.overall_status]
        ]
        info_table = Table(info_data, colWidths=[1.5*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.25 * inch))
        
        # Summary
        elements.append(Paragraph("SUMMARY", h2_style))
        summary_data = [
            ["Rules Checked:", str(report_data.total_rules_checked)],
            ["Passed:", str(report_data.passed_count)],
            ["Failed:", str(report_data.failed_count)],
            ["Review:", str(report_data.review_count)],
            ["Not Applicable:", str(report_data.not_applicable_count)]
        ]
        summary_table = Table(summary_data, colWidths=[1.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25 * inch))
        
        # Product Information
        elements.append(Paragraph("PRODUCT INFORMATION", h2_style))
        pinfo = report_data.product_info
        if pinfo:
            p_data = []
            if pinfo.product_name: p_data.append(["Product Name:", pinfo.product_name])
            if pinfo.net_quantity: p_data.append(["Net Quantity:", pinfo.net_quantity])
            if pinfo.mrp: p_data.append(["MRP:", pinfo.mrp])
            if pinfo.manufacturer: p_data.append(["Manufacturer:", pinfo.manufacturer])
            if pinfo.manufacturing_date: p_data.append(["Manufacturing Date:", pinfo.manufacturing_date])
            if pinfo.customer_care: p_data.append(["Consumer Care:", pinfo.customer_care])
            
            if p_data:
                # Need Paragraphs to wrap long texts
                wrapped_p_data = [[Paragraph(row[0], bold_style), Paragraph(row[1], normal_style)] for row in p_data]
                p_table = Table(wrapped_p_data, colWidths=[1.5*inch, 4.5*inch])
                p_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ]))
                elements.append(p_table)
            else:
                elements.append(Paragraph("No product information extracted.", normal_style))
        else:
            elements.append(Paragraph("No product information available.", normal_style))
            
        elements.append(Spacer(1, 0.25 * inch))
        
        # Violations
        elements.append(Paragraph("VIOLATIONS", h2_style))
        if report_data.violations:
            for viol in report_data.violations:
                elements.append(Paragraph(f"{viol.rule_id}: {viol.rule_name}", h3_style))
                v_data = [
                    ["Status:", viol.status],
                    ["Severity:", viol.severity],
                    ["Message:", viol.message]
                ]
                wrapped_v = [[Paragraph(row[0], bold_style), Paragraph(str(row[1]), normal_style)] for row in v_data]
                v_table = Table(wrapped_v, colWidths=[1*inch, 5*inch])
                v_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
                elements.append(v_table)
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph("No violations found.", normal_style))
            
        elements.append(Spacer(1, 0.25 * inch))
        
        # Rule Results Details
        elements.append(Paragraph("RULE RESULTS DETAILS", h2_style))
        for img_res in report_data.image_results:
            for rr in img_res.rule_results:
                elements.append(Paragraph(f"{rr.rule_id} - {rr.rule_name}", h3_style))
                
                rr_data = [
                    ["Status:", rr.status],
                    ["Expected:", rr.expected],
                    ["Actual:", rr.actual if rr.actual else "Not detected"],
                ]
                
                wrapped_rr = [[Paragraph(row[0], bold_style), Paragraph(str(row[1]), normal_style)] for row in rr_data]
                rr_table = Table(wrapped_rr, colWidths=[1*inch, 5*inch])
                rr_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
                elements.append(rr_table)
                
                elements.append(Spacer(1, 0.05 * inch))
                elements.append(Paragraph("EVIDENCE", bold_style))
                
                if rr.evidence and rr.evidence.get("source_text"):
                    evidence_text = f"Source Text: {rr.evidence.get('source_text')} (Confidence: {rr.evidence.get('confidence', 0):.2f})"
                    if rr.evidence.get("bbox"):
                        evidence_text += f"\nBBox: {rr.evidence.get('bbox')}"
                    elements.append(Paragraph(evidence_text.replace("\n", "<br/>"), normal_style))
                else:
                    elements.append(Paragraph("No evidence available.", normal_style))
                    
                elements.append(Spacer(1, 0.15 * inch))
                
        # Metadata
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("REPORT METADATA", h2_style))
        meta_data = [
            ["Generated At:", report_data.generated_at],
            ["Ruleset Version:", report_data.ruleset_version or "N/A"],
            ["Engine Version:", report_data.engine_version or "N/A"]
        ]
        meta_table = Table(meta_data, colWidths=[1.5*inch, 4.5*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(meta_table)

        doc.build(elements)
        return buffer.getvalue()

    def render_docx(self, report_data: InspectionReportData) -> bytes:
        """Generates a DOCX report using python-docx."""
        doc = docx.Document()
        
        # Title
        title = doc.add_heading('SIH26034 COMPLIANCE INSPECTION REPORT', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Inspection Info
        doc.add_heading('Inspection Information', level=1)
        doc.add_paragraph(f"Inspection ID: {report_data.inspection_number}")
        doc.add_paragraph(f"Date: {report_data.inspection_date}")
        doc.add_paragraph(f"Product: {report_data.product_name} ({report_data.brand})")
        doc.add_paragraph(f"Overall Status: {report_data.overall_status}")
        
        # Summary
        doc.add_heading('SUMMARY', level=1)
        doc.add_paragraph(f"Rules Checked: {report_data.total_rules_checked}")
        doc.add_paragraph(f"Passed: {report_data.passed_count}")
        doc.add_paragraph(f"Failed: {report_data.failed_count}")
        doc.add_paragraph(f"Review: {report_data.review_count}")
        doc.add_paragraph(f"Not Applicable: {report_data.not_applicable_count}")
        
        # Product Information
        doc.add_heading('PRODUCT INFORMATION', level=1)
        pinfo = report_data.product_info
        if pinfo:
            if pinfo.product_name: doc.add_paragraph(f"Product Name: {pinfo.product_name}")
            if pinfo.net_quantity: doc.add_paragraph(f"Net Quantity: {pinfo.net_quantity}")
            if pinfo.mrp: doc.add_paragraph(f"MRP: {pinfo.mrp}")
            if pinfo.manufacturer: doc.add_paragraph(f"Manufacturer: {pinfo.manufacturer}")
            if pinfo.manufacturing_date: doc.add_paragraph(f"Manufacturing Date: {pinfo.manufacturing_date}")
            if pinfo.customer_care: doc.add_paragraph(f"Consumer Care: {pinfo.customer_care}")
        else:
            doc.add_paragraph("No product information available.")
            
        # Violations
        doc.add_heading('VIOLATIONS', level=1)
        if report_data.violations:
            for viol in report_data.violations:
                doc.add_heading(f"{viol.rule_id}: {viol.rule_name}", level=2)
                doc.add_paragraph(f"Status: {viol.status}")
                doc.add_paragraph(f"Severity: {viol.severity}")
                doc.add_paragraph(f"Message: {viol.message}")
        else:
            doc.add_paragraph("No violations found.")
            
        # Rule Results Details
        doc.add_heading('RULE RESULTS DETAILS', level=1)
        for img_res in report_data.image_results:
            for rr in img_res.rule_results:
                doc.add_heading(f"{rr.rule_id} - {rr.rule_name}", level=2)
                doc.add_paragraph(f"Status: {rr.status}")
                doc.add_paragraph(f"Expected: {rr.expected}")
                doc.add_paragraph(f"Actual: {rr.actual if rr.actual else 'Not detected'}")
                
                # Evidence
                evidence_p = doc.add_paragraph()
                evidence_p.add_run('EVIDENCE\n').bold = True
                
                if rr.evidence and rr.evidence.get("source_text"):
                    evidence_p.add_run(f"Source Text: {rr.evidence.get('source_text')} (Confidence: {rr.evidence.get('confidence', 0):.2f})\n")
                    if rr.evidence.get("bbox"):
                        evidence_p.add_run(f"BBox: {rr.evidence.get('bbox')}")
                else:
                    evidence_p.add_run("No evidence available.")
                    
        # Metadata
        doc.add_heading('REPORT METADATA', level=1)
        doc.add_paragraph(f"Generated At: {report_data.generated_at}")
        doc.add_paragraph(f"Ruleset Version: {report_data.ruleset_version or 'N/A'}")
        doc.add_paragraph(f"Engine Version: {report_data.engine_version or 'N/A'}")
        
        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
