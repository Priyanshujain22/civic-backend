from flask import Flask
from flask_cors import CORS
from config import Config
import sys
import os

# Add backend directory to sys.path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.admin_routes import admin_bp
from routes.officer_routes import officer_bp

app = Flask(__name__)
app.config.from_object(Config)
Config.validate()  # Log warning if DATABASE_URL is missing
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for frontend communication with explicit resource matching

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(complaint_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(officer_bp, url_prefix='/api/officer')

# Auto-migration for resolution_notes column
def run_migrations():
    from database import get_db_connection
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            ALTER TABLE complaints 
            ADD COLUMN IF NOT EXISTS resolution_notes TEXT;
        """)
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        cursor.close()
        conn.close()

run_migrations()

@app.route('/')
def home():
    return {"message": "Civic Complaint System API is Running"}

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
