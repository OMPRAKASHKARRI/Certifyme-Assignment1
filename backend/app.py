import os
from flask import Flask, jsonify, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models import db, Admin
from routes import bp

# Path to the frontend folder
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.config.from_object(Config)

# Enable CORS for frontend integration
CORS(app, supports_credentials=True)

# Initialize Plugins
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized access. Please log in."}), 401

# Register Blueprints
app.register_blueprint(bp)

# Create Database tables
with app.app_context():
    db.create_all()

# Serve the frontend HTML
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'admin.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
