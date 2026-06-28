from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, session, flash, url_for
from models.user import UserModel
from extensions import limiter, oauth
import logging

logger = logging.getLogger(__name__)

user_auth_bp = Blueprint('user_auth', __name__)

def user_required(f):
    """
    Decorator for routes that require an authenticated citizen/user.
    Redirects to /user/login for HTML requests, or returns 401 for API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Unauthorized. Please log in.'}), 401
            return redirect(url_for('user_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@user_auth_bp.route('/user/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    """Handles citizen registration."""
    if 'user_id' in session:
        return redirect(url_for('user_auth.profile'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if not full_name or not email or not password:
            flash("All required fields must be filled out.", "danger")
            return render_template('register.html')

        user_id = UserModel.register(full_name, email, phone, password)
        if user_id:
            logger.info(f"New citizen registered: {email}")
            session['user_id'] = user_id
            session['user_name'] = full_name
            flash("Registration successful. Welcome to Voice2Justice!", "success")
            return redirect(url_for('user_auth.profile'))
        else:
            flash("An account with that email already exists.", "danger")

    return render_template('register.html')

@user_auth_bp.route('/user/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    """Handles citizen login."""
    if 'user_id' in session:
        return redirect(url_for('user_auth.profile'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = UserModel.authenticate(email, password)
        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            logger.info(f"Successful user login for: {email}")
            flash("Successfully logged in.", "success")
            return redirect(url_for('user_auth.profile'))
        else:
            logger.warning(f"Failed user login attempt for: {email} from IP: {request.remote_addr}")
            flash("Invalid email or password.", "danger")

    return render_template('user_login.html')

@user_auth_bp.route('/user/login/google')
def login_google():
    """Redirects to Google for OAuth login."""
    redirect_uri = url_for('user_auth.login_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@user_auth_bp.route('/user/login/google/callback')
def login_google_callback():
    """Handles callback from Google OAuth."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            flash("Failed to get user info from Google.", "danger")
            return redirect(url_for('user_auth.login'))
            
        email = user_info.get('email')
        full_name = user_info.get('name')
        google_id = user_info.get('sub')
        profile_picture = user_info.get('picture')
        
        # Link or register
        user = UserModel.oauth_login_or_register(email, full_name, google_id, profile_picture)
        
        session.permanent = True
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['profile_picture'] = user.get('profile_picture')
        
        logger.info(f"Successful Google OAuth login for: {email}")
        flash("Successfully logged in with Google.", "success")
        return redirect(url_for('user_auth.profile'))
    except Exception as e:
        logger.error(f"Google OAuth error: {e}", exc_info=True)
        flash("An error occurred during Google login.", "danger")
        return redirect(url_for('user_auth.login'))

@user_auth_bp.route('/user/logout', methods=['GET'])
def logout():
    """Logs out the citizen by clearing their session keys."""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('profile_picture', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('serve_index'))

@user_auth_bp.route('/user/profile', methods=['GET'])
@user_required
def profile():
    """Renders the citizen's profile and their complaint history."""
    user = UserModel.get_by_id(session['user_id'])
    complaints = UserModel.get_complaints(session['user_id'])
    return render_template('profile.html', user=user, complaints=complaints)
