"""
PDF Report Generation Service — Voice2Justice
==============================================
Generates professional, branded PDF reports for every complaint using
ReportLab.  Each report includes:

  - Voice2Justice branded header
  - Complaint number, user name, category, confidence, status, dates
  - Assigned department & AI-generated summary
  - QR code linking to the complaint tracking URL (graceful fallback)
  - SHA-256 document integrity hash

Caching:
  Reports are regenerated ONLY when the complaint's updated_at timestamp
  is newer than the existing PDF's modification time.

Usage:
    from services.pdf_service import generate_complaint_pdf
    pdf_path = generate_complaint_pdf(complaint_dict)
"""

import os
import hashlib
import logging
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable,
)

logger = logging.getLogger(__name__)

# ── Colour Palette (Voice2Justice indigo theme) ───────────────────────────
INDIGO_DARK   = colors.HexColor('#3730a3')
INDIGO        = colors.HexColor('#4f46e5')
INDIGO_LIGHT  = colors.HexColor('#e0e7ff')
SLATE_900     = colors.HexColor('#0f172a')
SLATE_700     = colors.HexColor('#334155')
SLATE_500     = colors.HexColor('#64748b')
SLATE_200     = colors.HexColor('#e2e8f0')
SLATE_50      = colors.HexColor('#f8fafc')
WHITE         = colors.white
BLUE_50       = colors.HexColor('#eff6ff')
BLUE_600      = colors.HexColor('#2563eb')
GREEN_600     = colors.HexColor('#16a34a')
RED_600       = colors.HexColor('#dc2626')
AMBER_600     = colors.HexColor('#d97706')

# ── Report output directory ───────────────────────────────────────────────
FLASK_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR  = os.path.join(FLASK_DIR, 'reports')


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_reports_dir() -> str:
    """Create the reports/ directory if it doesn't exist and return its path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR


def _generate_qr_image(data: str, size: int = 110):
    """
    Generate a QR code as a ReportLab Image flowable.
    Returns None if QR generation fails (graceful fallback).
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#4f46e5", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Image(buf, width=size, height=size)
    except Exception as exc:
        logger.warning("QR code generation failed (PDF will still be created): %s", exc)
        return None


def _priority_color(priority: str):
    return {'High': RED_600, 'Medium': AMBER_600, 'Low': GREEN_600}.get(priority, SLATE_700)


def _needs_regeneration(filepath: str, complaint: dict) -> bool:
    """Return True if the PDF does not exist or the complaint was updated since last generation."""
    if not os.path.isfile(filepath):
        return True
    try:
        pdf_mtime = os.path.getmtime(filepath)
        updated_at = complaint.get('updated_at') or complaint.get('created_at')
        if updated_at:
            # Parse SQLite timestamp: "2026-06-21 10:30:00"
            comp_ts = datetime.strptime(str(updated_at)[:19], "%Y-%m-%d %H:%M:%S").timestamp()
            return comp_ts > pdf_mtime
    except (ValueError, OSError) as exc:
        logger.debug("Regeneration check failed, will regenerate: %s", exc)
    return True  # When in doubt, regenerate


