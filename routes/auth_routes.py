from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from config import Config
from utils.response import success_response, error_response
from utils.auth_middleware import token_required
from models.user_model import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    role = data.get('role', 'citizen') # Default to citizen

    if not name or not email or not password:
        return error_response("Missing required fields", 400)

    # Check if user exists
    if User.get_by_email(email):
        return error_response("Email already registered", 409)

    hashed_password = generate_password_hash(password)
    
    if User.create(name, email, hashed_password, role, phone):
        return success_response(message="User registered successfully")
    else:
        return error_response("Registration failed", 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    print(f"DEBUG: Login attempt for email: {email}")
    user = User.get_by_email(email)
    
    # Check hashed password, or plain text for initial default users
    is_valid = False
    if user:
        print(f"DEBUG: User object retrieved for {email}")
        if check_password_hash(user['password'], password):
            is_valid = True
            print("DEBUG: Password match via hash")
        elif user['password'] == password: # Fallback for plain text default users
            is_valid = True
            print("DEBUG: Password match via plain text")
        else:
            print("DEBUG: Password DOES NOT match")
    else:
        # Check if it was a connection error or just no user
        from database import get_db_connection
        test_conn = get_db_connection()
        if not test_conn:
            print(f"DEBUG: DATABASE CONNECTION FAILED for login attempt: {email}")
            return error_response("Server database connection error", 500)
        else:
            test_conn.close()
            print(f"DEBUG: No user found in DB for email: {email}")
            
    if not is_valid:
        return error_response("Invalid credentials", 401)

    # Generate Token
    token_payload = {
        'id': user['id'],
        'email': user['email'],
        'role': user['role'],
        'name': user['name'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    
    token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm="HS256")
    
    return success_response(data={
        "token": token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "role": user['role']
        }
    })

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    user_id = request.user['id']
    user = User.get_by_id(user_id)
    if not user:
        return error_response("User not found", 404)
    
    # Remove password from response
    user.pop('password', None)
    return success_response(data=user)

@auth_bp.route('/profile/update', methods=['POST'])
@token_required
def update_profile():
    user_id = request.user['id']
    data = request.json
    name = data.get('name')
    phone = data.get('phone')

    if not name:
        return error_response("Name is required", 400)

    if User.update(user_id, name, phone):
        return success_response(message="Profile updated successfully")
    else:
        return error_response("Failed to update profile", 500)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    
    if not email:
        return error_response("Email is required", 400)
    
    user = User.get_by_email(email)
    
    # For security reasons, we always return success even if the email doesn't exist
    # to prevent account enumeration.
    return success_response(message="If an account exists with this email, a reset link has been sent.")
