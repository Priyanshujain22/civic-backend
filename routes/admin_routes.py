from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.auth_middleware import token_required, role_required
from models.complaint_model import Complaint
from models.user_model import User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/complaints', methods=['GET'])
@token_required
@role_required('admin')
def get_all_complaints():
    complaints = Complaint.get_all()
    return success_response(data=complaints)

@admin_bp.route('/assign', methods=['POST'])
@token_required
@role_required('admin')
def assign_officer():
    data = request.json
    complaint_id = data.get('complaint_id')
    if not complaint_id: 
        complaint_id = data.get('id')
        
    officer_id = data.get('officer_id')

    if not complaint_id or not officer_id:
        return error_response("Complaint ID and Officer ID required", 400)

    if Complaint.assign_officer(complaint_id, officer_id):
        return success_response(message="Officer assigned successfully")
    else:
        return error_response("Assignment failed", 500)

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_users():
    role_filter = request.args.get('role')
    users = User.get_all_by_role(role_filter)
    return success_response(data=users)
