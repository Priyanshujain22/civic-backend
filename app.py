import sys
import os
from flask import Flask
from flask_cors import CORS

# Add current directory to path for absolute imports on Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import Config first
try:
    from config import Config
except ImportError:
    # Fallback if config is in a different place
    sys.path.append(os.getcwd())
    from config import Config

# Global to store import error
IMPORT_ERROR = "None"

# Import Blueprints - Wrapped in a try-except to catch import errors on Vercel
try:
    from routes.auth_routes import auth_bp
    from routes.complaint_routes import complaint_bp
    from routes.admin_routes import admin_bp
    from routes.officer_routes import officer_bp
    from routes.vendor_routes import vendor_bp
except Exception as e:
    import traceback
    IMPORT_ERROR = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    print(f"CRITICAL IMPORT ERROR: {IMPORT_ERROR}")
    auth_bp = complaint_bp = admin_bp = officer_bp = vendor_bp = None

app = Flask(__name__)
app.config.from_object(Config)

# Robust CORS configuration
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"]
}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Migration helper from database.py
from database import run_db_migrations

# Run migrations once on startup
print("Starting database migrations...")
run_db_migrations()

# Register Blueprints only if they were imported successfully
if all([auth_bp, complaint_bp, admin_bp, officer_bp, vendor_bp]):
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(complaint_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(officer_bp, url_prefix='/api/officer')
    app.register_blueprint(vendor_bp, url_prefix='/api/vendor')
else:
    print(f"⚠️ Warning: Some blueprints failed to load. Migration still attempted. Error: {IMPORT_ERROR}")

@app.route('/')
def home():
    return {
        "status": "online" if auth_bp else "degraded",
        "message": "Civic Complaint System API" if auth_bp else "CRITICAL: Import Error on Server",
        "db_configured": Config.DATABASE_URL is not None,
        "import_error": IMPORT_ERROR
    }

@app.errorhandler(500)
def handle_500(e):
    return {"status": "error", "message": "Internal Server Error", "details": str(e)}, 500

@app.route('/api/db-check')
def db_check():
    from database import get_db_connection
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"status": "success", "message": "Database connection successful"}, 200
    else:
        return {"status": "error", "message": "Database connection failed. Check server logs."}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
