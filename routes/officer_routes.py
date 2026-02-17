from flask import Blueprint, request
from ..utils.response import success_response, error_response
from ..utils.auth_middleware import token_required, role_required
from ..models.complaint_model import Complaint

officer_bp = Blueprint('officer', __name__)

@officer_bp.route('/assigned', methods=['GET'])
@token_required
@role_required('officer')
def get_assigned_complaints():
    user = request.user
    complaints = Complaint.get_assigned_to_officer(user['id'])
    return success_response(data=complaints)

@officer_bp.route('/update-status', methods=['POST'])
@token_required
@role_required('officer')
def update_status():
    data = request.json
    complaint_id = data.get('id')
    status = data.get('status')

    if not complaint_id or not status:
        return error_response("Complaint ID and Status required", 400)
        
    if status not in ['In Progress', 'Resolved']:
        return error_response("Invalid status", 400)

    if Complaint.update_status(complaint_id, status):
        return success_response(message="Status updated successfully")
    else:
        return error_response("Update failed", 500)
