from flask import Flask, send_from_directory, request, jsonify
import sqlite3
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'complaints.db')

# ── Email Setup ──────────────────────────────────────────────────
# Note for hackathon: Using a generic test email account or prompting.
# In a real app, you'd load these from .env. If the credentials fail,
# the app catches the exception and continues without crashing.
SENDER_EMAIL = "voice2justicee@gmail.com"  # Using user's provided email
SENDER_APP_PASSWORD = "cbob gosf yvig ptcb"     # Using user's provided password

def send_complaint_email(to_email, complaint_id, category, text, summary, sections, location):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"URGENT: New Complaint Received - ID #{complaint_id} ({category})"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #4f46e5;">Voice2Justice Routing System</h2>
            <p><strong>Complaint ID:</strong> #{complaint_id}</p>
            <p><strong>Category:</strong> {category}</p>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Applicable Codes/Sections:</strong> {sections}</p>
            <hr>
            <h3>AI Summary:</h3>
            <p style="background: #f1f5f9; padding: 15px; border-left: 4px solid #3b82f6;">{summary}</p>
            <h3>Original Citizen Narrative:</h3>
            <p style="font-style: italic;">"{text}"</p>
            <hr>
            <p><small>This is an automated message from the AI Triage System.</small></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        # Real sending configuration
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ [MOCK EMAIL SENT] To: {to_email} | Subject: {msg['Subject']}")
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False

# ── Database Setup ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS complaints') # Reset DB for new schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            department TEXT,
            priority TEXT,
            sla TEXT,
            summary TEXT,
            sections TEXT,
            submitted_to TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ── Serve Frontend ──────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

# ── Agent Pipeline Keywords ─────────────────────────────────────
CRIME_KEYWORDS = [
    'snatch', 'rob', 'steal', 'theft', 'murder', 'assault', 'attack',
    'kidnap', 'harass', 'stab', 'shoot', 'chain', 'purse', 'scared',
    'crime', 'threat', 'beat', 'molest', 'rape', 'abuse', 'extortion'
]
CIVIC_KEYWORDS = [
    'water', 'pipe', 'leak', 'pothole', 'garbage', 'street', 'light',
    'road', 'drain', 'sewer', 'electric', 'park', 'footpath', 'bridge',
    'clean', 'waste', 'noise', 'pollution', 'construction', 'flood'
]

