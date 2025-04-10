"""
Utility functions for the GraphRAG API.

This module provides helper functions for the API implementation.
"""

from typing import Dict, Any, List, Optional
import json
import os
import time


def format_error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Format an error response.

    Args:
        message: Error message
        status_code: HTTP status code

    Returns:
        Formatted error response
    """
    return {"error": True, "message": message, "status_code": status_code}


def log_api_request(
    session_id: str, endpoint: str, request_data: Dict[str, Any]
) -> None:
    """
    Log an API request for debugging and analytics.

    Args:
        session_id: Session ID
        endpoint: API endpoint
        request_data: Request data
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "api")

    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{session_id}.log")

    log_entry = {"timestamp": timestamp, "endpoint": endpoint, "request": request_data}

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def validate_session_id(session_id: str) -> bool:
    """
    Validate a session ID format.

    Args:
        session_id: Session ID to validate

    Returns:
        True if valid, False otherwise
    """
    import uuid

    try:
        uuid_obj = uuid.UUID(session_id)
        return str(uuid_obj) == session_id
    except (ValueError, AttributeError):
        return False


def get_command_suggestions(context: Dict[str, Any]) -> List[str]:
    """
    Generate command suggestions based on game context.

    Args:
        context: Game context

    Returns:
        List of suggested commands
    """
    suggestions = ["look around"]

    # Add movement suggestions
    if "exits" in context:
        for exit_name in context["exits"]:
            suggestions.append(f"go to {exit_name}")

    # Add NPC interaction suggestions
    if "npcs_present" in context:
        for npc in context["npcs_present"]:
            suggestions.append(f"talk to {npc}")

    # Add item interaction suggestions
    if "items_present" in context:
        for item in context["items_present"]:
            suggestions.append(f"examine {item}")
            suggestions.append(f"take {item}")

    # Add combat suggestions if enemies are present
    if any(
        context.get("npcs_present", {}).get(npc, {}).get("hostile", False)
        for npc in context.get("npcs_present", {})
    ):
        suggestions.append("attack enemy")

    # Add inventory suggestions if player has items
    if context.get("inventory_count", 0) > 0:
        suggestions.append("inventory")
        suggestions.append("use item")

    # Always include help
    suggestions.append("help")

    return suggestions


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    # Remove any potentially dangerous characters
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")

    # Limit length
    if len(sanitized) > 500:
        sanitized = sanitized[:500]

    return sanitized.strip()
