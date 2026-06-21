"""
Flask Extensions
================
Initializes Flask extensions like Flask-Limiter here to avoid circular imports.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize rate limiter with IP address tracking
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
