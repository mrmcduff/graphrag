"""
User management API routes for GraphRAG.

This module defines the API endpoints for user management.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
import re

from .models import db, User
from .auth import require_auth, require_admin, authenticate_user
from .utils import format_error_response, log_api_request

# Create a blueprint for the user management API routes
user_bp = Blueprint('user', __name__, url_prefix='/api/users')

@user_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request body:
        username: Username (required)
        email: Email address (required)
        password: Password (required)
        
    Returns:
        User data with access token
    """
    data = request.json or {}
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify(format_error_response(f"Missing required field: {field}", 400)), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # Validate username
    if not re.match(r'^[a-zA-Z0-9_]{3,50}$', username):
        return jsonify(format_error_response(
            "Username must be 3-50 characters and contain only letters, numbers, and underscores", 
            400)), 400
    
    # Validate email
    try:
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return jsonify(format_error_response(f"Invalid email: {str(e)}", 400)), 400
    
    # Validate password
    if len(password) < 8:
        return jsonify(format_error_response("Password must be at least 8 characters long", 400)), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify(format_error_response("Username already exists", 409)), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify(format_error_response("Email already exists", 409)), 409
    
    # Create new user
    try:
        user = User(
            username=username,
            email=email,
            password=password,
            is_admin=False,
            daily_limit=data.get('daily_limit', 100)
        )
        db.session.add(user)
        db.session.commit()
        
        # Log the request
        log_api_request('new_user', '/api/users/register', {'username': username, 'email': email})
        
        # Authenticate user to get access token
        auth_data = authenticate_user(username, password)
        
        return jsonify(auth_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(format_error_response(f"Error creating user: {str(e)}", 500)), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and get access token.
    
    Request body:
        username: Username or email (required)
        password: Password (required)
        
    Returns:
        User data with access token
    """
    data = request.json or {}
    
    # Validate required fields
    if 'username' not in data or 'password' not in data:
        return jsonify(format_error_response("Username/email and password are required", 400)), 400
    
    username = data['username']
    password = data['password']
    
    # Authenticate user
    auth_data = authenticate_user(username, password)
    
    if not auth_data:
        return jsonify(format_error_response("Invalid credentials", 401)), 401
    
    # Log the request
    log_api_request('user_login', '/api/users/login', {'username': username})
    
    return jsonify(auth_data)

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user data.
    
    Returns:
        Current user data
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    # Log the request
    log_api_request(str(user.id), '/api/users/me', {})
    
    return jsonify(user.to_dict())

@user_bp.route('/me/api-key', methods=['POST'])
@jwt_required()
def refresh_api_key():
    """
    Generate a new API key for the current user.
    
    Returns:
        New API key
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    # Generate new API key
    new_api_key = user.refresh_api_key()
    db.session.commit()
    
    # Log the request
    log_api_request(str(user.id), '/api/users/me/api-key', {})
    
    return jsonify({
        "success": True,
        "api_key": new_api_key
    })

@user_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def update_password():
    """
    Update current user's password.
    
    Request body:
        current_password: Current password (required)
        new_password: New password (required)
        
    Returns:
        Success message
    """
    data = request.json or {}
    
    # Validate required fields
    if 'current_password' not in data or 'new_password' not in data:
        return jsonify(format_error_response("Current password and new password are required", 400)), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Validate new password
    if len(new_password) < 8:
        return jsonify(format_error_response("New password must be at least 8 characters long", 400)), 400
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    # Verify current password
    if not user.verify_password(current_password):
        return jsonify(format_error_response("Current password is incorrect", 401)), 401
    
    # Update password
    user.update_password(new_password)
    db.session.commit()
    
    # Log the request
    log_api_request(str(user.id), '/api/users/me/password', {})
    
    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    })

@user_bp.route('/me/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """
    Get current user's API usage statistics.
    
    Returns:
        API usage statistics
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    # Log the request
    log_api_request(str(user.id), '/api/users/me/usage', {})
    
    return jsonify({
        "api_calls_count": user.api_calls_count,
        "daily_limit": user.daily_limit,
        "remaining_calls": max(0, user.daily_limit - user.api_calls_count)
    })

# Admin routes

@user_bp.route('/', methods=['GET'])
@require_auth
@require_admin
def list_users():
    """
    List all users (admin only).
    
    Returns:
        List of users
    """
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user(user_id):
    """
    Get user by ID (admin only).
    
    URL parameters:
        user_id: User ID
        
    Returns:
        User data
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    return jsonify(user.to_dict())

@user_bp.route('/<int:user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    """
    Update user (admin only).
    
    URL parameters:
        user_id: User ID
        
    Request body:
        is_active: User active status (optional)
        is_admin: User admin status (optional)
        daily_limit: Daily API call limit (optional)
        
    Returns:
        Updated user data
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    data = request.json or {}
    
    # Update user fields
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    if 'daily_limit' in data:
        try:
            daily_limit = int(data['daily_limit'])
            if daily_limit < 0:
                return jsonify(format_error_response("Daily limit must be a positive integer", 400)), 400
            user.daily_limit = daily_limit
        except ValueError:
            return jsonify(format_error_response("Daily limit must be a valid integer", 400)), 400
    
    db.session.commit()
    
    # Log the request
    log_api_request(str(user.id), f'/api/users/{user_id}', data)
    
    return jsonify(user.to_dict())

@user_bp.route('/<int:user_id>/reset-usage', methods=['POST'])
@require_auth
@require_admin
def reset_user_usage(user_id):
    """
    Reset user's API usage counter (admin only).
    
    URL parameters:
        user_id: User ID
        
    Returns:
        Success message
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify(format_error_response("User not found", 404)), 404
    
    user.reset_api_calls()
    db.session.commit()
    
    # Log the request
    log_api_request(str(user.id), f'/api/users/{user_id}/reset-usage', {})
    
    return jsonify({
        "success": True,
        "message": f"API usage counter reset for user {user.username}"
    })
