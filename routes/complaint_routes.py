from flask import Blueprint, request
from ..utils.response import success_response, error_response
from ..utils.auth_middleware import token_required
from ..models.complaint_model import Complaint

complaint_bp = Blueprint('complaint', __name__)

@complaint_bp.route('/complaints', methods=['POST'])
@token_required
def create_complaint():
    user = request.user
    data = request.json
    
    category_id = data.get('category_id') # Frontend should send ID
    # Note: For now frontend sends category Name string, backend needs to map or we change DB to store string (less ideal)
    # OR simpler for now: map common strings to IDs (1-6) or assumes frontend sends ID.
    # Let's assume frontend logic will be updated to send IDs later, 
    # but for robustness if we get a string, we might need a lookup.
    # PROPOSAL: Frontend sends category strings like 'Road Damage'. 
    # We should have a lookup or just store strings if schema allowed (schema has category_id INT).
    # We need a Category Model lookup. For MVP let's assume valid ID 1-6 or basic mapping.
    # Mapping for demo:
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
