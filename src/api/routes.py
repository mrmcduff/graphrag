"""
API Routes for GraphRAG Text Adventure Game.

This module defines all the API endpoints for interacting with the game.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import os
import time
import json

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
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR in new_game: {str(e)}")
        print(f"TRACEBACK: {error_traceback}")
        
        # Check if we're in debug mode
        debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
        
        if debug_mode:
            # In debug mode, return detailed error information
            return jsonify({
                "error": "Error creating game session",
                "message": str(e),
                "traceback": error_traceback
            }), 500
        else:
            # In production mode, return a generic error message
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
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR in process_command: {str(e)}")
        print(f"TRACEBACK: {error_traceback}")
        
        # Check if we're in debug mode
        debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
        
        if debug_mode:
            # In debug mode, return detailed error information
            return jsonify({
                "error": "Error processing command",
                "message": str(e),
                "traceback": error_traceback
            }), 500
        else:
            # In production mode, return a generic error message
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


@api_bp.route("/worlds/documents", methods=["GET"])
@require_auth
def list_document_folders():
    """
    List available document folders for world creation.

    Returns:
        List of available document folders
    """
    try:
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "documents",
        )

        # Create the directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)

        # Get all subdirectories
        folders = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                folders.append(
                    {
                        "name": item,
                        "path": os.path.join("data", "documents", item),
                        "file_count": len(
                            [f for f in os.listdir(item_path) if f.endswith(".docx")]
                        ),
                    }
                )

        # Add the root documents directory
        docx_count = len([f for f in os.listdir(base_dir) if f.endswith(".docx")])
        if docx_count > 0:
            folders.insert(
                0,
                {
                    "name": "root",
                    "path": os.path.join("data", "documents"),
                    "file_count": docx_count,
                },
            )

        return jsonify({"success": True, "folders": folders})
    except Exception as e:
        return jsonify(
            format_error_response(f"Error listing document folders: {str(e)}", 500)
        ), 500


@api_bp.route("/worlds/available", methods=["GET"])
@require_auth
def list_available_worlds():
    """
    List available serialized worlds.

    Returns:
        List of available worlds
    """
    try:
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "output",
        )

        # Create the directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)

        # Get all subdirectories and the root directory if it has a knowledge graph
        worlds = []

        # Check if the root output directory has a knowledge graph
        if os.path.exists(os.path.join(base_dir, "knowledge_graph.gexf")):
            worlds.append(
                {
                    "name": "default",
                    "path": "data/output",
                    "created": time.ctime(
                        os.path.getmtime(os.path.join(base_dir, "knowledge_graph.gexf"))
                    ),
                    "entities_count": count_entities(base_dir),
                }
            )

        # Check subdirectories
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, "knowledge_graph.gexf")
            ):
                worlds.append(
                    {
                        "name": item,
                        "path": os.path.join("data", "output", item),
                        "created": time.ctime(
                            os.path.getmtime(
                                os.path.join(item_path, "knowledge_graph.gexf")
                            )
                        ),
                        "entities_count": count_entities(item_path),
                    }
                )

        return jsonify({"success": True, "worlds": worlds})
    except Exception as e:
        return jsonify(
            format_error_response(f"Error listing available worlds: {str(e)}", 500)
        ), 500


def count_entities(world_dir):
    """Helper function to count entities in a world directory"""
    counts = {"locations": 0, "characters": 0, "items": 0}

    for entity_type in counts.keys():
        file_path = os.path.join(world_dir, f"game_{entity_type}.csv")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    # Subtract 1 for the header row
                    counts[entity_type] = sum(1 for _ in f) - 1
            except:
                pass

    return counts


@api_bp.route("/worlds/create", methods=["POST"])
@require_auth
def create_new_world():
    """
    Create a new world from documents.

    Request body:
        documents_dir: Path to directory containing documents
        output_name: Name for the output world (optional, defaults to input directory name)
        chunk_size: Maximum chunk size in tokens (optional)
        overlap: Overlap between chunks in tokens (optional)

    Returns:
        Information about the created world
    """
    data = request.json or {}
    documents_dir = data.get("documents_dir")
    output_name = data.get(
        "output_name"
    )  # Will default to input directory name in document_processor
    chunk_size = data.get("chunk_size", 512)
    overlap = data.get("overlap", 50)

    # Log the request
    log_api_request("create_world", "/worlds/create", data)

    if not documents_dir:
        return jsonify(
            format_error_response("No documents directory specified", 400)
        ), 400

    try:
        # Convert relative path to absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        abs_documents_dir = os.path.join(base_dir, documents_dir)
        abs_output_dir = os.path.join(base_dir, "data", "output")

        # Import the document processor
        from src.document_processor import main as process_documents

        # Process the documents - output_name will be derived from documents_dir if not provided
        world_dir = process_documents(
            documents_dir=abs_documents_dir,
            output_dir=abs_output_dir,
            chunk_size=chunk_size,
            overlap=overlap,
            output_name=output_name,
        )

        # Get the relative path for the response
        rel_world_dir = os.path.relpath(world_dir, base_dir)

        return jsonify(
            {
                "success": True,
                "message": f"World created successfully",
                "world": {
                    "name": os.path.basename(world_dir),
                    "path": rel_world_dir,
                    "created": time.ctime(
                        os.path.getmtime(
                            os.path.join(world_dir, "knowledge_graph.gexf")
                        )
                    ),
                    "entities_count": count_entities(world_dir),
                },
            }
        )
    except Exception as e:
        return jsonify(
            format_error_response(f"Error creating world: {str(e)}", 500)
        ), 500


@api_bp.route("/game/new/from_world", methods=["POST"])
@require_auth
def new_game_from_world():
    """
    Create a new game session from a specific serialized world.

    Request body:
        world_path: Path to the serialized world
        config: Optional configuration dictionary
        provider_id: LLM provider ID (1-6, default: 4 for Anthropic)

    Returns:
        Initial game state and session ID
    """
    data = request.json or {}
    world_path = data.get("world_path")
    config = data.get("config", {})
    provider_id = data.get("provider_id", 4)  # Default to Anthropic
    provider_config = data.get("provider_config", {})

    # Log the request
    log_api_request("new_session_from_world", "/game/new/from_world", data)

    if not world_path:
        return jsonify(format_error_response("No world path specified", 400)), 400

    # Validate provider_id
    if not isinstance(provider_id, int) or provider_id < 1 or provider_id > 6:
        return jsonify(
            format_error_response(
                "Invalid provider_id. Must be an integer between 1 and 6.", 400
            )
        ), 400

    try:
        # Convert relative path to absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        abs_world_path = os.path.join(base_dir, world_path)

        # Verify the world exists
        if not os.path.exists(os.path.join(abs_world_path, "knowledge_graph.gexf")):
            return jsonify(
                format_error_response(f"World not found at {world_path}", 404)
            ), 404

        # Create new game session with the specified world
        session = GameSession(abs_world_path, config, provider_id, provider_config)
        game_sessions[session.session_id] = session

        # Return initial game state
        return jsonify(session.get_initial_state())
    except Exception as e:
        return jsonify(
            format_error_response(f"Error creating game session: {str(e)}")
        ), 500