# ── Process Complaint API ──────────────────────────────────────
@app.route('/api/process', methods=['POST'])
def process_complaint():
    data = request.get_json()
    text = data.get('text', '').strip()
    gps_location = data.get('location', '')

    if not text:
        return jsonify({'status': 'error', 'message': 'No complaint text provided'}), 400

    text_lower = text.lower()

    import re
    loc_pattern = r'((?:[a-zA-Z0-9-,]+\s+){1,6}(?:street|road|cross|layout|nagar|colony|block|market|area|park|junction|circle|highway|avenue|sector|phase|st|rd)(?:\s+[a-zA-Z0-9-,]+){0,2})'
    loc_match = re.search(loc_pattern, text, re.IGNORECASE)
    
    if loc_match:
        extracted = loc_match.group(1).strip().title()
        # Remove common prepositions at start of sentence if present
        extracted = re.sub(r'^(At|On|In|Near|Opposite|Outside|Behind|Around)\s+', '', extracted, flags=re.IGNORECASE)
        final_location = extracted
    else:
        final_location = gps_location
        
        
    if not final_location or "denied" in final_location.lower() or "unavailable" in final_location.lower() or "not supported" in final_location.lower():
        return jsonify({'status': 'error', 'message': 'Location access is mandatory. Please enable GPS or specify a location in your complaint.'}), 400

    # 1. Classifier Agent
    crime_score = sum(1 for kw in CRIME_KEYWORDS if kw in text_lower)
    civic_score = sum(1 for kw in CIVIC_KEYWORDS if kw in text_lower)

    if crime_score > civic_score:
        incident_type = 'crpc_crime'
        category = 'Criminal Offense'
        department = 'Local Police Station'
        priority = 'High'
        sla = 'Immediate FIR Registration'
        sections = "BNS Sec. 378 (Theft/Snatching), BNS Sec. 354 (Assault), BNS Sec. 109"
        submitted_to = "Station House Officer (SHO), Local Police Jurisdiction"
        target_email = "chandanachettipally@gmail.com"  # Police Department Route
        summary = f"The complainant reported a critical incident involving potential criminal activity. The text indicates threats or acts such as: {text[:100]}... Required immediate intelligence routing."
    else:
        incident_type = 'civic_issue'
        category = 'Infrastructure / Civic Issue'
        department = 'Municipal Corporation'
        priority = 'Medium'
        sla = '24-48 Hours'
        sections = "Municipal Corporation Act, Section 298 (Maintenance of Public Infrastructure)"
        submitted_to = "Chief Zonal Officer, Public Works & Sanitation Dept"
        target_email = "rpranitha909@gmail.com"  # Civic Issue Route
        summary = f"The citizen reported a civic discrepancy regarding localized infrastructure. Issue overview: {text[:100]}... Requires standard municipal intervention workflow."

    # 2. Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO complaints (text, type, category, department, priority, sla, summary, sections, submitted_to, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (text, incident_type, category, department, priority, sla, summary, sections, submitted_to, final_location))
    complaint_id = c.lastrowid
    conn.commit()
    conn.close()

    # Shared Button for PDF Download
    pdf_btn_html = f'''
    <button class="btn btn-primary" onclick="window.open('/report/{complaint_id}', '_blank')" style="width:100%;margin-top:1rem;font-size:0.85rem;padding:0.5rem;display:flex;align-items:center;justify-content:center;gap:0.5rem;border:none;cursor:pointer;">
        <i class="fa-solid fa-file-pdf"></i> Generate & Download PDF Report
    </button>
    '''

    # 3. Build response HTML
    email_status_text = f"✔ Auto-Routed to: {target_email}"

    if incident_type == 'crpc_crime':
        result_html = f'''
        <div class="result-card">
            <div class="result-header">
                <span style="font-family:monospace;color:var(--text-muted);">
                    <i class="fa-solid fa-file-pdf"></i> FIR_Draft_#{complaint_id}
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
                    <i class="fa-solid fa-ticket"></i> Ticket_#CIV-{complaint_id}
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
                <div class="result-label">Email Routed</div>
                <div class="result-value" style="color:#10b981; font-size: 0.85rem;">{email_status_text}</div>
            </div>
            {pdf_btn_html}
        </div>'''

    # Send Background Email
    send_complaint_email(target_email, complaint_id, category, text, summary, sections, final_location)

    # 4. Pipeline steps for frontend animation
    pipeline_steps = [
        "Initializing Flask Agent Platform...",
        "[Agent Extractor] Parsing entities...",
        "[Agent Classifier] Determining issue type...",
        f"[Agent Mapper] Mapping to {'Legal Codes' if incident_type == 'crpc_crime' else 'Civic Directory'}...",
        "[Agent Router] Generating structured payload...",
        f"[Database] Saved as complaint #{complaint_id} in SQLite..."
    ]

    return jsonify({
        'status': 'success',
        'type': incident_type,
        'complaint_id': complaint_id,
        'steps': pipeline_steps,
        'html': result_html
    })

# ── Get All Complaints (bonus endpoint) ────────────────────────
@app.route('/api/complaints', methods=['GET'])
def get_complaints():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM complaints ORDER BY created_at DESC')
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rows)

