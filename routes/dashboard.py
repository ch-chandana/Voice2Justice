from flask import Blueprint, jsonify, render_template
from models.complaint import ComplaintModel
from routes.auth import admin_required

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
        return jsonify({'status': 'error', 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/recent', methods=['GET'])
@admin_required
def api_dashboard_recent():
    """Returns the most recent complaints for the data table."""
    try:
        recent = ComplaintModel.get_recent_complaints(limit=10)
        return jsonify({
            'status': 'success',
            'data': recent
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
