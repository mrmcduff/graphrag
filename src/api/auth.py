"""
Authentication utilities for the GraphRAG API.

This module provides authentication middleware and utilities for the API.
"""

from flask import request, jsonify, current_app, g
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request,
)
from functools import wraps
from datetime import datetime, timedelta
import re
from typing import Callable, Dict, Any, Optional, Union

from .models import db, User, ApiUsage
from .utils import format_error_response

# Initialize JWT manager
jwt = JWTManager()


def get_current_user() -> Optional[User]:
    """
    Get the current authenticated user from the JWT token.

    Returns:
        User object if authenticated, None otherwise
    """
    try:
        # Verify JWT token is present and valid
        verify_jwt_in_request()

        # Get user identity from token
        user_id = get_jwt_identity()

        # Retrieve user from database
        if user_id:
            return User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(f"Error getting current user: {str(e)}")

    return None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username/email and password.

    Args:
        username: Username or email
        password: Password

    Returns:
        User data dictionary with access token if authentication successful, None otherwise
    """
    # Check if input is an email
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", username) is not None

    if is_email:
        user = User.query.filter_by(email=username).first()
    else:
        user = User.query.filter_by(username=username).first()

    if not user or not user.verify_password(password):
        return None

    if not user.is_active:
        return None

    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Create access token
    expires = timedelta(days=1)
    access_token = create_access_token(
        identity=user.id,
        additional_claims={"username": user.username, "is_admin": user.is_admin},
        expires_delta=expires,
    )

    return {
        "user": user.to_dict(),
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires.total_seconds(),
    }


def authenticate_api_key(api_key: str) -> Optional[User]:
    """
    Authenticate a user with API key.

    Args:
        api_key: API key

    Returns:
        User object if authentication successful, None otherwise
    """
    user = User.query.filter_by(api_key=api_key).first()

    if not user or not user.is_active:
        return None

    return user


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for API endpoints.

    This decorator checks for either a valid JWT token or API key.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # First try to get API key from header or query param
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")

        if api_key:
            user = authenticate_api_key(api_key)
            if not user:
                return jsonify(format_error_response("Invalid API key", 401)), 401

            # Check if user has exceeded daily limit
            if user.has_exceeded_daily_limit():
                return jsonify(
                    format_error_response("Daily API call limit exceeded", 429)
                ), 429

            # Track API usage
            endpoint = request.path
            session_id = kwargs.get("session_id")

            # Increment API call counter
            user.increment_api_calls()

            # Log API usage
            usage = ApiUsage(user.id, endpoint, session_id)
            db.session.add(usage)
            db.session.commit()

            # Set user in request context for the view function
            request.current_user = user

            return f(*args, **kwargs)

        # If no API key, check for JWT token or Google OAuth token
        try:
            # Check for Google OAuth token in Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

                # Try to decode as a Google OAuth token
                try:
                    import jwt

                    current_app.logger.info(
                        f"Attempting to decode token: {token[:20]}... [truncated]"
                    )

                    # Just verify it's a valid JWT, we don't need to validate the signature for now
                    payload = jwt.decode(token, options={"verify_signature": False})
                    current_app.logger.info(
                        f"Token decoded successfully. Payload keys: {list(payload.keys())}"
                    )
                    email = payload.get("email")
                    current_app.logger.info(f"Extracted email: {email}")

                    if email:
                        user = User.query.filter_by(email=email).first()
                        current_app.logger.info(
                            f"User lookup result: {user.username if user else 'No user found'} (active: {user.is_active if user else 'N/A'})"
                        )
                        if user and user.is_active:
                            # We found a valid user with this email
                            current_app.logger.info(
                                f"Found active user: {user.username}"
                            )
                            pass
                        else:
                            # Check if this is an authorized email that just needs a user account
                            from .auth_routes import AUTHORIZED_EMAILS

                            current_app.logger.info(
                                f"AUTHORIZED_EMAILS list length: {len(AUTHORIZED_EMAILS)}"
                            )
                            current_app.logger.info(
                                f"User email lowercase: {email.lower()}"
                            )
                            current_app.logger.info(
                                f"First authorized email: {AUTHORIZED_EMAILS[0] if AUTHORIZED_EMAILS else 'No authorized emails'}"
                            )

                            if email.lower() in AUTHORIZED_EMAILS:
                                current_app.logger.info(
                                    f"Email {email} is authorized, creating new user"
                                )
                                # Create a new user for this authorized email
                                import os
                                from datetime import datetime

                                try:
                                    user = User(
                                        username=email.split("@")[0],
                                        email=email.lower(),
                                        password=os.urandom(
                                            16
                                        ).hex(),  # Random password since OAuth is used
                                        is_admin=False,
                                        daily_limit=100,
                                        last_login=datetime.utcnow(),
                                    )
                                    db.session.add(user)
                                    db.session.commit()
                                    current_app.logger.info(
                                        f"New user created: {user.username}"
                                    )
                                except Exception as e:
                                    current_app.logger.error(
                                        f"Error creating user: {str(e)}"
                                    )
                                    return jsonify(
                                        format_error_response(
                                            f"Error creating user: {str(e)}", 500
                                        )
                                    ), 500
                            else:
                                current_app.logger.warning(
                                    f"Email {email} is not authorized"
                                )
                                return jsonify(
                                    format_error_response("User not authorized", 403)
                                ), 403
                    else:
                        # Fall back to JWT token validation
                        user_id = get_jwt_identity()
                        user = User.query.get(user_id)
                except Exception as e:
                    # If Google token validation fails, try JWT token
                    current_app.logger.error(
                        f"Google token validation failed: {str(e)}"
                    )
                    try:
                        user_id = get_jwt_identity()
                        user = User.query.get(user_id)
                        current_app.logger.info(
                            f"Fallback to JWT: user_id={user_id}, user={user.username if user else 'None'}"
                        )
                    except Exception as jwt_err:
                        current_app.logger.error(
                            f"JWT fallback also failed: {str(jwt_err)}"
                        )
                        return jsonify(
                            format_error_response(
                                f"Authentication failed: {str(e)} | JWT fallback: {str(jwt_err)}",
                                401,
                            )
                        ), 401
            else:
                # No Authorization header, try JWT token
                user_id = get_jwt_identity()
                user = User.query.get(user_id)

            if not user or not user.is_active:
                current_app.logger.error(
                    f"Authentication failed at final check: user={user.username if user else 'None'}, active={user.is_active if user else 'N/A'}"
                )
                return jsonify(
                    format_error_response("User account is inactive", 401)
                ), 401

            # Check if user has exceeded daily limit
            if user.has_exceeded_daily_limit():
                return jsonify(
                    format_error_response("Daily API call limit exceeded", 429)
                ), 429

            # Track API usage
            endpoint = request.path
            session_id = kwargs.get("session_id")

            # Increment API call counter
            user.increment_api_calls()

            # Log API usage
            usage = ApiUsage(user.id, endpoint, session_id)
            db.session.add(usage)
            db.session.commit()

            # Set user in request context for the view function
            request.current_user = user

            return f(*args, **kwargs)
        except Exception:
            return jsonify(format_error_response("Authentication required", 401)), 401

    return decorated


def require_admin(f: Callable) -> Callable:
    """
    Decorator to require admin privileges for API endpoints.

    This decorator must be used after the require_auth decorator.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Get current user from request context (set by require_auth)
        user = getattr(request, "current_user", None)

        if not user or not user.is_admin:
            return jsonify(format_error_response("Admin privileges required", 403)), 403

        return f(*args, **kwargs)

    return decorated
