"""
Dashboard & Admin Review Routes
================================
  GET  /dashboard               — render the analytics dashboard HTML
  GET  /api/dashboard/stats     — top-level aggregate stats
  GET  /api/dashboard/categories — top 5 categories for charts
  GET  /api/dashboard/trends    — monthly trends + status distribution
  GET  /api/dashboard/recent    — recent complaints with fraud/verification data
  GET  /api/dashboard/fraud-stats — fraud & verification aggregate stats
  POST /api/admin/review        — admin action: mark complaint as Genuine or Fake
"""
import logging
from flask import Blueprint, jsonify, render_template, request
from models.complaint import ComplaintModel
from routes.auth import admin_required

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
@admin_required
def render_dashboard():
    """Renders the main analytics dashboard HTML page."""
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@admin_required
def api_dashboard_stats():
    """Returns top-level aggregate statistics."""
    try:
        stats = ComplaintModel.get_dashboard_stats()
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/categories', methods=['GET'])
@admin_required
def api_dashboard_categories():
    """Returns the top 5 complaint categories for charts."""
    try:
        categories = ComplaintModel.get_top_categories(limit=5)
        return jsonify({
            'status': 'success',
            'data': categories
        })
    except Exception as e:
        logger.error(f"Dashboard categories error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/trends', methods=['GET'])
@admin_required
def api_dashboard_trends():
    """Returns monthly trends and status distributions for charts."""
    try:
        trends = ComplaintModel.get_monthly_trends()
        status_dist = ComplaintModel.get_status_distribution()
        return jsonify({
            'status': 'success',
            'data': {
                'monthly_trends': trends,
                'status_distribution': status_dist
            }
        })
    except Exception as e:
        logger.error(f"Dashboard trends error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/recent', methods=['GET'])
@admin_required
def api_dashboard_recent():
    """Returns the most recent complaints with fraud & verification columns."""
    try:
        recent = ComplaintModel.get_recent_complaints(limit=20)
        return jsonify({
            'status': 'success',
            'data': recent
        })
    except Exception as e:
        logger.error(f"Dashboard recent error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/fraud-stats', methods=['GET'])
@admin_required
def api_dashboard_fraud_stats():
    """Returns fraud, verification, and review status aggregate statistics."""
    try:
        fraud_stats = ComplaintModel.get_fraud_stats()
        return jsonify({
            'status': 'success',
            'data': fraud_stats
        })
    except Exception as e:
        logger.error(f"Fraud stats error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── Admin Review Action ───────────────────────────────────────────────────

VALID_REVIEW_STATUSES = ['Pending', 'Genuine', 'Fake']

@dashboard_bp.route('/api/admin/review', methods=['POST'])
@admin_required
def admin_review_complaint():
    """
    Admin action to mark a complaint as Genuine or Fake.
    Stores the decision in the `review_status` database field.
    This enables the platform to learn the difference between
    suspicious (auto-flagged) and confirmed fake (admin-verified).
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid or missing JSON body'}), 400

    # Validate complaint_id
    try:
        complaint_id = int(data.get('complaint_id'))
        if complaint_id <= 0:
            raise ValueError('ID must be positive')
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'complaint_id must be a positive integer'}), 400

    # Validate review_status
    review_status = data.get('review_status', '').strip()
    if review_status not in VALID_REVIEW_STATUSES:
        valid_list = ', '.join(VALID_REVIEW_STATUSES)
        return jsonify({
            'status': 'error',
            'message': f'Invalid review_status. Must be one of: {valid_list}'
        }), 400

    # Check complaint exists
    comp = ComplaintModel.get(complaint_id)
    if not comp:
        return jsonify({'status': 'error', 'message': 'Complaint not found'}), 404

    # Update the review status
    success = ComplaintModel.update_review_status(complaint_id, review_status)
    if success:
        logger.info(f"Admin review: Complaint #{complaint_id} marked as '{review_status}'")
        return jsonify({
            'status': 'success',
            'message': f'Complaint #{complaint_id} marked as {review_status}'
        })
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update review status'}), 500