# ── Generate PDF / Report HTML Route ─────────────────────────────
@app.route('/report/<int:complaint_id>')
def generate_report(complaint_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    comp = c.fetchone()
    conn.close()

    if not comp:
        return "Complaint not found", 404
    
    doc_type = 'First Information Report (FIR)' if comp['type'] == 'crpc_crime' else 'Civic Issue Official Report'
    pdf_filename = f"Report_{comp['type']}_{complaint_id}.pdf" if comp['type'] == 'crpc_crime' else f"Report_Civic_{complaint_id}.pdf"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Report - #{comp['id']}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; padding: 20px; background: #e2e8f0; margin: 0; color: #1e293b; }}
            .document {{ background: white; padding: 50px; max-width: 800px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #4f46e5; border-radius: 4px; }}
            .header {{ text-align: center; border-bottom: 2px solid #cbd5e1; padding-bottom: 20px; margin-bottom: 30px; }}
            .title {{ font-size: 28px; font-weight: 800; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; color: #0f172a; }}
            .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 10px; }}
            .meta {{ font-size: 13px; color: #475569; font-family: monospace; }}
            .grid {{ display: grid; grid-template-columns: 180px 1fr; gap: 15px; margin-bottom: 30px; background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }}
            .label {{ font-weight: 700; color: #334155; text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px; }}
            .value {{ color: #0f172a; font-weight: 500; }}
            .section-title {{ font-size: 18px; font-weight: 700; margin-top: 40px; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; gap: 10px; }}
            .section-title::after {{ content: ''; flex: 1; height: 1px; background: #e2e8f0; }}
            .summary-box {{ line-height: 1.7; background: #eff6ff; padding: 20px; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; font-size: 15px; color: #1e3a8a; }}
            .narrative-box {{ line-height: 1.7; white-space: pre-wrap; font-style: italic; color: #475569; padding: 20px; background: #f1f5f9; border-radius: 8px; border: 1px solid #e2e8f0; }}
            
            .top-bar {{ display: flex; justify-content: center; margin-bottom: 20px; }}
            .btn-download {{ display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 12px 24px; background: #4f46e5; color: white; border: none; cursor: pointer; font-size: 16px; border-radius: 30px; font-weight: 600; box-shadow: 0 4px 12px rgba(79,70,229,0.3); transition: all 0.2s; }}
            .btn-download:hover {{ background: #4338ca; transform: translateY(-2px); }}
            
            .footer-sig {{ margin-top: 60px; display: flex; justify-content: space-between; }}
            .sig-block {{ text-align: center; color: #64748b; font-size: 14px; }}
            .sig-line {{ border-top: 1px solid #94a3b8; width: 200px; margin-bottom: 10px; }}
            
            /* Print styles */
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
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                Save as Official PDF
            </button>
        </div>

        <div class="document" id="pdf-content">
            <div class="header">
                <div class="title">{doc_type}</div>
                <div class="subtitle">Automated Intelligence Routing System - Voice2Justice</div>
                <div class="meta">Doc ID: {comp['type'].upper()}-{comp['id']} &nbsp;&bull;&nbsp; Generated: {comp['created_at']}</div>
            </div>

            <div class="section-title">Routing Protocol</div>
            <div class="grid">
                <div class="label">Complaint Category:</div><div class="value">{comp['category']}</div>
                <div class="label">Location:</div><div class="value">{comp['location']}</div>
                <div class="label">Routing Department:</div><div class="value">{comp['department']}</div>
                <div class="label">Priority Level:</div><div class="value" style="color: {'#dc2626' if comp['priority']=='High' else '#d97706'}; font-weight: 700;">{comp['priority']}</div>
                <div class="label">Expected SLA:</div><div class="value">{comp['sla']}</div>
                <div class="label">Submitted To:</div><div class="value">{comp['submitted_to']}</div>
                <div class="label">Applicable Codes:</div><div class="value">{comp['sections']}</div>
            </div>

            <div class="section-title">AI Complaint Extracted Summary</div>
            <div class="summary-box">
                {comp['summary']}
            </div>

            <div class="section-title">Verbatim Citizen Narrative</div>
            <div class="narrative-box">{comp['text']}</div>

            <div class="footer-sig">
                <div class="sig-block">
                    <div class="sig-line"></div>
                    <p>Digital AI Signature</p>
                    <p style="font-size: 11px; font-family: monospace;">Hash: V2J-{comp['id']}-{hash(comp['text']) % 100000}</p>
                </div>
                <div class="sig-block">
                    <div class="sig-line"></div>
                    <p>Receiving Authority</p>
                    <p style="font-size: 11px;">{comp['submitted_to']}</p>
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
                  margin:       10,
                  filename:     'Report_{comp['type']}_{comp['id']}.pdf',
                  image:        {{ type: 'jpeg', quality: 0.98 }},
                  html2canvas:  {{ scale: 2, useCORS: true }},
                  jsPDF:        {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
                }};
                
                html2pdf().set(opt).from(element).save().then(() => {{
                    btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Downloaded Successfully';
                    setTimeout(() => {{
                        btn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Save as Official PDF';
                        btn.style.opacity = '1';
                    }}, 3000);
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html

# ── Run ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  Voice2Justice Flask Server")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)
