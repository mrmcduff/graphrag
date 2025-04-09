"""
Authentication routes for Google OAuth integration with GraphRAG.

This module provides endpoints for handling Google OAuth authentication and user authorization.
"""
from flask import Blueprint, request, jsonify, current_app
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import db, User
from .utils import format_error_response, log_api_request

# Create a blueprint for the auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/users')

# In-memory list of authorized emails (for simplicity)
# In a production environment, this would be stored in a database
AUTHORIZED_EMAILS: List[str] = []

def load_authorized_emails() -> None:
    """Load authorized emails from a JSON file."""
    try:
        auth_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'authorized_emails.json')
        if os.path.exists(auth_file):
            with open(auth_file, 'r') as f:
                data = json.load(f)
                global AUTHORIZED_EMAILS
                AUTHORIZED_EMAILS = data.get('emails', [])
    except Exception as e:
        print(f"Error loading authorized emails: {e}")
        AUTHORIZED_EMAILS = []

def save_authorized_emails() -> None:
    """Save authorized emails to a JSON file."""
    try:
        auth_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'authorized_emails.json')
        os.makedirs(os.path.dirname(auth_file), exist_ok=True)
        with open(auth_file, 'w') as f:
            json.dump({'emails': AUTHORIZED_EMAILS}, f, indent=2)
    except Exception as e:
        print(f"Error saving authorized emails: {e}")

# Load authorized emails when the module is imported
load_authorized_emails()

@auth_bp.route('/authorize', methods=['POST'])
def authorize_user():
    """
    Check if a user's email is authorized to access the system.
    
    Request body:
        email: User's email address
        
    Returns:
        Authorization status
    """
    data = request.json or {}
    
    if 'email' not in data:
        return jsonify(format_error_response("Email is required", 400)), 400
    
    email = data['email'].lower()
    
    # Log the request (excluding email for privacy)
    log_api_request('auth', '/api/users/authorize', {'action': 'authorize'})
    
    # Check if email is in the authorized list
    is_authorized = email in AUTHORIZED_EMAILS
    
    # If authorized, create or update user in database
    if is_authorized:
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create new user with default settings
            user = User(
                username=email.split('@')[0],
                email=email,
                password=os.urandom(16).hex(),  # Random password since OAuth is used
                is_admin=False,
                daily_limit=100
            )
            db.session.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
    
    return jsonify({
        "authorized": is_authorized,
        "message": "User is authorized" if is_authorized else "User is not authorized"
    })

@auth_bp.route('/authorized-emails', methods=['GET'])
def get_authorized_emails():
    """
    Get the list of authorized emails.
    
    Returns:
        List of authorized emails
    """
    # This endpoint should be protected in production
    return jsonify({
        "emails": AUTHORIZED_EMAILS
    })

@auth_bp.route('/authorized-emails', methods=['POST'])
def add_authorized_email():
    """
    Add an email to the authorized list.
    
    Request body:
        email: Email to add
        
    Returns:
        Updated list of authorized emails
    """
    # This endpoint should be protected in production
    data = request.json or {}
    
    if 'email' not in data:
        return jsonify(format_error_response("Email is required", 400)), 400
    
    email = data['email'].lower()
    
    # Add email if not already in list
    if email not in AUTHORIZED_EMAILS:
        AUTHORIZED_EMAILS.append(email)
        save_authorized_emails()
    
    return jsonify({
        "success": True,
        "emails": AUTHORIZED_EMAILS
    })

@auth_bp.route('/authorized-emails', methods=['DELETE'])
def remove_authorized_email():
    """
    Remove an email from the authorized list.
    
    Request body:
        email: Email to remove
        
    Returns:
        Updated list of authorized emails
    """
    # This endpoint should be protected in production
    data = request.json or {}
    
    if 'email' not in data:
        return jsonify(format_error_response("Email is required", 400)), 400
    
    email = data['email'].lower()
    
    # Remove email if in list
    if email in AUTHORIZED_EMAILS:
        AUTHORIZED_EMAILS.remove(email)
        save_authorized_emails()
    
    return jsonify({
        "success": True,
        "emails": AUTHORIZED_EMAILS
    })
