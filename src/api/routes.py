"""
API Routes for GraphRAG Text Adventure Game.

This module defines all the API endpoints for interacting with the game.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any

from .game_session import GameSession
from .utils import (
    format_error_response,
    log_api_request,
    validate_session_id,
    sanitize_input,
)
from .auth import require_auth

# Create a blueprint for the API routes
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Store active game sessions
game_sessions: Dict[str, GameSession] = {}


@api_bp.route("/game/new", methods=["POST"])
@require_auth
def new_game():
    """
    Create a new game session.

    Request body:
        game_data_dir: Directory containing game data files (optional)
        config: Optional configuration dictionary
        provider_id: LLM provider ID (1-6, default: 4 for Anthropic)

    Returns:
        Initial game state and session ID
    """
    data = request.json or {}
    game_data_dir = data.get("game_data_dir", "data/output")
    config = data.get("config", {})
    provider_id = data.get("provider_id", 4)  # Default to Anthropic
    provider_config = data.get("provider_config", {})

    # Validate provider_id
    if not isinstance(provider_id, int) or provider_id < 1 or provider_id > 6:
        return jsonify(
            format_error_response(
                "Invalid provider_id. Must be an integer between 1 and 6.", 400
            )
        ), 400

    # Validate provider_config
    if not isinstance(provider_config, dict):
        return jsonify(
            format_error_response("provider_config must be a dictionary.", 400)
        ), 400

    # Log the request
    log_api_request("new_session", "/game/new", data)

    try:
        # Create new game session with provider configuration
        session = GameSession(game_data_dir, config, provider_id, provider_config)
        game_sessions[session.session_id] = session

        # Return initial game state
        return jsonify(session.get_initial_state())
    except Exception as e:
        return jsonify(
            format_error_response(f"Error creating game session: {str(e)}")
        ), 500


@api_bp.route("/game/<session_id>/command", methods=["POST"])
@require_auth
def process_command(session_id):
    """
    Process a command for an existing game session.

    URL parameters:
        session_id: Session ID

    Request body:
        command: Command to process

    Returns:
        Command result with formatting metadata
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    data = request.json or {}
    command = sanitize_input(data.get("command", ""))

    # Log the request
    log_api_request(session_id, f"/game/{session_id}/command", data)

    if not command:
        return jsonify(format_error_response("No command provided", 400)), 400

    try:
        # Process the command
        result = game_sessions[session_id].process_command(command)
        return jsonify(result)
    except Exception as e:
        return jsonify(
            format_error_response(f"Error processing command: {str(e)}")
        ), 500


@api_bp.route("/game/<session_id>/save", methods=["POST"])
@require_auth
def save_game(session_id):
    """
    Save the current game state.

    URL parameters:
        session_id: Session ID

    Request body:
        filename: Save file name (optional)

    Returns:
        Success or error message
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    data = request.json or {}
    filename = data.get("filename", f"save_{session_id}.json")

    # Log the request
    log_api_request(session_id, f"/game/{session_id}/save", data)

    try:
        success = game_sessions[session_id].game_state.save_game(filename)
        if success:
            return jsonify({"success": True, "message": f"Game saved to {filename}"})
        else:
            return jsonify(format_error_response("Failed to save game", 500)), 500
    except Exception as e:
        return jsonify(format_error_response(f"Error saving game: {str(e)}", 500)), 500


@api_bp.route("/game/<session_id>/load", methods=["POST"])
@require_auth
def load_game(session_id):
    """
    Load a saved game state.

    URL parameters:
        session_id: Session ID

    Request body:
        filename: Save file name

    Returns:
        Success or error message with updated game state
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    data = request.json or {}
    filename = data.get("filename", "")

    # Log the request
    log_api_request(session_id, f"/game/{session_id}/load", data)

    if not filename:
        return jsonify(format_error_response("No filename provided", 400)), 400

    try:
        success = game_sessions[session_id].game_state.load_game(filename)
        if success:
            # Get updated game state
            context = game_sessions[session_id].game_state.get_current_context()

            return jsonify(
                {
                    "success": True,
                    "message": f"Game loaded from {filename}",
                    "player_location": game_sessions[
                        session_id
                    ].game_state.player_location,
                    "npcs_present": list(context.get("npcs_present", {}).keys()),
                    "items_present": list(context.get("items_present", {}).keys()),
                }
            )
        else:
            return jsonify(format_error_response("Failed to load game", 500)), 500
    except Exception as e:
        return jsonify(format_error_response(f"Error loading game: {str(e)}", 500)), 500


@api_bp.route("/game/<session_id>/state", methods=["GET"])
@require_auth
def get_game_state(session_id):
    """
    Get the current game state.

    URL parameters:
        session_id: Session ID

    Returns:
        Current game state
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    # Log the request
    log_api_request(session_id, f"/game/{session_id}/state", {})

    try:
        session = game_sessions[session_id]
        context = session.game_state.get_current_context()

        return jsonify(
            {
                "player_location": session.game_state.player_location,
                "inventory": session.game_state.inventory,
                "npcs_present": list(context.get("npcs_present", {}).keys()),
                "items_present": list(context.get("items_present", {}).keys()),
                "combat_active": session.combat_system.active_combat is not None,
                "metadata": {
                    "session_id": session_id,
                    "inventory_count": len(session.game_state.inventory),
                },
            }
        )
    except Exception as e:
        return jsonify(
            format_error_response(f"Error getting game state: {str(e)}", 500)
        ), 500


@api_bp.route("/game/<session_id>/llm", methods=["POST"])
@require_auth
def set_llm_provider(session_id):
    """
    Set the LLM provider for a game session.

    URL parameters:
        session_id: Session ID

    Request body:
        provider_id: LLM provider ID (1-6)

    Returns:
        Success or error message
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    data = request.json or {}
    provider_id = data.get("provider_id", 3)  # Default to OpenAI

    # Log the request
    log_api_request(session_id, f"/game/{session_id}/llm", data)

    try:
        game_sessions[session_id].command_processor.setup_llm_provider(provider_id)

        # Map provider ID to name for better feedback
        provider_names = {
            1: "Local API",
            2: "Local direct model",
            3: "OpenAI",
            4: "Anthropic Claude",
            5: "Google Gemini",
            6: "Rule-based (no LLM)",
        }

        provider_name = provider_names.get(provider_id, f"Provider {provider_id}")

        return jsonify(
            {"success": True, "message": f"LLM provider set to {provider_name}"}
        )
    except Exception as e:
        return jsonify(
            format_error_response(f"Error setting LLM provider: {str(e)}", 500)
        ), 500


@api_bp.route("/game/<session_id>", methods=["DELETE"])
@require_auth
def end_game_session(session_id):
    """
    End a game session and clean up resources.

    URL parameters:
        session_id: Session ID

    Returns:
        Success or error message
    """
    # Validate session ID
    if not validate_session_id(session_id) or session_id not in game_sessions:
        return jsonify(format_error_response("Invalid session ID", 404)), 404

    # Log the request
    log_api_request(session_id, f"/game/{session_id}", {"action": "delete"})

    try:
        # Remove the session
        del game_sessions[session_id]
        return jsonify({"success": True, "message": f"Game session {session_id} ended"})
    except Exception as e:
        return jsonify(
            format_error_response(f"Error ending game session: {str(e)}", 500)
        ), 500
