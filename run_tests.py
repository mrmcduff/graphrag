#!/usr/bin/env python3
"""
Test script to verify Google token authentication with a local server.

This script automates testing the GraphRAG API with Google tokens against a locally
running server instance.
"""

import os
import sys
import subprocess
import time
import signal
import argparse


def run_local_server():
    """Start the local server in a subprocess."""
    print("Starting local GraphRAG API server...")
    server_process = subprocess.Popen(
        ["python3", "run_local_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Give the server a moment to start
    time.sleep(2)
    return server_process


def run_token_test(token):
    """Run the token validation test against localhost."""
    print("\nRunning token validation test against local server...")
    test_cmd = [
        "python3",
        "test_token_validation.py",
        token,
        "--url",
        "http://localhost:8000",
    ]
    subprocess.run(test_cmd)


def main():
    parser = argparse.ArgumentParser(
        description="Test Google token authentication locally"
    )
    parser.add_argument("token", help="The Google token to test")
    parser.add_argument(
        "--skip-server",
        action="store_true",
        help="Skip starting a local server (if one is already running)",
    )

    args = parser.parse_args()

    server_process = None

    try:
        if not args.skip_server:
            server_process = run_local_server()

        # Run the token test
        run_token_test(args.token)

        if not args.skip_server:
            print("\nTest complete. Stopping local server...")
    finally:
        # Clean up the server process
        if server_process:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    main()
