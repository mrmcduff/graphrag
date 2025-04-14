#!/usr/bin/env python3
"""
Run the GraphRAG API server locally for testing.

This script sets up and runs the GraphRAG API server locally with debug mode
enabled for easier testing and development.
"""

import os
import sys

# Add src directory to path for imports
src_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_dir)

# Import server module
from src.api.server import create_app, main

if __name__ == "__main__":
    print("Starting GraphRAG API server locally...")
    print("Server will run on http://localhost:8000")
    print("Press Ctrl+C to stop the server")

    # Set debug environment variables
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["JWT_DECODE_ALGORITHMS"] = (
        "HS256,RS256"  # Enable RS256 for Google tokens
    )

    # Run the server
    main()
