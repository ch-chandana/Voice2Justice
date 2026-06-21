"""
Report routes
=============
  GET /report/<complaint_id>     — render a printable HTML report with a PDF download button
  GET /report/<complaint_id>/pdf — generate and download a professional PDF report

Security fixes applied vs. original:
  - All database values are HTML-escaped via markupsafe.escape() before injection
  - SHA-256 (hashlib) replaces Python's insecure hash() for the document integrity hash
"""
import os
import hashlib
from flask import Blueprint, send_file, request
from markupsafe import escape

from models.complaint import ComplaintModel
from services.pdf_service import generate_complaint_pdf

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/report/<int:complaint_id>')
def generate_report(complaint_id):
    comp = ComplaintModel.get(complaint_id)

    if not comp:
        return 'Complaint not found', 404

    doc_type = (
        'First Information Report (FIR)'
        if comp['type'] == 'crpc_crime'
        else 'Civic Issue Official Report'
    )

    # SECURITY FIX: SHA-256 replaces Python's hash() which is non-cryptographic,
    # process-scoped, and produces collisions — unsuitable for document signatures.
    doc_hash = hashlib.sha256(
        comp['text'].encode('utf-8')
    ).hexdigest()[:16].upper()

    # SECURITY FIX: escape every DB field before injecting into HTML
    safe = {
        k: str(escape(str(v))) if v is not None else ''
        for k, v in comp.items()
    }

    # Priority colour is derived from a controlled DB enum — safe to compare directly
    priority_colour = '#dc2626' if comp['priority'] == 'High' else '#d97706'

    # PDF filename uses safe (escaped) values
    pdf_filename = f"Report_{safe['type']}_{safe['id']}.pdf"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Report - #{safe['id']}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; padding: 20px; background: #e2e8f0; margin: 0; color: #1e293b; }}
        .document {{ background: white; padding: 50px; max-width: 800px; margin: 0 auto;
                     box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #4f46e5; border-radius: 4px; }}
        .header {{ text-align: center; border-bottom: 2px solid #cbd5e1; padding-bottom: 20px; margin-bottom: 30px; }}
        .title {{ font-size: 28px; font-weight: 800; margin-bottom: 5px; text-transform: uppercase;
                  letter-spacing: 1px; color: #0f172a; }}
        .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 10px; }}
        .meta {{ font-size: 13px; color: #475569; font-family: monospace; }}
        .grid {{ display: grid; grid-template-columns: 180px 1fr; gap: 15px; margin-bottom: 30px;
                 background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }}
        .label {{ font-weight: 700; color: #334155; text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px; }}
        .value {{ color: #0f172a; font-weight: 500; }}
        .section-title {{ font-size: 18px; font-weight: 700; margin-top: 40px; margin-bottom: 15px;
                          color: #1e293b; display: flex; align-items: center; gap: 10px; }}
        .section-title::after {{ content: ''; flex: 1; height: 1px; background: #e2e8f0; }}
        .summary-box {{ line-height: 1.7; background: #eff6ff; padding: 20px;
                        border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0;
                        font-size: 15px; color: #1e3a8a; }}
        .narrative-box {{ line-height: 1.7; white-space: pre-wrap; font-style: italic; color: #475569;
                          padding: 20px; background: #f1f5f9; border-radius: 8px; border: 1px solid #e2e8f0; }}
        .top-bar {{ display: flex; justify-content: center; margin-bottom: 20px; }}
        .btn-download {{ display: inline-flex; align-items: center; justify-content: center; gap: 10px;
                         padding: 12px 24px; background: #4f46e5; color: white; border: none; cursor: pointer;
                         font-size: 16px; border-radius: 30px; font-weight: 600;
                         box-shadow: 0 4px 12px rgba(79,70,229,0.3); transition: all 0.2s; }}
        .btn-download:hover {{ background: #4338ca; transform: translateY(-2px); }}
        .footer-sig {{ margin-top: 60px; display: flex; justify-content: space-between; }}
        .sig-block {{ text-align: center; color: #64748b; font-size: 14px; }}
        .sig-line {{ border-top: 1px solid #94a3b8; width: 200px; margin-bottom: 10px; }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .document {{ box-shadow: none; padding: 0; max-width: 100%; border-top: none; }}
            .top-bar {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="top-bar" id="no-print">
        <button class="btn-download" onclick="downloadPDF()">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            Save as Official PDF
        </button>
    </div>

    <div class="document" id="pdf-content">
        <div class="header">
            <div class="title">{doc_type}</div>
            <div class="subtitle">Automated Intelligence Routing System - Voice2Justice</div>
            <div class="meta">Doc ID: {safe['type'].upper()}-{safe['id']} &nbsp;&bull;&nbsp; Generated: {safe['created_at']}</div>
        </div>

        <div class="section-title">Routing Protocol</div>
        <div class="grid">
            <div class="label">Complaint Category:</div>
            <div class="value">{safe['category']}</div>

            <div class="label">Location:</div>
            <div class="value">{safe['location']}</div>

            <div class="label">Routing Department:</div>
            <div class="value">{safe['department']}</div>

            <div class="label">Priority Level:</div>
            <div class="value" style="color: {priority_colour}; font-weight: 700;">{safe['priority']}</div>

            <div class="label">Expected SLA:</div>
            <div class="value">{safe['sla']}</div>

            <div class="label">Submitted To:</div>
            <div class="value">{safe['submitted_to']}</div>

            <div class="label">Applicable Codes:</div>
            <div class="value">{safe['sections']}</div>
        </div>

        <div class="section-title">AI Complaint Extracted Summary</div>
        <div class="summary-box">{safe['summary']}</div>

        <div class="section-title">Verbatim Citizen Narrative</div>
        <div class="narrative-box">{safe['text']}</div>

        <div class="footer-sig">
            <div class="sig-block">
                <div class="sig-line"></div>
                <p>Digital AI Signature</p>
                <p style="font-size: 11px; font-family: monospace;">Hash: V2J-{safe['id']}-{doc_hash}</p>
            </div>
            <div class="sig-block">
                <div class="sig-line"></div>
                <p>Receiving Authority</p>
                <p style="font-size: 11px;">{safe['submitted_to']}</p>
            </div>
        </div>
    </div>

    <script>
        function downloadPDF() {{
            const element = document.getElementById('pdf-content');
            const btn = document.querySelector('.btn-download');
            btn.innerHTML = 'Generating PDF...';
            btn.style.opacity = '0.7';

            const opt = {{
                margin:      10,
                filename:    '{pdf_filename}',
                image:       {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{ scale: 2, useCORS: true }},
                jsPDF:       {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};

            html2pdf().set(opt).from(element).save().then(() => {{
                btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                    + '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>'
                    + '</svg> Downloaded Successfully';
                setTimeout(() => {{
                    btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                        + '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"'
                        + ' d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>'
                        + '</svg> Save as Official PDF';
                    btn.style.opacity = '1';
                }}, 3000);
            }});
        }}
    </script>
</body>
</html>"""
    return html


@reports_bp.route('/report/<int:complaint_id>/pdf')
def download_pdf(complaint_id):
    """Generate (or serve cached) PDF report and return as a download."""
    comp = ComplaintModel.get(complaint_id)
    if not comp:
        return 'Complaint not found', 404

    # Derive base URL from the incoming request
    base_url = request.host_url.rstrip('/')

    try:
        pdf_path = generate_complaint_pdf(dict(comp), base_url=base_url)
    except Exception as e:
        return f'PDF generation failed: {e}', 500

    if not os.path.isfile(pdf_path):
        return 'PDF file not found after generation', 500

    filename = os.path.basename(pdf_path)
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )

