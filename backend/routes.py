from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import re
import secrets
from datetime import datetime, timedelta

from models import db, Admin, Opportunity

bp = Blueprint('api', __name__)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ================= AUTH ROUTES =================

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([full_name, email, password, confirm_password]):
        return jsonify({"error": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    existing_admin = Admin.query.filter_by(email=email).first()
    if existing_admin:
        return jsonify({"error": "Account already exists"}), 409

    new_admin = Admin(full_name=full_name, email=email)
    new_admin.set_password(password)
    
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "Account created successfully"}), 201


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    email = data.get('email')
    password = data.get('password')
    remember_me = data.get('remember_me', False)

    admin = Admin.query.filter_by(email=email).first()

    if not admin or not admin.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(admin, remember=remember_me)
    return jsonify({"message": "Login successful", "admin": admin.to_dict()}), 200


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email or not is_valid_email(email):
        return jsonify({"error": "Invalid email"}), 400

    admin = Admin.query.filter_by(email=email).first()
    
    if admin:
        token = secrets.token_urlsafe(32)
        print(f"RESET LINK GENERATED FOR {email}: http://localhost:5000/reset-password?token={token}")
        # Normally you would save this token in the DB with an expiration time
        
    return jsonify({"message": "If the email is registered, a reset link has been sent"}), 200


# ================= OPPORTUNITY ROUTES =================

@bp.route('/api/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    ops = Opportunity.query.filter_by(admin_id=current_user.id).all()
    return jsonify({
        "status": "success",
        "data": [op.to_dict() for op in ops]
    }), 200


@bp.route('/api/opportunities', methods=['POST'])
@login_required
def create_opportunity():
    data = request.get_json()
    
    title = data.get('title')
    duration = data.get('duration')
    start_date = data.get('start_date')
    description = data.get('description')
    skills = data.get('skills')
    category = data.get('category')
    future_opportunities = data.get('future_opportunities')
    max_applicants = data.get('max_applicants')

    # required fields validation
    if not all([title, duration, start_date, description, skills, category, future_opportunities]):
        return jsonify({"error": "Missing required fields"}), 400

    valid_categories = ["technology", "business", "design", "marketing", "data", "other"]
    if category.lower() not in valid_categories:
        return jsonify({"error": f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"}), 400
    category = category.lower()

    new_op = Opportunity(
        title=title,
        duration=duration,
        start_date=start_date,
        description=description,
        skills=skills,
        category=category,
        future_opportunities=future_opportunities,
        max_applicants=max_applicants if max_applicants else None,
        admin_id=current_user.id
    )

    db.session.add(new_op)
    db.session.commit()

    return jsonify({"status": "success", "data": new_op.to_dict()}), 201


@bp.route('/api/opportunities/<int:id>', methods=['GET'])
@login_required
def get_opportunity(id):
    op = Opportunity.query.get(id)
    if not op or op.admin_id != current_user.id:
        return jsonify({"error": "Opportunity not found"}), 404

    return jsonify({"status": "success", "data": op.to_dict()}), 200


@bp.route('/api/opportunities/<int:id>/edit', methods=['PUT', 'POST'])
@login_required
def edit_opportunity(id):
    op = Opportunity.query.get(id)
    if not op or op.admin_id != current_user.id:
        return jsonify({"error": "Opportunity not found"}), 404

    data = request.get_json()
    
    title = data.get('title')
    duration = data.get('duration')
    start_date = data.get('start_date')
    description = data.get('description')
    skills = data.get('skills')
    category = data.get('category')
    future_opportunities = data.get('future_opportunities')
    
    if not all([title, duration, start_date, description, skills, category, future_opportunities]):
        return jsonify({"error": "Missing required fields"}), 400
        
    valid_categories = ["technology", "business", "design", "marketing", "data", "other"]
    if category.lower() not in valid_categories:
        return jsonify({"error": f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"}), 400
    category = category.lower()

    op.title = title
    op.duration = duration
    op.start_date = start_date
    op.description = description
    op.skills = skills
    op.category = category
    op.future_opportunities = future_opportunities
    
    if 'max_applicants' in data:
        op.max_applicants = data.get('max_applicants')

    db.session.commit()

    return jsonify({"status": "success", "data": op.to_dict()}), 200


@bp.route('/api/opportunities/<int:id>', methods=['DELETE'])
@login_required
def delete_opportunity(id):
    op = Opportunity.query.get(id)
    if not op or op.admin_id != current_user.id:
        return jsonify({"error": "Opportunity not found"}), 404

    db.session.delete(op)
    db.session.commit()

    return jsonify({"status": "success", "message": "Opportunity deleted"}), 200
