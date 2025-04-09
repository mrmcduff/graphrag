"""
GraphRAG Text Adventure Game API Server.

This module provides the main Flask application for the GraphRAG text adventure game API.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import argparse
import os
import logging
from typing import Dict, Any

from .routes import api_bp


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
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
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
                "/api/game/<session_id>"
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
    
    args = parser.parse_args()
    
    # Create log directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
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
    
    print(f"Starting GraphRAG Text Adventure API Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
