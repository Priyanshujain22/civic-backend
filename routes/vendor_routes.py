from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.auth_middleware import token_required, role_required
from models.complaint_model import Complaint
from models.quotation_model import Quotation
from models.vendor_model import Vendor

vendor_bp = Blueprint('vendor', __name__)

@vendor_bp.route('/available', methods=['GET'])
@token_required
@role_required('vendor')
def get_available_jobs():
    # Only show unverified vendors some message? 
    # For now, let's assume all verified for simpler flow or check here
    vendor = Vendor.get_by_user_id(request.user['id'])
    if not vendor or not vendor['verified']:
        return error_response("Vendor not verified. Please contact admin.", 403)
        
    complaints = Complaint.get_all() # We could filter for resolution_type='private' and status='Awaiting Quotes'
    private_jobs = [c for c in complaints if c['resolution_type'] == 'private' and c['status'] == 'Awaiting Quotes']
    return success_response(data=private_jobs)

@vendor_bp.route('/quote', methods=['POST'])
@token_required
@role_required('vendor')
def submit_quote():
    data = request.json
    complaint_id = data.get('complaint_id')
    price = data.get('price')
    estimated_time = data.get('estimated_time')
    
    if not complaint_id or not price:
        return error_response("Complaint ID and Price are required", 400)
        
    if Quotation.create(complaint_id, request.user['id'], price, estimated_time):
        return success_response(message="Quotation submitted successfully")
    else:
        return error_response("Failed to submit quotation", 500)

@vendor_bp.route('/my-jobs', methods=['GET'])
@token_required
@role_required('vendor')
def get_my_jobs():
    jobs = Quotation.get_by_vendor(request.user['id'])
    # Filter for jobs where quote was approved
    accepted_jobs = [j for j in jobs if j['status'] == 'Approved']
    return success_response(data=accepted_jobs)

@vendor_bp.route('/complete', methods=['POST'])
@token_required
@role_required('vendor')
def mark_complete():
    data = request.json
    complaint_id = data.get('complaint_id')
    
    if not complaint_id:
        return error_response("Complaint ID required", 400)
        
    if Complaint.update_status(complaint_id, 'Resolved'):
        return success_response(message="Job marked as completed")
    else:
        return error_response("Failed to update status", 500)
