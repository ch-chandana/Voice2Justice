from flask import Flask, send_from_directory, request, jsonify, send_file
import sqlite3
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Database Path (Render Safe)
DB_PATH = 'complaints.db'

# Email Setup
SENDER_EMAIL = "voice2justicee@gmail.com"
SENDER_APP_PASSWORD = "cbob gosf yvig ptcb"


# ── Email Function ─────────────────────────────────────
def send_complaint_email(to_email, complaint_id, category, text, summary, sections, location):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"New Complaint #{complaint_id} ({category})"

        body = f"""
        Complaint ID: {complaint_id}

        Category: {category}
        Location: {location}

        AI Summary:
        {summary}

        Original Complaint:
        {text}

        Legal Sections:
        {sections}
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print("Email Error:", e)


# ── Database Setup ─────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            type TEXT,
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
    """)

    conn.commit()
    conn.close()


init_db()


# ── Serve Frontend ─────────────────────────────────────
@app.route('/')
def home():
    return send_file('index.html')


# ── Keyword Lists ─────────────────────────────────────
CRIME_KEYWORDS = [
    'snatch', 'rob', 'steal', 'theft', 'murder', 'assault',
    'attack', 'kidnap', 'harass', 'stab', 'shoot', 'rape'
]

CIVIC_KEYWORDS = [
    'water', 'pipe', 'leak', 'pothole', 'garbage', 'street',
    'road', 'drain', 'sewer', 'electric', 'waste'
]


# ── Process Complaint ─────────────────────────────────
@app.route('/api/process', methods=['POST'])
def process_complaint():

    data = request.get_json()

    text = data.get("text", "").strip()
    gps_location = data.get("location", "")

    if not text:
        return jsonify({"status": "error", "message": "No complaint text"}), 400

    text_lower = text.lower()

    # Location Extraction
    loc_pattern = r'((?:[a-zA-Z0-9-,]+\s+){1,6}(?:street|road|nagar|area|layout|colony))'
    loc_match = re.search(loc_pattern, text, re.IGNORECASE)

    if loc_match:
        final_location = loc_match.group(1).title()
    else:
        final_location = gps_location

    if not final_location:
        return jsonify({"status": "error", "message": "Location required"}), 400

    # Classification
    crime_score = sum(1 for kw in CRIME_KEYWORDS if kw in text_lower)
    civic_score = sum(1 for kw in CIVIC_KEYWORDS if kw in text_lower)

    if crime_score > civic_score:

        incident_type = "crime"
        category = "Criminal Offense"
        department = "Local Police Station"
        priority = "High"
        sla = "Immediate"
        sections = "BNS Sec 378 Theft, Sec 354 Assault"
        submitted_to = "Station House Officer"
        email = "chandanachettipally@gmail.com"

        summary = f"Crime related complaint reported: {text[:100]}..."

    else:

        incident_type = "civic"
        category = "Civic Issue"
        department = "Municipal Corporation"
        priority = "Medium"
        sla = "24-48 hours"
        sections = "Municipal Infrastructure Act"
        submitted_to = "Municipal Officer"
        email = "rpranitha909@gmail.com"

        summary = f"Civic infrastructure issue reported: {text[:100]}..."

    # Save to Database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO complaints
        (text, type, category, department, priority, sla, summary, sections, submitted_to, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        text,
        incident_type,
        category,
        department,
        priority,
        sla,
        summary,
        sections,
        submitted_to,
        final_location
    ))

    complaint_id = c.lastrowid

    conn.commit()
    conn.close()

    # Send Email
    send_complaint_email(email, complaint_id, category, text, summary, sections, final_location)

    result_html = f"""
    <div class="result-card">
        <div class="result-header">
            <span style="font-family:monospace">Complaint #{complaint_id}</span>
            <span class="result-tag {'tag-crime' if incident_type=='crime' else 'tag-civic'}">
                {category}
            </span>
        </div>

        <div class="result-row">
            <div class="result-label">Location</div>
            <div class="result-value">{final_location}</div>
        </div>

        <div class="result-row">
            <div class="result-label">Department</div>
            <div class="result-value">{department}</div>
        </div>

        <div class="result-row">
            <div class="result-label">Priority</div>
            <div class="result-value">{priority}</div>
        </div>

        <div class="result-row">
            <div class="result-label">Sections</div>
            <div class="result-value">{sections}</div>
        </div>
    </div>
    """

    steps = [
        "Initializing agent system...",
        "Extracting entities...",
        "Classifying complaint...",
        "Mapping department...",
        "Generating structured report..."
    ]

    return jsonify({
        "status": "success",
        "complaint_id": complaint_id,
        "steps": steps,
        "html": result_html
    })


# ── View Complaints API ─────────────────────────────────
@app.route('/api/complaints')
def view_complaints():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    c = conn.cursor()
    c.execute("SELECT * FROM complaints ORDER BY created_at DESC")

    rows = [dict(row) for row in c.fetchall()]

    conn.close()

    return jsonify(rows)


# ── Run Server ─────────────────────────────────────────
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)