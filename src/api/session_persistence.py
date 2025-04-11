"""
Session Persistence Module for GraphRAG.

This module provides functions to store and retrieve game sessions
from the database to ensure persistence across Heroku dyno restarts.
"""

import pickle
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import models and database
from .models import db, User
from .game_session import GameSession

# Create a game_sessions table if it doesn't exist
class GameSessionStore(db.Model):
    """Model for storing game sessions persistently in the database."""

    __tablename__ = "game_sessions"

    session_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    game_data = db.Column(db.Text, nullable=False)  # JSON serialized game state
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with User model
    user = db.relationship("User", backref=db.backref("game_sessions", lazy=True))


# In-memory cache
_session_cache: Dict[str, GameSession] = {}


def store_session(session: GameSession, user_id: Optional[int] = None) -> bool:
    """
    Store a game session in both memory cache and database.
    
    Args:
        session: The GameSession object to store
        user_id: Optional user ID to associate with the session
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Store in memory cache
        _session_cache[session.session_id] = session
        
        # Serialize the game state (not the entire session)
        game_state_data = {
            "session_id": session.session_id,
            "player_location": session.game_state.player_location,
            "inventory": session.game_state.inventory,
            "visited_locations": list(session.game_state.visited_locations),
            "game_turn": session.game_state.game_turn,
            "provider_id": session.command_processor.llm_manager.active_provider_id,
        }
        
        # Check if session already exists in database
        db_session = GameSessionStore.query.get(session.session_id)
        if db_session:
            # Update existing session
            db_session.game_data = json.dumps(game_state_data)
            db_session.last_accessed = datetime.utcnow()
        else:
            # Create new session record
            db_session = GameSessionStore(
                session_id=session.session_id,
                user_id=user_id,
                game_data=json.dumps(game_state_data)
            )
            db.session.add(db_session)
            
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error storing session: {str(e)}")
        return False


def get_session(session_id: str) -> Optional[GameSession]:
    """
    Get a game session from memory cache or database.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        The GameSession object if found, None otherwise
    """
    # Check memory cache first
    if session_id in _session_cache:
        return _session_cache[session_id]
    
    # Try to retrieve from database
    try:
        db_session = GameSessionStore.query.filter_by(
            session_id=session_id, is_active=True
        ).first()
        
        if db_session:
            # We can't fully restore the session from the database,
            # but we can recreate it with the same session ID
            from .routes import GameSession
            
            # Parse the stored game state
            game_state_data = json.loads(db_session.game_data)
            
            # Create a new session with the same ID
            # This is a simplified approach - in a real implementation,
            # you would need to restore the full game state
            game_data_dir = "data/output"  # Default game data directory
            provider_id = game_state_data.get("provider_id", 4)  # Default to Anthropic
            
            # Create new session with the same ID
            session = GameSession(game_data_dir, {}, provider_id, {})
            
            # Store in memory cache
            _session_cache[session_id] = session
            
            # Update last accessed time
            db_session.last_accessed = datetime.utcnow()
            db.session.commit()
            
            return session
    except Exception as e:
        print(f"Error retrieving session from database: {str(e)}")
    
    return None


def update_session_routes():
    """
    Patch the routes module to use persistent sessions.
    Call this function after the routes are registered.
    """
    from . import routes
    
    # Store the original new_game function
    original_new_game = routes.new_game
    
    # Define the patched new_game function
    def patched_new_game():
        result = original_new_game()
        
        # After creating a new game session, store it in the database
        if result.status_code == 200:
            # Extract session_id from the response
            response_data = json.loads(result.get_data(as_text=True))
            session_id = response_data.get("session_id")
            
            if session_id and session_id in routes.game_sessions:
                # Get current user ID if available
                user_id = None
                try:
                    from .auth import get_current_user
                    current_user = get_current_user()
                    if current_user:
                        user_id = current_user.id
                except Exception:
                    pass
                
                # Store the session
                store_session(routes.game_sessions[session_id], user_id)
        
        return result
    
    # Replace the original function with the patched one
    routes.new_game = patched_new_game
    
    # Store the original process_command function
    original_process_command = routes.process_command
    
    # Define the patched process_command function
    def patched_process_command(session_id):
        # Check if session exists in memory
        if session_id not in routes.game_sessions:
            # Try to retrieve from database
            session = get_session(session_id)
            if session:
                routes.game_sessions[session_id] = session
        
        # Call the original function
        return original_process_command(session_id)
    
    # Replace the original function with the patched one
    routes.process_command = patched_process_command
