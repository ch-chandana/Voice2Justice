from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, session, flash, url_for
from models.admin import AdminModel

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    """
    Decorator for routes that require an authenticated admin.
    Redirects to /login for HTML requests, or returns 401 for API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Unauthorized. Admin access required.'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


import logging
from extensions import limiter

logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    """Handles admin login."""
    if 'admin_id' in session:
        return redirect(url_for('dashboard.render_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = AdminModel.authenticate(username, password)
        if admin:
            session.permanent = True  # Allows session timeout configurations to apply
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_role'] = admin['role']
            logger.info(f"Successful login for admin: {username}")
            return redirect(url_for('dashboard.render_dashboard'))
        else:
            logger.warning(f"Failed login attempt for username: {username} from IP: {request.remote_addr}")
            flash("Invalid username or password.", "danger")
            
    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET'])
def logout():
    """Logs out the admin by clearing the session."""
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('auth.login'))
