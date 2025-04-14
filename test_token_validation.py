#!/usr/bin/env python3
"""
Test script for token validation in the GraphRAG API.

This script tests the Google token validation flow to help debug authentication issues.
"""

import sys
import os
import json
import base64
import requests
import argparse
from datetime import datetime
import traceback

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import required modules
try:
    from src.api.models import User, db
    from src.api.auth_routes import AUTHORIZED_EMAILS
except ImportError as e:
    print(f"Warning: Could not import models - running without DB validation: {e}")
    AUTHORIZED_EMAILS = []


def decode_token(token):
    """Decode a JWT token and return its payload."""
    try:
        # Split the token and get the payload part (second part)
        token_parts = token.split(".")
        if len(token_parts) < 2:
            return None

        # Fix padding for base64 decoding
        padded = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
        decoded_bytes = base64.b64decode(padded.replace("-", "+").replace("_", "/"))
        payload = json.loads(decoded_bytes)
        return payload
    except Exception as e:
        print(f"Error decoding token: {str(e)}")
        print(traceback.format_exc())
        return None


def check_token_algorithm(token):
    """Check the token's algorithm."""
    try:
        # Split the token and get the header part (first part)
        token_parts = token.split(".")
        if len(token_parts) < 1:
            return None

        # Fix padding for base64 decoding
        padded = token_parts[0] + "=" * (4 - len(token_parts[0]) % 4)
        decoded_bytes = base64.b64decode(padded.replace("-", "+").replace("_", "/"))
        header = json.loads(decoded_bytes)

        print(f"Token header: {header}")
        return header.get("alg")
    except Exception as e:
        print(f"Error checking token algorithm: {str(e)}")
        print(traceback.format_exc())
        return None


def simulate_token_validation(token):
    """Simulate the token validation logic in auth.py."""
    print("\n===== Token Validation Simulation =====")

    if not token.startswith("eyJ"):
        print("❌ Not a valid JWT token format (should start with 'eyJ')")
        return False

    alg = check_token_algorithm(token)
    if alg:
        print(f"✅ Token algorithm: {alg}")
        if alg == "RS256":
            print(
                "Note: RS256 is used by Google, make sure Flask-JWT-Extended is configured to accept it"
            )

    payload = decode_token(token)
    if not payload:
        print("❌ Failed to decode token payload")
        return False

    print(f"✅ Token decoded successfully")

    # Check for email
    email = payload.get("email")
    if not email:
        print("❌ No email found in token payload")
        return False

    print(f"✅ Email found in token: {email}")

    # Check if email is authorized
    if email.lower() in AUTHORIZED_EMAILS:
        print(f"✅ Email {email} is in the authorized list")
    else:
        print(f"❌ Email {email} is NOT in the authorized list")
        print(f"Authorized emails: {AUTHORIZED_EMAILS}")
        if not AUTHORIZED_EMAILS:
            print(
                "Warning: Authorized emails list is empty - could not load from database"
            )

    # Token expiration
    exp = payload.get("exp")
    if exp:
        from time import time

        now = int(time())
        if exp < now:
            print(f"❌ Token expired at {datetime.fromtimestamp(exp).isoformat()}")
            return False
        else:
            print(f"✅ Token is valid until {datetime.fromtimestamp(exp).isoformat()}")

    # Print all claims for debugging
    print("\nToken claims:")
    for key, value in payload.items():
        print(f"  {key}: {value}")

    return True


def test_api_endpoints(token, base_url):
    """Test API endpoints with the token."""
    print("\n===== API Endpoint Tests =====")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Test /api/users/authorize endpoint
    email = decode_token(token).get("email", "")
    print(f"\nTesting /api/users/authorize with email: {email}")
    try:
        response = requests.post(
            f"{base_url}/api/users/authorize",
            headers=headers,
            json={"email": email},
            timeout=10,
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ /api/users/authorize test passed")
        else:
            print("❌ /api/users/authorize test failed")
    except Exception as e:
        print(f"❌ Error testing /api/users/authorize: {str(e)}")
        print(traceback.format_exc())

    # Test /api/users/me endpoint
    print(f"\nTesting /api/users/me")
    try:
        response = requests.get(f"{base_url}/api/users/me", headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ /api/users/me test passed")
        else:
            print("❌ /api/users/me test failed")
            # Try to decode any json error message
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass

            # Additional diagnostics for 422 errors
            if response.status_code == 422:
                print("\nAdditional diagnostics for 422 error:")
                print("- This indicates a JWT validation issue")
                print(
                    "- Check if Flask-JWT-Extended is properly configured to accept RS256 algorithm"
                )
                print("- Make sure JWT_DECODE_ALGORITHMS includes 'RS256'")
                print(
                    "- Check that @jwt_required(optional=True) is used or that @require_auth is used"
                )
    except Exception as e:
        print(f"❌ Error testing /api/users/me: {str(e)}")
        print(traceback.format_exc())

    # Test /api/users/me/api-key endpoint
    print(f"\nTesting /api/users/me/api-key")
    try:
        response = requests.post(
            f"{base_url}/api/users/me/api-key", headers=headers, timeout=10
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ /api/users/me/api-key test passed")
            print(
                "\nALTERNATIVE SOLUTION: Instead of fixing the Google token validation,"
            )
            print("you can use this API key in your React app as an X-API-Key header")
            try:
                api_key = response.json().get("api_key")
                if api_key:
                    print(f"API Key: {api_key}")
            except:
                pass
        else:
            print("❌ /api/users/me/api-key test failed")
    except Exception as e:
        print(f"❌ Error testing /api/users/me/api-key: {str(e)}")
        print(traceback.format_exc())

    # Test /api/game/new endpoint
    print(f"\nTesting /api/game/new")
    try:
        response = requests.post(
            f"{base_url}/api/game/new",
            headers=headers,
            json={"provider_id": 4},  # Anthropic provider
            timeout=10,
        )
        print(f"Status code: {response.status_code}")
        print(
            f"Response: {response.text[:200]}..."
            if len(response.text) > 200
            else f"Response: {response.text}"
        )

        if response.status_code == 200:
            print("✅ /api/game/new test passed")
        else:
            print("❌ /api/game/new test failed")
    except Exception as e:
        print(f"❌ Error testing /api/game/new: {str(e)}")
        print(traceback.format_exc())


def main():
    parser = argparse.ArgumentParser(
        description="Test token validation for GraphRAG API"
    )
    parser.add_argument("token", help="The Google token to test")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL for API tests"
    )
    parser.add_argument(
        "--skip-api", action="store_true", help="Skip API endpoint tests"
    )
    parser.add_argument(
        "--jwt-test", action="store_true", help="Run additional JWT tests"
    )

    args = parser.parse_args()

    print("==== GraphRAG Token Validation Test ====")
    print(f"Token (first 20 chars): {args.token[:20]}...")

    # Validate the token locally
    is_valid = simulate_token_validation(args.token)

    if is_valid and not args.skip_api:
        # Test API endpoints
        test_api_endpoints(args.token, args.url)

    if args.jwt_test:
        try:
            import jwt

            print("\n==== JWT Library Configuration ====")
            print(f"JWT Library version: {jwt.__version__}")
            print(f"Supported algorithms: {jwt.algorithms.get_default_algorithms()}")
        except ImportError:
            print("\nJWT library not available for testing.")

    print("\n==== Test Complete ====")


if __name__ == "__main__":
    main()
