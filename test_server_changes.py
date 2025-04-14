#!/usr/bin/env python3
"""
Test script to verify server configuration for Google OAuth tokens.
"""

print("=== Testing GraphRAG Server Configuration ===")

# Create a Flask app with similar config to test locally
try:
    from flask import Flask
    from flask_jwt_extended import JWTManager

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-key"

    # Set algorithms
    app.config["JWT_ALGORITHM"] = "HS256"
    app.config["JWT_DECODE_ALGORITHMS"] = ["HS256", "RS256"]

    # Print configuration
    print("\nJWT Configuration:")
    for key, value in app.config.items():
        if key.startswith("JWT_"):
            print(f"  {key}: {value}")

    # Initialize JWT
    jwt = JWTManager(app)

    print("\nCreate a simple endpoint for debugging:")
    print("""
@app.route("/api/debug", methods=["GET"])
def debug_endpoint():
    \"\"\"Simple endpoint to verify server configuration.\"\"\"
    return {"status": "ok", "jwt_algorithms": app.config.get("JWT_DECODE_ALGORITHMS")}
    """)

    print("\nAdd this to user_routes.py:")
    print("""
@user_bp.route("/debug", methods=["GET"])
def debug_endpoint():
    \"\"\"Simple endpoint to verify server configuration.\"\"\"
    return jsonify({
        "status": "ok", 
        "jwt_algorithms": current_app.config.get("JWT_DECODE_ALGORITHMS"),
        "jwt_header_type": current_app.config.get("JWT_HEADER_TYPE"),
        "authorized_emails": AUTHORIZED_EMAILS,
        "token_handlers": [rule.endpoint for rule in current_app.url_map.iter_rules() 
                          if "/api/users/me" in rule.rule]
    })
    """)

    print("\nTest instructions:")
    print("1. Add the debug endpoint to user_routes.py")
    print("2. Deploy the updated code")
    print("3. Test with: curl https://your-api-url/api/users/debug")
    print("4. This will show if your changes are being applied")

except ImportError:
    print("Flask and/or Flask-JWT-Extended not installed.")
    print("Add this simple debug endpoint to user_routes.py:")
    print("""
@user_bp.route("/debug", methods=["GET"])
def debug_endpoint():
    \"\"\"Simple endpoint to verify server configuration.\"\"\"
    return jsonify({
        "status": "ok", 
        "jwt_algorithms": current_app.config.get("JWT_DECODE_ALGORITHMS"),
        "jwt_header_type": current_app.config.get("JWT_HEADER_TYPE"),
        "google_token_enabled": True,
        "route_handlers": str(current_app.view_functions)
    })
    """)

print("\nALTERNATIVE SOLUTION: Use API Keys")
print("If you can get the /api/users/me/api-key endpoint working,")
print("you can use the API key with X-API-Key header instead of Google tokens.")
print("Test with: curl -H 'X-API-Key: your-api-key' https://your-api-url/api/game/new")
