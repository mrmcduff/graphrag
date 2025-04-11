"""
World Management API Routes for GraphRAG Text Adventure Game.

This module defines API endpoints for creating, listing, and managing game worlds.
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List
import os
import shutil
import sys
import time
from werkzeug.utils import secure_filename

from .utils import (
    format_error_response,
    log_api_request,
    sanitize_input,
)
from .auth import require_auth

# Create a blueprint for the world management routes
world_bp = Blueprint("world", __name__, url_prefix="/api/worlds")

# Allowed file extensions
ALLOWED_EXTENSIONS = {"docx"}


def allowed_file(filename):
    """Check if a filename has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_base_dir():
    """Get the base directory of the application."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_documents_dir():
    """Get the documents directory path."""
    return os.path.join(get_base_dir(), "data", "documents")


def get_output_dir():
    """Get the output directory path."""
    return os.path.join(get_base_dir(), "data", "output")


@world_bp.route("/list", methods=["GET"])
@require_auth
def list_worlds():
    """
    List existing generatable worlds.

    Returns:
        List of available document folders
    """
    # Log the request
    log_api_request("list_worlds", "/worlds/list", {})

    try:
        # Import the document processor
        sys.path.append(get_base_dir())
        from src.document_processor import list_document_folders

        # Get the documents directory
        documents_dir = get_documents_dir()

        # Create the directory if it doesn't exist
        os.makedirs(documents_dir, exist_ok=True)

        # Get all subdirectories
        folders = []
        for item in os.listdir(documents_dir):
            item_path = os.path.join(documents_dir, item)
            if os.path.isdir(item_path):
                docx_count = len(
                    [f for f in os.listdir(item_path) if f.endswith(".docx")]
                )
                folders.append(
                    {
                        "name": item,
                        "path": os.path.join("data/documents", item),
                        "document_count": docx_count,
                        "created": time.ctime(os.path.getctime(item_path)),
                    }
                )

        # Add the root documents directory
        docx_count = len([f for f in os.listdir(documents_dir) if f.endswith(".docx")])
        if docx_count > 0:
            folders.insert(
                0,
                {
                    "name": "root",
                    "path": "data/documents",
                    "document_count": docx_count,
                    "created": time.ctime(os.path.getctime(documents_dir)),
                },
            )

        return jsonify({"success": True, "worlds": folders})
    except Exception as e:
        return jsonify(
            format_error_response(f"Error listing worlds: {str(e)}", 500)
        ), 500


@world_bp.route("/create", methods=["POST"])
@require_auth
def create_world():
    """
    Create a new world folder.

    Request body:
        name: Name for the new world folder

    Returns:
        Information about the created world folder
    """
    data = request.json or {}
    world_name = sanitize_input(data.get("name", ""))

    # Log the request
    log_api_request("create_world", "/worlds/create", data)

    if not world_name:
        return jsonify(format_error_response("No world name provided", 400)), 400

    # Secure the filename to prevent directory traversal
    world_name = secure_filename(world_name)

    try:
        # Get the documents directory
        documents_dir = get_documents_dir()

        # Create the directory if it doesn't exist
        os.makedirs(documents_dir, exist_ok=True)

        # Check if the world already exists
        world_path = os.path.join(documents_dir, world_name)
        if os.path.exists(world_path):
            return jsonify(
                format_error_response(f"World '{world_name}' already exists", 400)
            ), 400

        # Create the world directory
        os.makedirs(world_path, exist_ok=True)

        return jsonify(
            {
                "success": True,
                "message": f"World '{world_name}' created successfully",
                "world": {
                    "name": world_name,
                    "path": os.path.join("data/documents", world_name),
                    "document_count": 0,
                    "created": time.ctime(os.path.getctime(world_path)),
                },
            }
        )
    except Exception as e:
        return jsonify(
            format_error_response(f"Error creating world: {str(e)}", 500)
        ), 500


@world_bp.route("/upload", methods=["POST"])
@require_auth
def upload_documents():
    """
    Upload documents to a world folder.

    Form data:
        world_name: Name of the world folder
        files: Document files to upload (must be .docx)

    Returns:
        Information about the uploaded documents
    """
    # Log the request
    log_api_request(
        "upload_documents",
        "/worlds/upload",
        {"world_name": request.form.get("world_name")},
    )

    if "world_name" not in request.form:
        return jsonify(format_error_response("No world name provided", 400)), 400

    if "files" not in request.files:
        return jsonify(format_error_response("No files provided", 400)), 400

    world_name = sanitize_input(request.form.get("world_name"))
    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        return jsonify(format_error_response("No files selected", 400)), 400

    # Secure the world name to prevent directory traversal
    world_name = secure_filename(world_name)

    try:
        # Get the documents directory
        documents_dir = get_documents_dir()

        # Check if the world exists
        world_path = os.path.join(documents_dir, world_name)
        if not os.path.exists(world_path):
            return jsonify(
                format_error_response(f"World '{world_name}' does not exist", 404)
            ), 404

        # Upload each file
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(world_path, filename)
                file.save(file_path)
                uploaded_files.append(
                    {
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "uploaded": time.ctime(os.path.getctime(file_path)),
                    }
                )

        # Get the updated document count
        docx_count = len([f for f in os.listdir(world_path) if f.endswith(".docx")])

        return jsonify(
            {
                "success": True,
                "message": f"Uploaded {len(uploaded_files)} documents to world '{world_name}'",
                "world": {
                    "name": world_name,
                    "path": os.path.join("data/documents", world_name),
                    "document_count": docx_count,
                    "created": time.ctime(os.path.getctime(world_path)),
                },
                "uploaded_files": uploaded_files,
            }
        )
    except Exception as e:
        return jsonify(
            format_error_response(f"Error uploading documents: {str(e)}", 500)
        ), 500


@world_bp.route("/generate", methods=["POST"])
@require_auth
def generate_world():
    """
    Generate a world from documents.

    Request body:
        world_name: Name of the world folder
        chunk_size: Maximum chunk size in tokens (optional)
        overlap: Overlap between chunks in tokens (optional)
        output_name: Optional name for the output world
        interactive_llm_selection: Whether to prompt for LLM selection (optional, default: false)
        skip_graph: Whether to skip knowledge graph generation (optional, default: false)
        debug: Whether to enable debug output for LLM interactions (optional, default: false)

    Returns:
        Information about the generated world
    """
    data = request.json or {}
    world_name = sanitize_input(data.get("world_name", ""))
    chunk_size = data.get("chunk_size", 512)
    overlap = data.get("overlap", 50)
    output_name = data.get("output_name")
    interactive_llm_selection = data.get("interactive_llm_selection", False)
    skip_graph = data.get("skip_graph", False)
    debug = data.get("debug", False)

    # Log the request
    log_api_request("generate_world", "/worlds/generate", data)

    if not world_name:
        return jsonify(format_error_response("No world name provided", 400)), 400

    # Secure the world name to prevent directory traversal
    world_name = secure_filename(world_name)

    try:
        # Get the documents directory
        documents_dir = get_documents_dir()
        output_dir = get_output_dir()

        # Check if the world exists
        world_path = os.path.join(documents_dir, world_name)
        if not os.path.exists(world_path):
            return jsonify(
                format_error_response(f"World '{world_name}' does not exist", 404)
            ), 404

        # Check if there are any documents in the world
        docx_files = [f for f in os.listdir(world_path) if f.endswith(".docx")]
        if not docx_files:
            return jsonify(
                format_error_response(f"World '{world_name}' has no documents", 400)
            ), 400

        # Import the document processor and Anthropic client
        sys.path.append(get_base_dir())
        from src.document_processor import main as process_documents
        from src.llm.anthropic_client import AnthropicClient

        # Create Anthropic client for quest extraction if not in interactive mode
        anthropic_client = None
        if not interactive_llm_selection and os.environ.get("ANTHROPIC_API_KEY"):
            anthropic_client = AnthropicClient()
            print(
                f"Using Anthropic client for quest extraction: {anthropic_client.name}"
            )

        # Process the documents with the Anthropic client or interactive selection
        world_dir = process_documents(
            documents_dir=world_path,
            output_dir=output_dir,
            chunk_size=chunk_size,
            overlap=overlap,
            output_name=output_name,
            llm_client=anthropic_client,
            interactive_llm_selection=interactive_llm_selection,
            skip_graph=skip_graph,
            debug=debug,
        )

        # Get the relative path for the response
        rel_world_dir = os.path.relpath(world_dir, get_base_dir())

        # Count entities
        from src.api.routes import count_entities

        return jsonify(
            {
                "success": True,
                "message": f"World '{world_name}' generated successfully",
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
            format_error_response(f"Error generating world: {str(e)}", 500)
        ), 500
