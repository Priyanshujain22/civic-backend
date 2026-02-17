from flask import Flask
from flask_cors import CORS
from config import Config

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.admin_routes import admin_bp
from routes.officer_routes import officer_bp

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Enable CORS for frontend communication

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(complaint_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(officer_bp, url_prefix='/api/officer')

@app.route('/')
def home():
    return {"message": "Civic Complaint System API is Running"}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
