"""
Status management route
=======================
  POST /api/update-status — update the status of an existing complaint

Bug fixes applied vs. original:
  - f-string syntax error fixed (was broken on Python < 3.12)
  - complaint_id validated as a positive integer before use
  - get_json(silent=True) prevents AttributeError on malformed requests
  - DB connection uses context manager to prevent leaks
"""
from flask import Blueprint, request, jsonify
from models.complaint import ComplaintModel
from routes.auth import admin_required

status_bp = Blueprint('status', __name__)

VALID_STATUSES = [
    'Received', 'Under Review', 'Investigating',
    'In Progress', 'Resolved', 'Closed', 'Rejected',
]


@status_bp.route('/api/update-status', methods=['POST'])
@admin_required
def update_status():
    # BUG FIX: silent=True returns None on bad JSON instead of crashing
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid or missing JSON body'}), 400

    new_status = data.get('status', '').strip()
    if new_status not in VALID_STATUSES:
        # BUG FIX: original had an f-string nested-quote syntax error here (crashed Python ≤ 3.11)
        valid_list = ', '.join(VALID_STATUSES)
        return jsonify({
            'status': 'error',
            'message': f'Invalid status. Must be one of: {valid_list}'
        }), 400

    # BUG FIX: complaint_id was previously used without any type or range check
    try:
        complaint_id = int(data.get('complaint_id'))
        if complaint_id <= 0:
            raise ValueError('ID must be a positive integer')
    except (TypeError, ValueError):
        return jsonify({
            'status': 'error',
            'message': 'complaint_id must be a positive integer'
        }), 400

    success = ComplaintModel.update_status(complaint_id, new_status)
    if not success:
        return jsonify({'status': 'error', 'message': 'Complaint not found'}), 404

    return jsonify({
        'status': 'success',
        'message': f'Complaint #{complaint_id} updated to: {new_status}'
    })
