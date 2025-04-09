"""
GraphRAG Text Adventure Game API Server.

This module provides the main Flask application for the GraphRAG text adventure game API.
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import argparse
import os
import logging
from typing import Dict, Any
import datetime

from .routes import api_bp
from .user_routes import user_bp
from .auth_routes import auth_bp
from .models import db
from .auth import jwt


def create_app(config: Dict[str, Any] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'api.log')),
            logging.StreamHandler()
        ]
    )
    
    # Apply configuration
    app.config.update(config or {})
    
    # Configure database
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'graphrag.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    
    # Serve static files from client directory
    @app.route('/client/<path:filename>')
    def serve_client_file(filename):
        client_dir = os.path.join(os.path.dirname(__file__), '..', 'client')
        return send_from_directory(client_dir, filename)
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": str(error)}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Server error", "message": str(error)}), 500
    
    # Add a health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok"})
    
    # Add a root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "name": "GraphRAG Text Adventure Game API",
            "version": "1.0.0",
            "endpoints": [
                "/api/game/new",
                "/api/game/<session_id>/command",
                "/api/game/<session_id>/save",
                "/api/game/<session_id>/load",
                "/api/game/<session_id>/state",
                "/api/game/<session_id>/llm",
                "/api/game/<session_id>",
                "/api/users/register",
                "/api/users/login",
                "/api/users/me"
            ]
        })
    
    return app


def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description='Start the GraphRAG Text Adventure API Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--create-admin', action='store_true', help='Create admin user if none exists')
    
    args = parser.parse_args()
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'api.log')),
            logging.StreamHandler()
        ]
    )
    
    # Create and run the app
    app = create_app()
    
    # Create admin user if requested and none exists
    if args.create_admin:
        with app.app_context():
            from .models import User
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                import secrets
                admin_password = secrets.token_urlsafe(12)
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=admin_password,
                    is_admin=True,
                    daily_limit=1000
                )
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user created with username: admin, password: {admin_password}")
                print(f"API Key: {admin.api_key}")
    
    print(f"Starting GraphRAG Text Adventure API Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
