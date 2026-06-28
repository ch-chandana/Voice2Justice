"""
Flask Extensions
================
Initializes Flask extensions like Flask-Limiter here to avoid circular imports.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

# Initialize rate limiter with IP address tracking
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize OAuth registry
oauth = OAuth()
