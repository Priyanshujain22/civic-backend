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

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_users():
    role = request.args.get('role')
    category = request.args.get('category')
    users = User.get_all_by_role(role, category)
    if not users and User.last_error:
        return error_response(f"Backend error: {User.last_error}", 500)
    return success_response(data=users)

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

@admin_bp.route('/route/government', methods=['POST'])
@token_required
@role_required('admin')
def route_government():
    data = request.json
    complaint_id = data.get('complaint_id')
    officer_id = data.get('officer_id')
    if not complaint_id:
        return error_response("Complaint ID required", 400)
    
    success, message = Complaint.route_to_government(complaint_id, officer_id)
    if success:
        return success_response(message=message)
    else:
        return error_response(message, 500)

@admin_bp.route('/route/private', methods=['POST'])
@token_required
@role_required('admin')
def route_private():
    data = request.json
    complaint_id = data.get('complaint_id')
    if not complaint_id:
        return error_response("Complaint ID required", 400)
    
    success, message = Complaint.route_to_private(complaint_id)
    if success:
        return success_response(message=message)
    else:
        return error_response(message, 500)

@admin_bp.route('/route/vendor', methods=['POST'])
@token_required
@role_required('admin')
def route_vendor():
    data = request.json
    complaint_id = data.get('complaint_id')
    vendor_id = data.get('vendor_id')
    if not complaint_id or not vendor_id:
        return error_response("Complaint ID and Vendor ID required", 400)
    success, message = Complaint.assign_vendor(complaint_id, vendor_id)
    if success:
        return success_response(message=message)
    else:
        return error_response(message, 500)

@admin_bp.route('/vendors/verify', methods=['POST'])
@token_required
@role_required('admin')
def verify_vendor():
    data = request.json
    vendor_id = data.get('vendor_id')
    from models.vendor_model import Vendor
    if Vendor.verify(vendor_id):
        return success_response(message="Vendor verified successfully")
    return error_response("Verification failed", 500)

@admin_bp.route('/migrate', methods=['GET'])
@token_required
@role_required('admin')
def force_migrate():
    from database import run_db_migrations
    run_db_migrations()
    return success_response(message="Migration triggered successfully.")
