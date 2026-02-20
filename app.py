import sys
import os
from flask import Flask
from flask_cors import CORS
from config import Config

# Add current directory to path for absolute imports on Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.admin_routes import admin_bp
from routes.officer_routes import officer_bp

app = Flask(__name__)
app.config.from_object(Config)
Config.validate()  # Log warning if DATABASE_URL is missing

# Explicitly enable CORS for all origins to handle preflight requests safely
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Auto-migration for resolution_notes column - wrapped in a helper
def start_migrations():
    try:
        from database import get_db_connection
        conn = get_db_connection()
        if not conn: 
            print("SKIPPING MIGRATION: No database connection available.")
            return
        
        cursor = conn.cursor()
        cursor.execute("""
            ALTER TABLE complaints 
            ADD COLUMN IF NOT EXISTS resolution_notes TEXT;
        """)
        conn.commit()
        print("MIGRATION SUCCESS: Database schema is up to date.")
    except Exception as e:
        print(f"MIGRATION ERROR (Non-fatal): {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

# Only run migrations when app starts, not during every import if possible
# But for Vercel serverless, this is where it happens
start_migrations()

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(complaint_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(officer_bp, url_prefix='/api/officer')

@app.route('/')
def home():
    return {
        "status": "online",
        "message": "Civic Complaint System API is Running",
        "db_configured": Config.DATABASE_URL is not None
    }

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
