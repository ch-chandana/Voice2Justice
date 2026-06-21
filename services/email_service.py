"""
Email Service
==============
Gmail SMTP notification sender — isolated from route logic.

Reads SENDER_EMAIL and SENDER_APP_PASSWORD from environment variables
(loaded via dotenv in config.py / app.py).

Extracted from routes/complaints.py in Step 3.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_complaint_email(
    to_email: str,
    complaint_id: int,
    category: str,
    text: str,
    summary: str,
    sections: str,
    location: str,
) -> bool:
    """
    Send a complaint routing notification via Gmail SMTP.

    Returns True on success, False on any error (logged to stdout).
    """
    sender_email = os.environ.get('SENDER_EMAIL', '')
    sender_password = os.environ.get('SENDER_APP_PASSWORD', '')

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

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] To: {to_email} | Subject: {msg['Subject']}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
