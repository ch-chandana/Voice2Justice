"""
Email Service
==============
Gmail SMTP notification sender — isolated from route logic.

Reads SENDER_EMAIL and SENDER_APP_PASSWORD from environment variables
(loaded via dotenv in config.py / app.py).

Extracted from routes/complaints.py in Step 3.

IMPORTANT: Email is sent in a background thread so it does NOT block
the Gunicorn worker.  On Render free tier WEB_CONCURRENCY=1, a blocking
SMTP call would freeze the entire server for 10–60 seconds.
"""
import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# ── SMTP connection timeout (seconds) ────────────────────────────────────
_SMTP_TIMEOUT = 10  # fail fast instead of hanging for 60+ seconds


def _send_email_sync(
    to_email: str,
    complaint_id: int,
    category: str,
    text: str,
    summary: str,
    sections: str,
    location: str,
) -> bool:
    """
    Internal sync email sender — called inside a background thread.
    Returns True on success, False on any error (logged to stdout).
    """
    sender_email = os.environ.get('SENDER_EMAIL', '')
    sender_password = os.environ.get('SENDER_APP_PASSWORD', '')

    # Guard: skip entirely if credentials are not configured
    if not sender_email or not sender_password:
        logger.warning(
            "[EMAIL SKIP] SENDER_EMAIL or SENDER_APP_PASSWORD not set — "
            "email notification skipped for complaint #%s", complaint_id
        )
        return False

    if not to_email:
        logger.warning("[EMAIL SKIP] No target email for complaint #%s", complaint_id)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = (
            f"URGENT: New Complaint Received - ID #{complaint_id} ({category})"
        )

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

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=_SMTP_TIMEOUT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info("[EMAIL SENT] To: %s | Subject: %s", to_email, msg['Subject'])
        return True
    except Exception as e:
        logger.error("[EMAIL ERROR] Complaint #%s — %s", complaint_id, e)
        return False


def send_complaint_email(
    to_email: str,
    complaint_id: int,
    category: str,
    text: str,
    summary: str,
    sections: str,
    location: str,
) -> None:
    """
    Fire-and-forget email sender.

    Spawns a daemon thread so the HTTP response is returned immediately
    to the client instead of blocking for the entire SMTP handshake.
    """
    t = threading.Thread(
        target=_send_email_sync,
        args=(to_email, complaint_id, category, text, summary, sections, location),
        daemon=True,  # won't prevent process shutdown
    )
    t.start()
    logger.info("[EMAIL QUEUED] Background thread started for complaint #%s", complaint_id)
