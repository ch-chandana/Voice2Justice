"""
Services package — Business logic for Voice2Justice
=====================================================
Exports:
  - classifier:     classify_complaint, extract_location, build_summary
  - email_service:  send_complaint_email
  - pdf_service:    generate_complaint_pdf
"""
from services.classifier import (          # noqa: F401
    classify_complaint,
    extract_location,
    build_summary,
)
from services.email_service import (       # noqa: F401
    send_complaint_email,
)
from services.pdf_service import (         # noqa: F401
    generate_complaint_pdf,
)

__all__ = [
    'classify_complaint',
    'extract_location',
    'build_summary',
    'send_complaint_email',
    'generate_complaint_pdf',
]
