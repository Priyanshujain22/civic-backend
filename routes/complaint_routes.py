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

    if not description or not location:
        return error_response("Description and Location are required", 400)

    complaint_id = Complaint.create(user['id'], category_id, description, location, image_path)
    
    if complaint_id:
        return success_response(message="Complaint submitted successfully", data={"id": complaint_id})
    else:
        return error_response("Failed to submit complaint", 500)

@complaint_bp.route('/complaints/my', methods=['GET'])
@token_required
def get_my_complaints():
    user = request.user
    complaints = Complaint.get_by_user(user['id'])
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
        return success_response(message="Quotation approved and vendor hired")
    else:
        return error_response("Approval failed", 500)
