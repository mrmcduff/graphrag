#!/usr/bin/env python3
"""
Run the GraphRAG API server locally for testing.

This script sets up and runs the GraphRAG API server locally with debug mode
enabled for easier testing and development.
"""

import os
import sys
import subprocess

# Activate the virtual environment first
venv_dir = os.path.join(os.path.dirname(__file__), ".venv")
venv_activate = os.path.join(venv_dir, "bin", "activate")
if os.path.exists(venv_activate):
    print(f"Using virtual environment at {venv_dir}")
    # This is hacky, but we need to activate the virtualenv
    activate_cmd = (
        f"source {venv_activate} && python3 -c 'import sys; print(sys.executable)'"
    )
    python_path = subprocess.check_output(activate_cmd, shell=True, text=True).strip()
    print(f"Using Python interpreter: {python_path}")

    # Now run the Flask app directly
    flask_cmd = f"source {venv_activate} && FLASK_APP=src.api.server FLASK_DEBUG=1 JWT_DECODE_ALGORITHMS='HS256,RS256' python3 -m flask run --host=0.0.0.0 --port=8000 --debugger --reload"
    print("Starting Flask development server...")
    print("Server will run on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    subprocess.run(flask_cmd, shell=True)
else:
    # Fall back to normal execution if venv not found
    print("Virtual environment not found. Running directly...")

    # Add src directory to path for imports
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    sys.path.insert(0, src_dir)

    # Import server module
    try:
        from src.api.server import create_app, main

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
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Make sure you have all dependencies installed:")
        print("   python3 -m pip install -r requirements.txt")
        print("2. Or activate your virtual environment:")
        print("   source .venv/bin/activate")
        print("3. Then try running again.")
        sys.exit(1)
