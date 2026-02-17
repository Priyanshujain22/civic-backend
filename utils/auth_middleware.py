from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from contextlib import contextmanager

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!', 'success': False}), 403

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            # Inject user data into kwargs or g (global context)
            # Here keeping it simple by passing 'current_user' to route if it accepts it
            # But standard Flask way is to use g OR just pass data.
            # Assuming we attach it to request for easier access
            request.user = data
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'success': False}), 403

        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'message': 'User not authenticated', 'success': False}), 403
            
            if request.user.get('role') != required_role:
                return jsonify({'message': f'Access denied: {required_role} role required', 'success': False}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
