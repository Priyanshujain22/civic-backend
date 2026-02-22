from flask import Blueprint, request
from utils.response import success_response, error_response
from utils.auth_middleware import token_required
from models.complaint_model import Complaint

complaint_bp = Blueprint('complaint', __name__)

@complaint_bp.route('/complaints', methods=['POST'])
@token_required
def create_complaint():
    user = request.user
    data = request.json
    
    category_id = data.get('category_id')
    cat_map = {
        "Road Damage": 1, "Garbage": 2, "Street Light": 3, 
        "Water Leakage": 4, "Drainage": 5, "Other": 6
    }
    
    cat_name = data.get('category')
    if not category_id and cat_name:
        category_id = cat_map.get(cat_name, 6)

    description = data.get('description')
    location = data.get('location')
    image_path = data.get('image_path')
    resolution_type = data.get('resolution_type')

    if not description or not location:
        return error_response("Description and Location are required", 400)

    result = Complaint.create(user['id'], category_id, description, location, image_path, resolution_type)
    
    if isinstance(result, int) or result:
        return success_response(message="Complaint submitted successfully", data={"id": result})
    else:
        # In a real production app, don't expose DB errors, but for this dev stage it helps
        return error_response(f"Backend Error: Check if database has 'resolution_type' column. Detail: {Complaint.last_error if hasattr(Complaint, 'last_error') else 'Unknown'}", 500)

@complaint_bp.route('/complaints/my', methods=['GET'])
@token_required
def get_my_complaints():
    user = request.user
    complaints = Complaint.get_by_user(user['id'])
    if not complaints and Complaint.last_error:
        return error_response(f"Retrieval Error: {Complaint.last_error}", 500)
    return success_response(data=complaints)

@complaint_bp.route('/complaints/<int:complaint_id>/quotes', methods=['GET'])
@token_required
def get_complaint_quotes(complaint_id):
    from models.quotation_model import Quotation
    quotes = Quotation.get_by_complaint(complaint_id)
    return success_response(data=quotes)

@complaint_bp.route('/quotes/<int:complaint_id>/approve', methods=['POST'])
@token_required
def approve_quote(complaint_id):
    data = request.json
    vendor_id = data.get('vendor_id')
    if not vendor_id:
        return error_response("Vendor ID required", 400)
    if Complaint.approve_quotation(complaint_id, vendor_id):
        return success_response(message="Quotation approved. Awaiting payment.")
    else:
        return error_response("Approval failed", 500)

@complaint_bp.route('/complaints/<int:complaint_id>/pay', methods=['POST'])
@token_required
def pay_complaint(complaint_id):
    if Complaint.mark_as_paid(complaint_id):
        return success_response(message="Payment successful. Job is now in progress.")
    else:
        return error_response("Payment failed", 500)

@complaint_bp.route('/complaints/<int:complaint_id>/feedback', methods=['POST'])
@token_required
def post_feedback(complaint_id):
    data = request.json
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not rating:
        return error_response("Rating is required", 400)
        
    if Complaint.submit_feedback(complaint_id, rating, comment):
        return success_response(message="Feedback submitted successfully")
    else:
        return error_response("Failed to submit feedback", 500)

@complaint_bp.route('/complaints/<int:complaint_id>/updates', methods=['GET'])
@token_required
def get_complaint_updates(complaint_id):
    from models.job_update_model import JobUpdate
    updates = JobUpdate.get_by_complaint(complaint_id)
    return success_response(data=updates)