def _build_styles():
    """Build paragraph styles used across the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='BrandTitle', fontName='Helvetica-Bold', fontSize=22,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='BrandSubtitle', fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#c7d2fe'), alignment=TA_CENTER,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading', fontName='Helvetica-Bold', fontSize=13,
        textColor=INDIGO, spaceBefore=8 * mm, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name='FieldLabel', fontName='Helvetica-Bold', fontSize=9,
        textColor=SLATE_500, leading=12,
    ))
    styles.add(ParagraphStyle(
        name='FieldValue', fontName='Helvetica', fontSize=10,
        textColor=SLATE_900, leading=14,
    ))
    styles.add(ParagraphStyle(
        name='SummaryText', fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#1e3a8a'), leading=16,
        leftIndent=4 * mm, rightIndent=4 * mm,
        spaceBefore=2 * mm, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='NarrativeText', fontName='Helvetica-Oblique', fontSize=9.5,
        textColor=SLATE_700, leading=15,
        leftIndent=4 * mm, rightIndent=4 * mm,
        spaceBefore=2 * mm, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='FooterText', fontName='Helvetica', fontSize=8,
        textColor=SLATE_500, alignment=TA_CENTER,
    ))
    return styles


# ═══════════════════════════════════════════════════════════════════════════
#  Main Generator
# ═══════════════════════════════════════════════════════════════════════════

def generate_complaint_pdf(complaint: dict,
                           base_url: str = "http://127.0.0.1:5000",
                           force: bool = False) -> str:
    """
    Generate a professional PDF report for a complaint.

    Args:
        complaint:  dict with complaint fields from the database.
        base_url:   base URL for QR code tracking link.
        force:      if True, always regenerate even if cache is fresh.

    Returns:
        Absolute path to the generated PDF file.
    """
    reports_dir = _ensure_reports_dir()
    styles = _build_styles()

    # ── Extract fields ────────────────────────────────────────────────────
    complaint_id     = complaint.get('id', 0)
    complaint_number = complaint.get('complaint_number', f'VJ-0000-{complaint_id:04d}')
    user_name        = complaint.get('user_name', 'Anonymous')
    category         = complaint.get('category', 'N/A')
    confidence       = complaint.get('confidence_score', 0.0)
    status           = complaint.get('status', 'Received')
    created_at       = complaint.get('created_at', 'N/A')
    updated_at       = complaint.get('updated_at', created_at)
    department       = complaint.get('department', 'N/A')
    summary          = complaint.get('summary', 'No summary available.')
    text             = complaint.get('text', '')
    incident_type    = complaint.get('type', 'unknown')
    priority         = complaint.get('priority', 'Medium')
    sla              = complaint.get('sla', 'N/A')
    sections         = complaint.get('sections', 'N/A')
    submitted_to     = complaint.get('submitted_to', 'N/A')
    location         = complaint.get('location', 'N/A')

    # ── Filename: Voice2Justice_<complaint_number>.pdf ─────────────────────
    safe_number = str(complaint_number).replace('-', '_')
    filename = f"Voice2Justice_{safe_number}.pdf"
    filepath = os.path.join(reports_dir, filename)

    # ── Cache check ───────────────────────────────────────────────────────
    if not force and not _needs_regeneration(filepath, complaint):
        logger.info("PDF cache hit for %s — skipping regeneration", complaint_number)
        return filepath

    # ── Document integrity hash ───────────────────────────────────────────
    doc_hash = hashlib.sha256(
        f"{complaint_id}{complaint_number}{text}".encode('utf-8')
    ).hexdigest()[:16].upper()

    tracking_url = f"{base_url}/api/track/{complaint_id}"

    # ── Build Document ────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=15 * mm, bottomMargin=20 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Voice2Justice Report - {complaint_number}",
        author="Voice2Justice Automated System",
    )

    story = []

    # ── 1. Branded Header ─────────────────────────────────────────────────
    header_data = [
        [Paragraph(
            '<font face="Helvetica-Bold" size="22" color="white">'
            '&#9878;  VOICE2JUSTICE</font>',
            styles['BrandTitle']
        )],
        [Paragraph("Automated Citizen Grievance Intelligence Platform",
                    styles['BrandSubtitle'])],
        [Paragraph(
            f'<font face="Courier" size="8" color="#c7d2fe">'
            f'Report #{complaint_number}  &bull;  '
            f'Generated {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
            f'</font>',
            styles['BrandSubtitle']
        )],
    ]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), INDIGO_DARK),
        ('TOPPADDING',    (0, 0), (-1,  0), 14),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=3, color=INDIGO,
                             spaceAfter=6 * mm, spaceBefore=0))

    # ── 2. Document Type Banner ───────────────────────────────────────────
    doc_type = ('First Information Report (FIR)' if incident_type == 'crpc_crime'
                else 'Civic Issue Official Report')
    banner_style = ParagraphStyle(
        'DocTypeBanner', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, textColor=INDIGO,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=4 * mm,
    )
    story.append(Paragraph(f"&mdash; {doc_type.upper()} &mdash;", banner_style))

    # ── 3. Complaint Details Grid ─────────────────────────────────────────
    story.append(Paragraph("COMPLAINT DETAILS", styles['SectionHeading']))

    conf_pct = f"{confidence:.1%}" if isinstance(confidence, (int, float)) else str(confidence)

    status_colors = {
        'Received': BLUE_600, 'Under Review': AMBER_600,
        'Investigating': AMBER_600, 'In Progress': AMBER_600,
        'Resolved': GREEN_600, 'Closed': SLATE_500, 'Rejected': RED_600,
    }
    status_col = status_colors.get(status, SLATE_700)

    fields = [
        ('Complaint Number', complaint_number),
        ('User Name',        user_name),
        ('Category',         category),
        ('AI Confidence',    conf_pct),
        ('Status',           status),
        ('Priority',         priority),
        ('Created Date',     str(created_at)),
        ('Updated Date',     str(updated_at)),
        ('Department',       department),
        ('SLA',              sla),
        ('Location',         location),
        ('Submitted To',     submitted_to),
        ('Applicable Codes', sections),
    ]

    grid_data = []
    for i in range(0, len(fields), 2):
        row = []
        for j in range(2):
            if i + j < len(fields):
                label, value = fields[i + j]
                if label == 'Status':
                    val_para = Paragraph(
                        f'<font color="{status_col.hexval()}">{value}</font>',
                        styles['FieldValue'])
                elif label == 'Priority':
                    p_col = _priority_color(priority)
                    val_para = Paragraph(
                        f'<font color="{p_col.hexval()}"><b>{value}</b></font>',
                        styles['FieldValue'])
                else:
                    val_para = Paragraph(str(value), styles['FieldValue'])
                row.append(Paragraph(label.upper(), styles['FieldLabel']))
                row.append(val_para)
            else:
                row.extend([Paragraph('', styles['FieldLabel']),
                            Paragraph('', styles['FieldValue'])])
        grid_data.append(row)

    col_w = doc.width / 4
    detail_table = Table(grid_data, colWidths=[col_w * 0.9, col_w * 1.1,
                                                col_w * 0.9, col_w * 1.1])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), SLATE_50),
        ('GRID',          (0, 0), (-1, -1), 0.5, SLATE_200),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(detail_table)

    # ── 4. AI Summary ─────────────────────────────────────────────────────
    story.append(Paragraph("AI COMPLAINT SUMMARY", styles['SectionHeading']))
    summary_data = [[Paragraph(str(summary), styles['SummaryText'])]]
    summary_table = Table(summary_data, colWidths=[doc.width])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), BLUE_50),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)

    # ── 5. Verbatim Narrative ─────────────────────────────────────────────
    story.append(Paragraph("VERBATIM CITIZEN NARRATIVE", styles['SectionHeading']))
    narrative_data = [[Paragraph(str(text), styles['NarrativeText'])]]
    narrative_table = Table(narrative_data, colWidths=[doc.width])
    narrative_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), SLATE_50),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, SLATE_200),
    ]))
    story.append(narrative_table)

    # ── 6. QR Code & Signatures ───────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_200,
                             spaceAfter=4 * mm, spaceBefore=0))

    sig_left = Paragraph(
        '<font size="9"><b>Digital AI Signature</b></font><br/>'
        f'<font face="Courier" size="7" color="#64748b">V2J-{complaint_id}-{doc_hash}</font>',
        ParagraphStyle('SigL', parent=styles['FooterText'], alignment=TA_LEFT),
    )
    sig_right = Paragraph(
        '<font size="9"><b>Receiving Authority</b></font><br/>'
        f'<font size="8" color="#64748b">{submitted_to}</font>',
        ParagraphStyle('SigR', parent=styles['FooterText'], alignment=TA_RIGHT),
    )

    # QR code (non-fatal if it fails)
    qr_image = _generate_qr_image(tracking_url, size=100)

    if qr_image:
        footer_data = [[sig_left, qr_image, sig_right]]
        footer_widths = [doc.width * 0.35, doc.width * 0.3, doc.width * 0.35]
    else:
        # Fallback: two-column layout with tracking URL text instead
        qr_fallback = Paragraph(
            f'<font size="8" color="#64748b">Track: {tracking_url}</font>',
            ParagraphStyle('QRFallback', parent=styles['FooterText'], alignment=TA_CENTER),
        )
        footer_data = [[sig_left, qr_fallback, sig_right]]
        footer_widths = [doc.width * 0.35, doc.width * 0.3, doc.width * 0.35]

    footer_table = Table(footer_data, colWidths=footer_widths)
    footer_table.setStyle(TableStyle([
        ('ALIGN',  (0, 0), (0, 0), 'LEFT'),
        ('ALIGN',  (1, 0), (1, 0), 'CENTER'),
        ('ALIGN',  (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(footer_table)

    if qr_image:
        story.append(Paragraph(
            '<font size="8" color="#64748b">Scan to track complaint status</font>',
            styles['FooterText'],
        ))

    # Final disclaimer
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE_200,
                             spaceAfter=2 * mm, spaceBefore=0))
    story.append(Paragraph(
        f'<font size="7" color="#94a3b8">'
        f'This document was auto-generated by the Voice2Justice AI platform on '
        f'{datetime.now().strftime("%d %B %Y at %H:%M:%S")}. '
        f'Document hash: {doc_hash}'
        f'</font>',
        styles['FooterText'],
    ))

    # ── Build ─────────────────────────────────────────────────────────────
    doc.build(story)
    logger.info("PDF generated: %s", filepath)
    return filepath
