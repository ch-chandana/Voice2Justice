"""
Routes package — Flask Blueprints for Voice2Justice
=====================================================
Exports all three blueprints so app.py can import them cleanly:

    from routes import complaints_bp, reports_bp, status_bp

URL ownership:
  complaints_bp → /api/process, /api/complaints, /api/track/<id>
  reports_bp    → /report/<id>
  status_bp     → /api/update-status
"""
from routes.complaints import complaints_bp   # noqa: F401
from routes.reports    import reports_bp      # noqa: F401
from routes.status     import status_bp       # noqa: F401

__all__ = ['complaints_bp', 'reports_bp', 'status_bp']
