"""
Redis Session Manager for GraphRAG.

This module provides Redis-based session persistence for game sessions,
ensuring they survive Heroku dyno restarts.
"""

import json
import os
import redis
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import uuid

from .game_session import GameSession

# Configure logging
logger = logging.getLogger(__name__)

# Redis connection
_redis_client = None

# Session expiration time (3 days)
SESSION_EXPIRY = 60 * 60 * 24 * 3  # 3 days in seconds


def get_redis_client() -> redis.Redis:
    """
    Get or create a Redis client using environment variables.
    
    Returns:
        Redis client instance
    """
    global _redis_client
    
    if _redis_client is None:
        # Get Redis URL from environment (Heroku sets REDIS_URL automatically)
        redis_url = os.environ.get('REDIS_URL')
        
        if not redis_url:
            logger.warning("REDIS_URL not found in environment, using in-memory storage")
            return None
        
        try:
            _redis_client = redis.from_url(redis_url)
            logger.info(f"Connected to Redis at {redis_url.split('@')[-1]}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return None
    
    return _redis_client


def serialize_game_state(session: GameSession) -> Dict[str, Any]:
    """
    Serialize a game session to a JSON-compatible dictionary.
    
    Args:
        session: The GameSession object to serialize
        
    Returns:
        Dictionary with serialized game state
    """
    # Extract essential game state
    game_state = session.game_state
    
    # Convert sets to lists for JSON serialization
    visited_locations = list(game_state.visited_locations) if hasattr(game_state, 'visited_locations') else []
    
    # Create a serializable dictionary
    serialized_data = {
        "session_id": session.session_id,
        "created_at": datetime.now().isoformat(),
        "game_data_dir": session.game_data_dir,
        "provider_id": session.command_processor.llm_manager.active_provider_id,
        "game_state": {
            "player_location": game_state.player_location,
            "inventory": game_state.inventory,
            "visited_locations": visited_locations,
            "game_turn": game_state.game_turn,
            "game_over": game_state.game_over if hasattr(game_state, 'game_over') else False,
            "last_command": session.last_command if hasattr(session, 'last_command') else "",
            "last_response": session.last_response if hasattr(session, 'last_response') else "",
        }
    }
    
    return serialized_data


def save_session(session: GameSession) -> bool:
    """
    Save a game session to Redis.
    
    Args:
        session: The GameSession object to save
        
    Returns:
        True if successful, False otherwise
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.warning("Redis client not available, skipping session save")
        return False
    
    try:
        # Serialize the game session
        serialized_data = serialize_game_state(session)
        
        # Save to Redis with expiration
        key = f"session:{session.session_id}"
        redis_client.set(key, json.dumps(serialized_data), ex=SESSION_EXPIRY)
        
        # Add to session index
        redis_client.sadd("active_sessions", session.session_id)
        
        logger.info(f"Saved session {session.session_id} to Redis")
        return True
    except Exception as e:
        logger.error(f"Error saving session to Redis: {str(e)}")
        return False


def load_session(session_id: str) -> Optional[GameSession]:
    """
    Load a game session from Redis.
    
    Args:
        session_id: The session ID to load
        
    Returns:
        GameSession object if found and loaded successfully, None otherwise
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.warning("Redis client not available, cannot load session")
        return None
    
    try:
        # Get session data from Redis
        key = f"session:{session_id}"
        serialized_json = redis_client.get(key)
        
        if not serialized_json:
            logger.warning(f"Session {session_id} not found in Redis")
            return None
        
        # Parse the JSON data
        session_data = json.loads(serialized_json)
        
        # Create a new game session
        game_data_dir = session_data.get("game_data_dir", "data/output")
        provider_id = session_data.get("provider_id", 4)  # Default to Anthropic
        
        # Create a new session with the same ID
        session = GameSession(game_data_dir, {}, provider_id, {}, session_id=session_id)
        
        # Restore game state
        game_state_data = session_data.get("game_state", {})
        
        # Apply game state to the session
        if game_state_data:
            session.game_state.player_location = game_state_data.get("player_location", "start")
            session.game_state.inventory = game_state_data.get("inventory", [])
            session.game_state.visited_locations = set(game_state_data.get("visited_locations", []))
            session.game_state.game_turn = game_state_data.get("game_turn", 0)
            
            if hasattr(session.game_state, 'game_over'):
                session.game_state.game_over = game_state_data.get("game_over", False)
            
            if hasattr(session, 'last_command'):
                session.last_command = game_state_data.get("last_command", "")
            
            if hasattr(session, 'last_response'):
                session.last_response = game_state_data.get("last_response", "")
        
        # Refresh expiration time
        redis_client.expire(key, SESSION_EXPIRY)
        
        logger.info(f"Loaded session {session_id} from Redis")
        return session
    except Exception as e:
        logger.error(f"Error loading session from Redis: {str(e)}")
        return None


def delete_session(session_id: str) -> bool:
    """
    Delete a game session from Redis.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        # Delete session data
        key = f"session:{session_id}"
        redis_client.delete(key)
        
        # Remove from session index
        redis_client.srem("active_sessions", session_id)
        
        logger.info(f"Deleted session {session_id} from Redis")
        return True
    except Exception as e:
        logger.error(f"Error deleting session from Redis: {str(e)}")
        return False


def get_active_sessions() -> Set[str]:
    """
    Get all active session IDs from Redis.
    
    Returns:
        Set of active session IDs
    """
    redis_client = get_redis_client()
    if not redis_client:
        return set()
    
    try:
        # Get all active sessions
        session_ids = redis_client.smembers("active_sessions")
        return {sid.decode('utf-8') for sid in session_ids}
    except Exception as e:
        logger.error(f"Error getting active sessions from Redis: {str(e)}")
        return set()


def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions from the active sessions index.
    
    Returns:
        Number of sessions cleaned up
    """
    redis_client = get_redis_client()
    if not redis_client:
        return 0
    
    try:
        # Get all active sessions
        session_ids = get_active_sessions()
        count = 0
        
        # Check each session
        for session_id in session_ids:
            key = f"session:{session_id}"
            if not redis_client.exists(key):
                # Session expired, remove from index
                redis_client.srem("active_sessions", session_id)
                count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
        
        return count
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        return 0
