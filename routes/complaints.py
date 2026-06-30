"""
Complaint routes
================
  POST /api/process              — submit and classify a new complaint
  GET  /api/complaints           — list all complaints (admin view)
  GET  /api/track/<complaint_id> — track the status of a single complaint

Step 3: All classification logic delegated to services/classifier.py,
        email sending delegated to services/email_service.py.
"""
import os
import sqlite3

from flask import Blueprint, request, jsonify
from markupsafe import escape

from config import DB_PATH
from services.classifier import classify_complaint, extract_location, build_summary
from services.email_service import send_complaint_email
from models.complaint import ComplaintModel
from routes.auth import admin_required

complaints_bp = Blueprint('complaints', __name__)


import logging
from extensions import limiter

logger = logging.getLogger(__name__)

# ── Routes ───────────────────────────────────────────────────────────────

@complaints_bp.route('/api/process', methods=['POST'])
@limiter.limit("5 per minute", error_message="You are submitting complaints too quickly. Please wait a moment.")
def process_complaint():
    try:
        return _process_complaint_inner()
    except Exception as e:
        logger.error("Unhandled error in /api/process: %s", e, exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred. Please try again.'
        }), 500


def _process_complaint_inner():
    # BUG FIX: use silent=True so malformed JSON returns 400 instead of crashing
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid or missing JSON body'}), 400

    text = data.get('text', '').strip()
    gps_location = data.get('location', '')

    if not text:
        return jsonify({'status': 'error', 'message': 'No complaint text provided'}), 400

    # Sanitize input for XSS protection
    safe_text = str(escape(text))
    text_lower = text.lower()

    # Extract location from complaint text (delegated to classifier service)
    extracted = extract_location(text)
    if extracted:
        final_location = str(escape(extracted))
    else:
        final_location = str(escape(gps_location)) if gps_location else ''

    if not final_location or any(
        word in final_location.lower()
        for word in ('denied', 'unavailable', 'not supported')
    ):
        return jsonify({
            'status': 'error',
            'message': (
                'Location access is mandatory. Please enable GPS '
                'or specify a location in your complaint.'
            )
        }), 400

    # 1. Classifier Agent (delegated to classifier service)
    result = classify_complaint(text_lower)

    incident_type = result['incident_type']
    category      = result['category']
    sections      = result['sections']
    department    = result['department']
    priority      = result['priority']
    sla           = result['sla']
    submitted_to  = result['submitted_to']
    target_email  = os.environ.get(result['target_email_key'], '')
    confidence    = result.get('confidence', 0.0)

    # Build AI summary (delegated to classifier service)
    summary = build_summary(incident_type, category, safe_text[:100])

    # ── Fraud Scoring ─────────────────────────────────────────────────────
    # Calculate fraud_score (0.0 to 1.0) based on behavioral signals.
    # All complaints are STORED regardless of score — never auto-rejected.
    from flask import session as flask_session

    submitted_ip = request.remote_addr
    user_id = flask_session.get('user_id')
    
    guest_name = None
    guest_email = None
    guest_phone = None
    user_type = 'Registered'

    if user_id:
        verification_status = 'Verified'
    else:
        user_type = 'Guest'
        verification_status = 'Unverified'
        guest_name = data.get('guest_name', '').strip()
        guest_email = data.get('guest_email', '').strip()
        guest_phone = data.get('guest_phone', '').strip()
        
        if not guest_name or not guest_email or not guest_phone:
            return jsonify({
                'status': 'error',
                'message': 'Guest users must provide Full Name, Email, and Phone Number.'
            }), 400

    fraud_score = 0.0

    # Signal 1: Excessive submissions from same IP in last hour (+0.4)
    ip_count = ComplaintModel.count_recent_by_ip(submitted_ip, hours=1)
    if ip_count >= 5:
        fraud_score += 0.4

    # Signal 2: Excessive submissions from same user in last hour (+0.3)
    if user_id:
        user_count = ComplaintModel.count_recent_by_user(user_id, hours=1)
        if user_count >= 5:
            fraud_score += 0.3

    # Signal 3: Identical complaint text previously submitted (+0.5)
    if ComplaintModel.check_duplicate_text(text):
        fraud_score += 0.5

    # Signal 4: Extremely low ML confidence score (+0.2)
    if confidence < 0.3:
        fraud_score += 0.2

    # Cap at 1.0
    fraud_score = min(fraud_score, 1.0)

    # Determine fraud status (never reject — just flag)
    if fraud_score >= 0.7:
        fraud_status = 'Suspicious'
    elif fraud_score >= 0.4:
        fraud_status = 'Review Required'
    else:
        fraud_status = 'Clean'

    # 2. Save to SQLite via ComplaintModel
    comp_data = {
        'user_name': None,
        'text': text,
        'type': incident_type,
        'category': category,
        'confidence_score': confidence,
        'department': department,
        'priority': priority,
        'sla': sla,
        'summary': summary,
        'sections': sections,
        'submitted_to': submitted_to,
        'location': final_location,
        'user_id': user_id,
        'verification_status': verification_status,
        'submitted_ip': submitted_ip,
        'fraud_score': round(fraud_score, 2),
        'fraud_status': fraud_status,
        'guest_name': guest_name,
        'guest_email': guest_email,
        'guest_phone': guest_phone,
        'user_type': user_type
    }
    complaint_id = ComplaintModel.create(comp_data)
    
    comp = ComplaintModel.get(complaint_id)
    complaint_number = comp['complaint_number']
    
    logger.info(f"Complaint successfully processed: ID={complaint_id}, Category='{category}', Priority='{priority}', FraudScore={fraud_score:.2f}, FraudStatus='{fraud_status}'")

    # 3. Build response card HTML
    pdf_btn_html = (
        f'<button class="btn btn-primary" '
        f'onclick="window.open(\'/report/{complaint_id}\', \'_blank\')" '
        f'style="width:100%;margin-top:1rem;font-size:0.85rem;padding:0.5rem;'
        f'display:flex;align-items:center;justify-content:center;gap:0.5rem;'
        f'border:none;cursor:pointer;">'
        f'<i class="fa-solid fa-file-pdf"></i> Generate &amp; Download PDF Report'
        f'</button>'
    )

    email_status_text = f"\u2714 Auto-Routed to: {target_email}"

    if incident_type == 'crpc_crime':
        result_html = f'''
        <div class="result-card">
            <div class="result-header">
                <span style="font-family:monospace;color:var(--text-muted);">
                    <i class="fa-solid fa-file-pdf"></i> FIR_Draft_{complaint_number}
                </span>
                <span class="result-tag tag-crime">Criminal Incident</span>
            </div>
            <div class="result-row">
                <div class="result-label">Category</div>
                <div class="result-value">{category}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Location</div>
                <div class="result-value" style="font-size: 0.85rem;">{final_location}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Applicable Codes</div>
                <div class="result-value" style="font-weight:600; font-size: 0.85rem;">{sections}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Department</div>
                <div class="result-value" style="font-weight:700;">{department}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Assigned To</div>
                <div class="result-value" style="font-size: 0.85rem;">{submitted_to}</div>
            </div>
            <div class="result-row">
                <div class="result-label">AI Confidence</div>
                <div class="result-value" style="font-size: 0.85rem;">{confidence:.1%}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Email Routed</div>
                <div class="result-value" style="color:#10b981; font-size: 0.85rem;">{email_status_text}</div>
            </div>
            {pdf_btn_html}
        </div>'''
    else:
        result_html = f'''
        <div class="result-card">
            <div class="result-header">
                <span style="font-family:monospace;color:var(--text-muted);">
                    <i class="fa-solid fa-ticket"></i> Ticket_{complaint_number}
                </span>
                <span class="result-tag tag-civic">Civic Issue</span>
            </div>
            <div class="result-row">
                <div class="result-label">Category</div>
                <div class="result-value">{category}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Location</div>
                <div class="result-value" style="font-size: 0.85rem;">{final_location}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Applicable Codes</div>
                <div class="result-value" style="font-weight:600; font-size: 0.85rem;">{sections}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Department</div>
                <div class="result-value" style="font-weight:700;color:#0ea5e9;">{department}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Assigned To</div>
                <div class="result-value" style="font-size: 0.85rem;">{submitted_to}</div>
            </div>
            <div class="result-row">
                <div class="result-label">AI Confidence</div>
                <div class="result-value" style="font-size: 0.85rem;">{confidence:.1%}</div>
            </div>
            <div class="result-row">
                <div class="result-label">Email Routed</div>
                <div class="result-value" style="color:#10b981; font-size: 0.85rem;">{email_status_text}</div>
            </div>
            {pdf_btn_html}
        </div>'''

    # 4. Send email notification (delegated to email service)
    send_complaint_email(
        target_email, complaint_id, category, text,
        summary, sections, final_location
    )

    # 5. Pipeline steps for frontend animation
    pipeline_steps = [
        'Initializing Flask Agent Platform...',
        '[Agent Extractor] Parsing entities...',
        '[Agent Classifier] Determining issue type...',
        f"[Agent Mapper] Mapping to {'Legal Codes' if incident_type == 'crpc_crime' else 'Civic Directory'}...",
        '[Agent Router] Generating structured payload...',
        f'[Database] Saved as complaint {complaint_number} in SQLite...',
    ]

    return jsonify({
        'status': 'success',
        'type': incident_type,
        'complaint_id': complaint_id,
        'complaint_number': complaint_number,
        'steps': pipeline_steps,
        'html': result_html,
    })


@complaints_bp.route('/api/complaints', methods=['GET'])
@admin_required
def get_complaints():
    rows = ComplaintModel.list_all()
    return jsonify(rows)


@complaints_bp.route('/api/track/<int:complaint_id>', methods=['GET'])
def track_complaint(complaint_id):
    comp = ComplaintModel.get(complaint_id)
    if not comp:
        return jsonify({
            'status': 'error',
            'message': f'No complaint found with ID #{complaint_id}'
        }), 404
    return jsonify({'status': 'success', 'complaint': dict(comp)})
