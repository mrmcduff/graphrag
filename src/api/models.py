"""
Database models for the GraphRAG API.

This module defines the database models for user management.
"""

from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256
from datetime import datetime
import uuid
import json

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and API access management."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Usage tracking
    api_calls_count = db.Column(db.Integer, default=0)


class GameSessionModel(db.Model):
    """Model for storing game sessions persistently in the database."""

    __tablename__ = "game_sessions"

    session_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    game_data = db.Column(db.Text, nullable=False)  # JSON serialized game session data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with User model
    user = db.relationship("User", backref=db.backref("game_sessions", lazy=True))
    daily_limit = db.Column(db.Integer, default=100)  # Default API call limit per day

    def __init__(self, username, email, password, is_admin=False, daily_limit=100):
        self.username = username
        self.email = email
        self.password_hash = self.hash_password(password)
        self.api_key = self.generate_api_key()
        self.is_admin = is_admin
        self.daily_limit = daily_limit

    @staticmethod
    def hash_password(password):
        """Hash a password using pbkdf2_sha256."""
        return pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        """Verify a password against the stored hash."""
        return pbkdf2_sha256.verify(password, self.password_hash)

    def update_password(self, password):
        """Update user password."""
        self.password_hash = self.hash_password(password)

    @staticmethod
    def generate_api_key():
        """Generate a unique API key."""
        return uuid.uuid4().hex + uuid.uuid4().hex

    def refresh_api_key(self):
        """Generate a new API key for the user."""
        self.api_key = self.generate_api_key()
        return self.api_key

    def increment_api_calls(self):
        """Increment the API call counter."""
        self.api_calls_count += 1

    def has_exceeded_daily_limit(self):
        """Check if user has exceeded their daily API call limit."""
        return self.api_calls_count >= self.daily_limit

    def reset_api_calls(self):
        """Reset the API call counter."""
        self.api_calls_count = 0

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "api_calls_count": self.api_calls_count,
            "daily_limit": self.daily_limit,
        }


class ApiUsage(db.Model):
    """Model to track API usage per user."""

    __tablename__ = "api_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(36), nullable=True)

    user = db.relationship("User", backref=db.backref("api_usage", lazy=True))

    def __init__(self, user_id, endpoint, session_id=None):
        self.user_id = user_id
        self.endpoint = endpoint
        self.session_id = session_id
