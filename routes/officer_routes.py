from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.auth_middleware import token_required, role_required
from models.complaint_model import Complaint

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
    resolution_notes = data.get('resolution_notes')

    if not complaint_id or not status:
        return error_response("Complaint ID and Status required", 400)
        
    if status not in ['In Progress', 'Resolved']:
        return error_response("Invalid status", 400)

    if Complaint.update_status(complaint_id, status, resolution_notes):
        return success_response(message="Status updated successfully")
    else:
        return error_response("Update failed", 500)

@officer_bp.route('/upload-proof', methods=['POST'])
@token_required
@role_required('officer')
def upload_proof():
    data = request.json
    complaint_id = data.get('complaint_id')
    proof_notes = data.get('proof_notes')
    # For now, we simulate image upload by just accepting a path/note
    if not complaint_id:
        return error_response("Complaint ID required", 400)
    if Complaint.update_status(complaint_id, 'Resolved', proof_notes):
        return success_response(message="Completion proof uploaded and job resolved")
    return error_response("Failed to upload proof", 500)
