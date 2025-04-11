"""
Game Session Module for GraphRAG API.

This module provides the GameSession class for managing individual game sessions via the API.
"""

import uuid
from typing import Dict, Any, Optional, List

# Import game components
from src.gamestate.game_state import GameState
from src.graphrag.graph_rag_engine import GraphRAGEngine
from src.combat.combat_system import CombatSystem
from src.llm.llm_manager import LLMManager
from src.engine.command_processor import CommandProcessor
from src.api.api_utils import get_non_interactive_llm_config


class GameSession:
    """Class to manage an individual game session via API."""

    def __init__(
        self,
        game_data_dir: str,
        config: Optional[Dict[str, Any]] = None,
        provider_id: int = 4,
        provider_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize a new game session with all required components.

        Args:
            game_data_dir: Directory containing game data files
            config: Optional configuration dictionary
            provider_id: LLM provider ID (default: 4 for Anthropic)
            provider_config: Optional provider-specific configuration
        """
        # Use provided session_id or generate a new one
        self.session_id = session_id or str(uuid.uuid4())
        self.game_data_dir = game_data_dir
        self.last_command = ""
        self.last_response = ""
        self.config = config or {}

        # Initialize components
        self.llm_manager = LLMManager()
        self.game_state = GameState(game_data_dir)
        self.graph_rag_engine = GraphRAGEngine(game_data_dir, self.llm_manager)

        # Initialize combat system with GameStateData
        self.combat_system = CombatSystem(
            game_state_data=self.game_state.data,
            game_state=self.game_state,
            graph=self.game_state.graph,
            relations_df=self.game_state.relations_df,
        )

        # Initialize command processor
        self.command_processor = CommandProcessor(
            self.game_state, self.graph_rag_engine, self.combat_system, self.llm_manager
        )

        # Set up LLM provider with non-interactive configuration
        # Get complete configuration with defaults for any missing values
        complete_config = get_non_interactive_llm_config(provider_id, provider_config)
        self.command_processor.setup_llm_provider(
            provider_id, complete_config, interactive=False
        )

        # Game history for this session
        self.history: List[Dict[str, Any]] = []

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a command and return formatted results.

        Args:
            command: The command to process

        Returns:
            Formatted response with metadata
        """
        # Process the command
        result = self.command_processor.process_command(command)

        # Add to history
        self.history.append({"command": command, "result": result})

        # Format the response with metadata
        formatted_response = self._format_response(result)

        return formatted_response

    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the response with metadata for display.

        Args:
            result: The raw result from the command processor

        Returns:
            Formatted response with display metadata
        """
        response = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "content": [],
            "metadata": {
                "action_type": result.get("action_type", "unknown"),
                "combat_active": result.get("combat_active", False),
                "player_location": self.game_state.player_location,
                "inventory_count": len(self.game_state.inventory),
                "session_id": self.session_id,
            },
        }

        # Format the message content with display metadata
        if "message" in result:
            response["content"].append({"text": result["message"], "format": "normal"})

        # Add combat log with special formatting if in combat
        if result.get("combat_active", False) and "combat_log" in result:
            for log_entry in result["combat_log"]:
                response["content"].append(
                    {
                        "text": log_entry,
                        "format": "combat",
                        "color": "#ff5733",  # Red color for combat text
                    }
                )

        # Add location description with special formatting
        if result.get("action_type") == "movement" and result.get("success", False):
            response["content"].append(
                {
                    "text": f"You are now in {self.game_state.player_location}.",
                    "format": "location",
                    "color": "#33a1ff",  # Blue color for location
                }
            )

        # Add inventory items with special formatting
        if result.get("action_type") == "inventory":
            response["content"].append(
                {
                    "text": "Inventory: " + ", ".join(self.game_state.inventory),
                    "format": "inventory",
                    "color": "#33ff57",  # Green color for inventory
                }
            )

        return response

    def get_initial_state(self) -> Dict[str, Any]:
        """
        Get the initial game state and welcome message.

        Returns:
            Initial game state with welcome message
        """
        # Generate welcome message
        welcome_prompt = f"""
        # Welcome Message
        You are starting a text adventure game set in a rich world. You are in {self.game_state.player_location}.
        
        Generate a brief, engaging welcome message that introduces the player to the game world.
        Keep it atmospheric and immersive. Describe the starting location briefly and suggest
        some initial actions the player might take.
        
        The message should be 3-4 sentences long.
        """

        try:
            welcome = self.llm_manager.generate_text(welcome_prompt)
        except Exception:
            welcome = f"Welcome to the text adventure! You find yourself in {self.game_state.player_location}. Look around to see what's here."

        # Get initial context
        initial_context = self.game_state.get_current_context()

        return {
            "session_id": self.session_id,
            "welcome_message": welcome,
            "player_location": self.game_state.player_location,
            "npcs_present": list(initial_context.get("npcs_present", {}).keys()),
            "content": [
                {
                    "text": welcome,
                    "format": "welcome",
                    "color": "#9933ff",  # Purple color for welcome
                },
                {
                    "text": f"You find yourself in {self.game_state.player_location}.",
                    "format": "location",
                    "color": "#33a1ff",  # Blue color for location
                },
            ],
            "metadata": {
                "combat_active": False,
                "inventory_count": len(self.game_state.inventory),
                "available_commands": [
                    "look",
                    "go",
                    "talk",
                    "take",
                    "inventory",
                    "help",
                ],
            },
        }
