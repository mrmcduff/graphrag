# GraphRAG API Documentation

This document provides a comprehensive overview of all API endpoints available in the GraphRAG Text Adventure Game system.

## Authentication

Most API endpoints require authentication. Authentication is handled via JWT tokens obtained through either:

1. **Google OAuth** - For web clients using Google Sign-In
2. **API Key** - For programmatic access using the API key found in HEROKU_CREDENTIALS.md

### API Key Authentication

To authenticate using an API key:

```
POST /api/auth/login
Content-Type: application/json

{
  "api_key": "YOUR_API_KEY_HERE"
}
```

Response:
```json
{
  "access_token": "JWT_TOKEN",
  "user": {
    "id": 1,
    "email": "admin@example.com"
  }
}
```

Once you have the JWT token, include it in the Authorization header for all subsequent requests:

```
Authorization: Bearer JWT_TOKEN
```

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

## Consuming the API from a React Application

### Setting Up a React Client

To consume the GraphRAG API from a React application, follow these steps:

1. **CORS Configuration**: Ensure your React app's origin is added to the allowed CORS origins. See the `cors_updates.md` file for instructions.

2. **API Client Implementation**: Create a service class to handle API requests. Here's a sample implementation:

```javascript
// src/services/graphRagApi.js
import axios from 'axios';

const API_URL = 'https://graphrag-api-a77f8919e96d.herokuapp.com';

class GraphRagApiService {
  constructor() {
    this.axios = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Add auth token to requests if available
    this.axios.interceptors.request.use(config => {
      const token = localStorage.getItem('graphrag_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Authentication
  async login(apiKey) {
    const response = await this.axios.post('/api/auth/login', { api_key: apiKey });
    if (response.data.access_token) {
      localStorage.setItem('graphrag_token', response.data.access_token);
    }
    return response.data;
  }

  async googleLogin(credential) {
    const response = await this.axios.post('/api/auth/google', { credential });
    if (response.data.access_token) {
      localStorage.setItem('graphrag_token', response.data.access_token);
    }
    return response.data;
  }

  logout() {
    localStorage.removeItem('graphrag_token');
  }

  // Game Session Management
  async createNewGame(providerId = 4) {
    const response = await this.axios.post('/api/game/new', { provider_id: providerId });
    return response.data;
  }

  async sendCommand(sessionId, command) {
    const response = await this.axios.post(`/api/game/${sessionId}/command`, { command });
    return response.data;
  }

  async getGameState(sessionId) {
    const response = await this.axios.get(`/api/game/${sessionId}/state`);
    return response.data;
  }

  async endGame(sessionId) {
    const response = await this.axios.delete(`/api/game/${sessionId}`);
    return response.data;
  }

  // Error handler wrapper
  async apiCall(method, ...args) {
    try {
      return await method.apply(this, args);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        // Token expired or invalid
        this.logout();
        window.location.href = '/login';
      }
      throw error;
    }
  }
}

export default new GraphRagApiService();
```

3. **React Context for Authentication**: Create an authentication context to manage the user's authentication state:

```javascript
// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import graphRagApi from '../services/graphRagApi';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('graphrag_token');
    if (token) {
      graphRagApi.axios.get('/api/users/me')
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('graphrag_token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (apiKey) => {
    const data = await graphRagApi.login(apiKey);
    setUser(data.user);
    return data;
  };

  const googleLogin = async (credential) => {
    const data = await graphRagApi.googleLogin(credential);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    graphRagApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, googleLogin, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
```

4. **Game Session Context**: Create a context for managing game sessions:

```javascript
// src/contexts/GameContext.js
import React, { createContext, useState, useContext } from 'react';
import graphRagApi from '../services/graphRagApi';

const GameContext = createContext();

export function GameProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const startNewGame = async (providerId = 4) => {
    setLoading(true);
    try {
      const data = await graphRagApi.createNewGame(providerId);
      setSessionId(data.session_id);
      setGameState(data);
      setHistory([{ type: 'system', text: data.initial_text }]);
      return data;
    } catch (error) {
      console.error('Error starting game:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const sendCommand = async (command) => {
    if (!sessionId) return;
    
    setLoading(true);
    setHistory(prev => [...prev, { type: 'user', text: command }]);
    
    try {
      const data = await graphRagApi.sendCommand(sessionId, command);
      setGameState(data);
      setHistory(prev => [...prev, { type: 'system', text: data.response }]);
      return data;
    } catch (error) {
      console.error('Error sending command:', error);
      setHistory(prev => [...prev, { type: 'error', text: 'Error processing command' }]);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const endGame = async () => {
    if (!sessionId) return;
    
    try {
      await graphRagApi.endGame(sessionId);
      setSessionId(null);
      setGameState(null);
      setHistory([]);
    } catch (error) {
      console.error('Error ending game:', error);
      throw error;
    }
  };

  return (
    <GameContext.Provider value={{
      sessionId,
      gameState,
      history,
      loading,
      startNewGame,
      sendCommand,
      endGame
    }}>
      {children}
    </GameContext.Provider>
  );
}

export function useGame() {
  return useContext(GameContext);
}
```

