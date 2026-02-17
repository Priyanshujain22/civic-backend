from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from config import Config
from ..utils.response import success_response, error_response
from ..models.user_model import User

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
    
    user = User.get_by_email(email)
    
    if not user or not check_password_hash(user['password'], password):
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
