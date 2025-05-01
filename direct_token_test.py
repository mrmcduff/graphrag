#!/usr/bin/env python3
"""
Direct test of Google token handling without involving the server.

This script directly tests the token decoding logic used in the user_routes.py
endpoints to validate and extract information from Google OAuth tokens.
"""

import os
import sys
import base64
import json
import argparse


def decode_token(token):
    """Decode the Google token and extract claims."""
    print(f"Decoding token: {token[:20]}...")

    try:
        # Split the token to get the parts (header, payload, signature)
        parts = token.split(".")
        if len(parts) < 2:
            print("❌ Invalid token format - not enough segments")
            return False

        # Get the payload (second part)
        payload_base64 = parts[1]

        # Fix padding for base64 decoding
        padded = payload_base64 + ("=" * (4 - len(payload_base64) % 4))

        # Decode the base64 with URL-safe character replacements
        decoded_bytes = base64.b64decode(padded.replace("-", "+").replace("_", "/"))

        # Convert to JSON
        payload = json.loads(decoded_bytes)

        # Check for email
        email = payload.get("email")
        if email:
            print(f"✅ Successfully extracted email: {email}")
        else:
            print("❌ No email found in token")

        # Print all claims
        print("\nToken claims:")
        for key, value in payload.items():
            print(f"  {key}: {value}")

        return True
    except Exception as e:
        print(f"❌ Error decoding token: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return False


def simulate_endpoint_logic(token):
    """Simulate the endpoint logic in user_routes.py."""
    print("\n=== Simulating /api/users/me endpoint logic ===")

    try:
        # Check Authorization header format
        if not token or not token.startswith("eyJ"):
            print("❌ Invalid token format (should start with 'eyJ')")
            return False

        # Split the token and get the header
        token_parts = token.split(".")
        if len(token_parts) < 1:
            print("❌ Invalid token format - not enough segments")
            return False

        # Decode header
        header_padded = token_parts[0] + "=" * (4 - len(token_parts[0]) % 4)
        header_bytes = base64.b64decode(
            header_padded.replace("-", "+").replace("_", "/")
        )
        header = json.loads(header_bytes)
        print(f"Token header: {header}")
        print(f"Token algorithm: {header.get('alg')}")

        # Decode payload
        padded = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
        decoded_bytes = base64.b64decode(padded.replace("-", "+").replace("_", "/"))
        payload = json.loads(decoded_bytes)

        # Extract email
        email = payload.get("email")
        if not email:
            print("❌ No email found in token")
            return False

        print(f"✅ Email found: {email}")
        print("✅ Google token validation successful")

        # In the real endpoint, we would:
        # 1. Lookup user by email
        # 2. Create user if authorized and not found
        # 3. Return user data

        return True
    except Exception as e:
        print(f"❌ Error in endpoint simulation: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Google token decoding directly")
    parser.add_argument("token", help="The Google token to test")

    args = parser.parse_args()

    print("==== Direct Google Token Test ====")

    # Basic token decoding
    decode_success = decode_token(args.token)

    if decode_success:
        # Simulate the endpoint logic
        simulate_endpoint_logic(args.token)

    print("\n==== Test Complete ====")


if __name__ == "__main__":
    main()