5. **Usage in Components**: Use the contexts in your React components:

```jsx
// src/App.js
import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { GameProvider } from './contexts/GameContext';
import GameInterface from './components/GameInterface';
import LoginPage from './components/LoginPage';
import PrivateRoute from './components/PrivateRoute';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <AuthProvider>
        <GameProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={
              <PrivateRoute>
                <GameInterface />
              </PrivateRoute>
            } />
          </Routes>
        </GameProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
```

### Error Handling

Implement proper error handling for API requests:

1. **Network Errors**: Handle cases where the API is unreachable
2. **Authentication Errors**: Redirect to login page when the token expires
3. **API Errors**: Display meaningful error messages to users

### Performance Considerations

1. **Caching**: Consider caching game state to reduce API calls
2. **Debouncing**: Implement debouncing for rapid command inputs
3. **Optimistic Updates**: Update UI optimistically before API responses for better UX

### Implementing Suggested Actions

The GraphRAG API provides contextual suggested actions in the game state response. These suggestions help users know what commands are available in their current context. Here's how to implement this feature in your React application:

1. **Extract Suggestions from API Response**: The API returns NPCs, items, and available commands in the game state response:

```javascript
const generateSuggestions = (gameState) => {
  // Default suggestions that are always available
  const suggestions = [
    'look around',
    'inventory',
    'help'
  ];
  
  // Add NPC-based suggestions
  if (gameState.npcs_present && Array.isArray(gameState.npcs_present)) {
    gameState.npcs_present.forEach(npc => {
      suggestions.push(`talk to ${npc}`);
      suggestions.push(`examine ${npc}`);
    });
  }
  
  // Add item-based suggestions
  if (gameState.items_present && Array.isArray(gameState.items_present)) {
    gameState.items_present.forEach(item => {
      suggestions.push(`take ${item}`);
      suggestions.push(`examine ${item}`);
    });
  }
  
  // Add available commands if provided by the API
  if (gameState.metadata && gameState.metadata.available_commands) {
    suggestions.push(...gameState.metadata.available_commands);
  }
  
  // Remove duplicates and limit number of suggestions
  return [...new Set(suggestions)].slice(0, 8);
};
```

2. **Create a Suggestions Component**:

```jsx
// src/components/CommandSuggestions.js
import React from 'react';
import './CommandSuggestions.css';

const CommandSuggestions = ({ suggestions, onSelectSuggestion }) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="command-suggestions">
      <h3>Suggested Actions</h3>
      <div className="suggestions-container">
        {suggestions.map((suggestion, index) => (
          <button 
            key={index} 
            className="suggestion-button"
            onClick={() => onSelectSuggestion(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};

export default CommandSuggestions;
```

3. **Integrate with Game Interface**:

```jsx
// In your GameInterface component
import CommandSuggestions from './CommandSuggestions';

function GameInterface() {
  const { gameState, sendCommand } = useGame();
  const [commandInput, setCommandInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  
  // Update suggestions when game state changes
  useEffect(() => {
    if (gameState) {
      setSuggestions(generateSuggestions(gameState));
    }
  }, [gameState]);
  
  const handleSuggestionClick = (suggestion) => {
    setCommandInput(suggestion);
    // Optional: automatically send the command
    sendCommand(suggestion);
  };
  
  return (
    <div className="game-interface">
      {/* Game output display */}
      
      {/* Command suggestions */}
      <CommandSuggestions 
        suggestions={suggestions}
        onSelectSuggestion={handleSuggestionClick}
      />
      
      {/* Command input */}
      <div className="command-input">
        <input
          type="text"
          value={commandInput}
          onChange={(e) => setCommandInput(e.target.value)}
          placeholder="Enter command..."
        />
        <button onClick={() => sendCommand(commandInput)}>Send</button>
      </div>
    </div>
  );
}
```

This implementation provides a user-friendly interface with contextually relevant command suggestions, making the game more accessible to players who might not know all available commands.
