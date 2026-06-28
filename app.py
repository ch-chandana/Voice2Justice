"""
Voice2Justice — Flask Application Entry Point
=============================================
This file is now responsible ONLY for:
  1. Creating the Flask app instance
  2. Initialising the database schema
  3. Registering the three route blueprints
  4. Serving the frontend template

All route logic has been moved to routes/:
  - routes/complaints.py  →  /api/process, /api/complaints, /api/track/<id>
  - routes/reports.py     →  /report/<id>
  - routes/status.py      →  /api/update-status
"""
import os
import sqlite3
import logging
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from datetime import timedelta
import ssl

from extensions import limiter

# Load .env before any blueprint imports so os.environ is fully populated
load_dotenv()

# Bypass SSL verification for local development to fix OAuth requests error
if os.environ.get('FLASK_ENV') != 'production':
    ssl._create_default_https_context = ssl._create_unverified_context
    import requests
    old_request = requests.Session.request
    def new_request(*args, **kwargs):
        kwargs['verify'] = False
        return old_request(*args, **kwargs)
    requests.Session.request = new_request

# ── Environment Validation ────────────────────────────────────────────────
if os.environ.get('FLASK_ENV') == 'production':
    if not os.environ.get('SECRET_KEY') or os.environ.get('SECRET_KEY') == 'default-dev-secret-key':
        raise ValueError("FATAL: SECRET_KEY must be set to a secure random string in production.")
    if not os.environ.get('EMAIL_USER') or not os.environ.get('EMAIL_PASS'):
        print("WARNING: Email credentials not fully configured. Email routing may fail.")

# ── Logging Configuration ─────────────────────────────────────────────────
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'), exist_ok=True)

log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

# File handler (10 MB max size, keep 5 backups)
file_handler = RotatingFileHandler(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log'), 
    maxBytes=10485760, 
    backupCount=5
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Setup root logger
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# ── App Instance ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-dev-secret-key')
app.permanent_session_lifetime = timedelta(minutes=30)

# Initialize Rate Limiter
limiter.init_app(app)

from extensions import oauth
oauth.init_app(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ── Database Path ─────────────────────────────────────────────────────────
# Also defined in config.py for blueprint use; kept here so init_db() works
# without an extra import before blueprints are registered.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'complaints.db')


# ── Database Initialisation ───────────────────────────────────────────────
from models.db import init_db
init_db()

# ── ML Model Initialization ───────────────────────────────────────────────
from ml.ml_model import classifier_instance
classifier_instance.load()

# ── Blueprint Registration ────────────────────────────────────────────────
from routes.complaints import complaints_bp  # noqa: E402
from routes.reports import reports_bp        # noqa: E402
from routes.status import status_bp          # noqa: E402
from routes.dashboard import dashboard_bp    # noqa: E402
from routes.auth import auth_bp              # noqa: E402
from routes.user_auth import user_auth_bp    # noqa: E402

app.register_blueprint(complaints_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(status_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_auth_bp)


# ── Frontend ──────────────────────────────────────────────────────────────
@app.route('/')
def serve_index():
    return render_template('index.html')


# ── Error Handlers ────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Not Found: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Error: {request.url}", exc_info=error)
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded: {request.url} by {request.remote_addr}")
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': f"Rate limit exceeded: {e.description}"}), 429
    return f"Rate limit exceeded: {e.description}", 429

# ── Security & Request Hooks ──────────────────────────────────────────────
@app.before_request
def log_request_info():
    # Only log API or auth paths to avoid spamming logs with static file requests
    if request.path.startswith('/api/') or request.path.startswith('/login'):
        logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

@app.after_request
def add_security_headers(response):
    # Security Headers
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# ── Entry Point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    # BUG FIX: debug mode is now controlled by FLASK_DEBUG env var
    # so it can never accidentally be True in production
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print('=' * 50)
    print('  Voice2Justice Flask Server')
    print('  Open http://127.0.0.1:5000 in your browser')
    print('=' * 50)
    app.run(debug=debug, host='127.0.0.1', port=5000)
