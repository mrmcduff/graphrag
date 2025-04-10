# GraphRAG API Documentation

This document provides a comprehensive overview of all API endpoints available in the GraphRAG Text Adventure Game system.

## Authentication

Most API endpoints require authentication. Authentication is handled via JWT tokens obtained through Google OAuth.

## Game Session Endpoints

### Create New Game

Creates a new game session with optional configuration.

- **URL**: `/api/game/new`
- **Method**: `POST`
- **Auth Required**: Yes
- **Request Body**:
  ```json
  {
    "game_data_dir": "data/output",  // Optional, directory containing game data files
    "config": {},                    // Optional, configuration dictionary
    "provider_id": 4,                // Optional, LLM provider ID (1-6, default: 4 for Anthropic)
    "provider_config": {}            // Optional, provider-specific configuration
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Initial game state and session ID
  ```json
  {
    "session_id": "abc123",
    "initial_text": "Welcome to the game...",
    "metadata": {
      "player_location": "Starting Room",
      "inventory_count": 0,
      "combat_active": false
    }
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"error": "Invalid provider_id. Must be an integer between 1 and 6."}`
  - **Code**: 500
  - **Content**: `{"error": "Error creating game session: [error message]"}`

### Process Command

Process a command for an existing game session.

- **URL**: `/api/game/<session_id>/command`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Request Body**:
  ```json
  {
    "command": "look around"  // Command to process
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Command result with formatting metadata
  ```json
  {
    "text": "You see a room with...",
    "metadata": {
      "player_location": "Room Name",
      "inventory_count": 1,
      "combat_active": false
    }
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 400
  - **Content**: `{"error": "No command provided"}`
  - **Code**: 500
  - **Content**: `{"error": "Error processing command: [error message]"}`

### Save Game

Save the current game state.

- **URL**: `/api/game/<session_id>/save`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Request Body**:
  ```json
  {
    "filename": "save_abc123.json"  // Optional, save file name
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Success message
  ```json
  {
    "success": true,
    "message": "Game saved successfully",
    "filename": "save_abc123.json"
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 500
  - **Content**: `{"error": "Error saving game: [error message]"}`

### Load Game

Load a saved game state.

- **URL**: `/api/game/<session_id>/load`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Request Body**:
  ```json
  {
    "filename": "save_abc123.json"  // Save file name to load
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Success message with updated game state
  ```json
  {
    "success": true,
    "message": "Game loaded successfully",
    "state": {
      "text": "You are in a room...",
      "metadata": {
        "player_location": "Room Name",
        "inventory_count": 1,
        "combat_active": false
      }
    }
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 400
  - **Content**: `{"error": "No filename provided"}`
  - **Code**: 404
  - **Content**: `{"error": "Save file not found"}`
  - **Code**: 500
  - **Content**: `{"error": "Error loading game: [error message]"}`

### Get Game State

Get the current game state.

- **URL**: `/api/game/<session_id>/state`
- **Method**: `GET`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Success Response**:
  - **Code**: 200
  - **Content**: Current game state
  ```json
  {
    "text": "You are in a room...",
    "metadata": {
      "player_location": "Room Name",
      "inventory_count": 1,
      "combat_active": false
    }
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 500
  - **Content**: `{"error": "Error getting game state: [error message]"}`

### Set LLM Provider

Set the LLM provider for a game session.

- **URL**: `/api/game/<session_id>/llm`
- **Method**: `POST`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Request Body**:
  ```json
  {
    "provider_id": 4,  // LLM provider ID (1-6)
    "provider_config": {
      "model": "claude-3-haiku-20240307"  // Optional, provider-specific configuration
    }
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Success message
  ```json
  {
    "success": true,
    "message": "LLM provider set to Anthropic Claude",
    "provider_id": 4
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 400
  - **Content**: `{"error": "Invalid provider_id. Must be an integer between 1 and 6."}`
  - **Code**: 500
  - **Content**: `{"error": "Error setting LLM provider: [error message]"}`

### End Game Session

End a game session and clean up resources.

- **URL**: `/api/game/<session_id>`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **URL Parameters**: `session_id` - ID of the game session
- **Success Response**:
  - **Code**: 200
  - **Content**: Success message
  ```json
  {
    "success": true,
    "message": "Game session ended"
  }
  ```
- **Error Response**:
  - **Code**: 404
  - **Content**: `{"error": "Invalid session ID"}`
  - **Code**: 500
  - **Content**: `{"error": "Error ending game session: [error message]"}`

## World Management Endpoints

### List Worlds

List existing generatable worlds.

- **URL**: `/api/worlds/list`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200
  - **Content**: List of available document folders
  ```json
  {
    "success": true,
    "worlds": [
      {
        "name": "fantasy_world",
        "path": "data/documents/fantasy_world",
        "document_count": 3,
        "created": "Thu Apr 10 12:20:00 2025"
      }
    ]
  }
  ```
- **Error Response**:
  - **Code**: 500
  - **Content**: `{"error": "Error listing worlds: [error message]"}`

### Create World

Create a new world folder.

- **URL**: `/api/worlds/create`
- **Method**: `POST`
- **Auth Required**: Yes
- **Request Body**:
  ```json
  {
    "name": "fantasy_world"  // Name for the new world folder
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Information about the created world folder
  ```json
  {
    "success": true,
    "message": "World 'fantasy_world' created successfully",
    "world": {
      "name": "fantasy_world",
      "path": "data/documents/fantasy_world",
      "document_count": 0,
      "created": "Thu Apr 10 12:20:00 2025"
    }
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"error": "No world name provided"}`
  - **Code**: 400
  - **Content**: `{"error": "World 'fantasy_world' already exists"}`
  - **Code**: 500
  - **Content**: `{"error": "Error creating world: [error message]"}`

### Upload Documents

Upload documents to a world folder.

- **URL**: `/api/worlds/upload`
- **Method**: `POST`
- **Auth Required**: Yes
- **Form Data**:
  - `world_name`: Name of the world folder
  - `files`: Document files to upload (must be .docx)
- **Success Response**:
  - **Code**: 200
  - **Content**: Information about the uploaded documents
  ```json
  {
    "success": true,
    "message": "Uploaded 2 documents to world 'fantasy_world'",
    "world": {
      "name": "fantasy_world",
      "path": "data/documents/fantasy_world",
      "document_count": 2,
      "created": "Thu Apr 10 12:20:00 2025"
    },
    "uploaded_files": [
      {
        "name": "document1.docx",
        "size": 12345,
        "uploaded": "Thu Apr 10 12:21:00 2025"
      },
      {
        "name": "document2.docx",
        "size": 67890,
        "uploaded": "Thu Apr 10 12:21:00 2025"
      }
    ]
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"error": "No world name provided"}`
  - **Code**: 400
  - **Content**: `{"error": "No files provided"}`
  - **Code**: 400
  - **Content**: `{"error": "No files selected"}`
  - **Code**: 404
  - **Content**: `{"error": "World 'fantasy_world' does not exist"}`
  - **Code**: 500
  - **Content**: `{"error": "Error uploading documents: [error message]"}`

### Generate World

Generate a world from documents.

- **URL**: `/api/worlds/generate`
- **Method**: `POST`
- **Auth Required**: Yes
- **Request Body**:
  ```json
  {
    "world_name": "fantasy_world",  // Name of the world folder
    "chunk_size": 512,              // Optional, maximum chunk size in tokens
    "overlap": 50,                  // Optional, overlap between chunks in tokens
    "output_name": "fantasy_game"   // Optional, name for the output world
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Information about the generated world
  ```json
  {
    "success": true,
    "message": "World 'fantasy_world' generated successfully",
    "world": {
      "name": "fantasy_game",
      "path": "data/output/fantasy_game",
      "created": "Thu Apr 10 12:25:00 2025",
      "entities_count": {
        "locations": 10,
        "characters": 15,
        "items": 20
      }
    }
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"error": "No world name provided"}`
  - **Code**: 404
  - **Content**: `{"error": "World 'fantasy_world' does not exist"}`
  - **Code**: 400
  - **Content**: `{"error": "World 'fantasy_world' has no documents"}`
  - **Code**: 500
  - **Content**: `{"error": "Error generating world: [error message]"}`

## User Management Endpoints

### Register User

Register a new user.

- **URL**: `/api/users/register`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "username": "user123",
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Success Response**:
  - **Code**: 201
  - **Content**: User information
  ```json
  {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "api_key": "api_key_123"
  }
  ```
- **Error Response**:
  - **Code**: 400
  - **Content**: `{"error": "Username already taken"}`
  - **Code**: 400
  - **Content**: `{"error": "Email already registered"}`
  - **Code**: 400
  - **Content**: `{"error": "Invalid email format"}`
  - **Code**: 500
  - **Content**: `{"error": "Error registering user: [error message]"}`

### Login User

Login a user and get a JWT token.

- **URL**: `/api/users/login`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "username": "user123",
    "password": "securepassword"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: JWT token
  ```json
  {
    "access_token": "jwt_token_123",
    "user": {
      "id": 1,
      "username": "user123",
      "email": "user@example.com"
    }
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Invalid username or password"}`
  - **Code**: 500
  - **Content**: `{"error": "Error logging in: [error message]"}`

### Get User Info

Get information about the authenticated user.

- **URL**: `/api/users/me`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200
  - **Content**: User information
  ```json
  {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "api_key": "api_key_123",
    "is_admin": false,
    "daily_limit": 100,
    "daily_usage": 25
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Unauthorized"}`
  - **Code**: 500
  - **Content**: `{"error": "Error getting user info: [error message]"}`

### Google OAuth Login

Handle Google OAuth login.

- **URL**: `/api/auth/google`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "credential": "google_id_token"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: JWT token
  ```json
  {
    "access_token": "jwt_token_123",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "is_authorized": true
    }
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Invalid Google ID token"}`
  - **Code**: 403
  - **Content**: `{"error": "Email not authorized to access the API"}`
  - **Code**: 500
  - **Content**: `{"error": "Error processing Google login: [error message]"}`

### List Authorized Emails

List emails authorized to access the API (admin only).

- **URL**: `/api/users/authorized-emails`
- **Method**: `GET`
- **Auth Required**: Yes (Admin)
- **Success Response**:
  - **Code**: 200
  - **Content**: List of authorized emails
  ```json
  {
    "emails": [
      "admin@example.com",
      "user@example.com"
    ]
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Unauthorized"}`
  - **Code**: 403
  - **Content**: `{"error": "Admin access required"}`
  - **Code**: 500
  - **Content**: `{"error": "Error listing authorized emails: [error message]"}`

### Add Authorized Email

Add an email to the authorized list (admin only).

- **URL**: `/api/users/authorized-emails`
- **Method**: `POST`
- **Auth Required**: Yes (Admin)
- **Request Body**:
  ```json
  {
    "email": "newuser@example.com"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Updated list of authorized emails
  ```json
  {
    "emails": [
      "admin@example.com",
      "user@example.com",
      "newuser@example.com"
    ]
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Unauthorized"}`
  - **Code**: 403
  - **Content**: `{"error": "Admin access required"}`
  - **Code**: 400
  - **Content**: `{"error": "Invalid email format"}`
  - **Code**: 409
  - **Content**: `{"error": "Email already authorized"}`
  - **Code**: 500
  - **Content**: `{"error": "Error adding authorized email: [error message]"}`

### Remove Authorized Email

Remove an email from the authorized list (admin only).

- **URL**: `/api/users/authorized-emails`
- **Method**: `DELETE`
- **Auth Required**: Yes (Admin)
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**: Updated list of authorized emails
  ```json
  {
    "emails": [
      "admin@example.com"
    ]
  }
  ```
- **Error Response**:
  - **Code**: 401
  - **Content**: `{"error": "Unauthorized"}`
  - **Code**: 403
  - **Content**: `{"error": "Admin access required"}`
  - **Code**: 404
  - **Content**: `{"error": "Email not found in authorized list"}`
  - **Code**: 500
  - **Content**: `{"error": "Error removing authorized email: [error message]"}`

## Utility Endpoints

### Health Check

Check if the API server is running.

- **URL**: `/health`
- **Method**: `GET`
- **Auth Required**: No
- **Success Response**:
  - **Code**: 200
  - **Content**: `{"status": "ok"}`

### API Index

Get information about the API.

- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: No
- **Success Response**:
  - **Code**: 200
  - **Content**: API information
  ```json
  {
    "name": "GraphRAG Text Adventure Game API",
    "version": "1.0.0",
    "endpoints": [
      "/api/game/new",
      "/api/game/<session_id>/command",
      "/api/game/<session_id>/save",
      "/api/game/<session_id>/load",
      "/api/game/<session_id>/state",
      "/api/game/<session_id>/llm",
      "/api/game/<session_id>",
      "/api/users/register",
      "/api/users/login",
      "/api/users/me",
      "/api/worlds/list",
      "/api/worlds/create",
      "/api/worlds/upload",
      "/api/worlds/generate"
    ]
  }
  ```
