from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from .command_processor import CommandType

class IntentResolver:
    """Resolve natural language intents to game commands using LLM."""

    def __init__(self, llm_manager):
        """
        Initialize the intent resolver.

        Args:
            llm_manager: The LLM manager to use for intent resolution
        """
        self.llm_manager = llm_manager
        self.command_examples = {
            CommandType.MOVEMENT: [
                "go forest",
                "walk north",
                "travel castle",
                "move village"
            ],
            CommandType.INTERACTION: [
                "look",
                "examine statue",
                "talk merchant",
                "speak guard",
                "take sword",
                "get potion",
                "use key"
            ],
            CommandType.INVENTORY: [
                "check inventory",
                "show items",
                "equip sword",
                "i"
            ],
            CommandType.COMBAT: [
                "attack the goblin",
                "fight the dragon",
                "check stats",
                "block",
                "dodge",
                "flee from battle"
            ],
            CommandType.SYSTEM: [
                "save game",
                "load game",
                "help",
                "show map",
                "display local map",
                "llm info",
                "llm change"
            ]
        }

    def _build_prompt(self, user_input: str, game_state=None) -> str:
        """
        Build a prompt for the LLM to resolve the intent.

        Args:
            user_input: The natural language input from the user
            game_state: Optional game state for context-aware resolution

        Returns:
            A formatted prompt for the LLM
        """
        prompt = (
            "You are an intent resolver for a text adventure game. "
            "Convert the user's natural language input into a valid game command.\n\n"
        )
        
        # Add game context if available
        if game_state:
            try:
                prompt += (
                    f"CURRENT LOCATION: {game_state.player_location}\n"
                )
                
                # Only add these if the methods exist
                if hasattr(game_state, 'get_characters_in_location'):
                    prompt += f"NEARBY CHARACTERS: {', '.join(game_state.get_characters_in_location())}\n"
                
                if hasattr(game_state, 'get_items_in_location'):
                    prompt += f"NEARBY ITEMS: {', '.join(game_state.get_items_in_location())}\n"
                
                prompt += "\n"
            except Exception as e:
                # Silently handle any errors with game state
                print(f"Error adding game state to prompt: {e}")
        
        prompt += "Valid command formats:\n"
        
        for cmd_type, examples in self.command_examples.items():
            prompt += f"# {cmd_type.value.upper()} COMMANDS:\n"
            for example in examples:
                prompt += f"- {example}\n"
            prompt += "\n"

        prompt += (
            "RULES:\n"
            "1. Extract the core intent and convert to the simplest valid command format\n"
            "2. For movement, use: go/move/walk/travel [location] - DO NOT include prepositions like 'to'\n"
            "3. For interaction, use: look/examine/talk/speak/take/get/use [target] - DO NOT include prepositions like 'to', 'with', or 'at'\n"
            "4. For inventory, use: inventory/items/i/equip [item]\n"
            "5. For combat, use: attack/fight/stats/block/dodge/flee [target]\n"
            "6. For system, use: save/load/help/map/llm [parameter]\n"
            "7. Return ONLY the converted command, nothing else\n\n"
            f"USER INPUT: {user_input}\n\n"
            "CONVERTED COMMAND:"
        )
        return prompt

    def resolve_intent(self, user_input: str, game_state=None) -> str:
        """
        Resolve the user's natural language intent to a game command.

        Args:
            user_input: The natural language input from the user
            game_state: Optional game state for context-aware resolution

        Returns:
            A valid game command string
        """
        prompt = self._build_prompt(user_input, game_state)
        
        try:
            # Use the LLM to resolve the intent
            resolved_command = self.llm_manager.generate_text(
                prompt, 
                max_tokens=50,  # Short response is all we need
                temperature=0.2  # Low temperature for more deterministic responses
            ).strip()
            
            # Clean up any potential formatting issues
            resolved_command = resolved_command.replace('"', '').replace("'", "").strip()
            
            # Remove common prepositions that might cause parsing issues
            for preposition in [' to ', ' with ', ' at ', ' on ', ' in ']:
                # Only replace prepositions with spaces around them to avoid affecting names
                resolved_command = resolved_command.replace(preposition, ' ')
            
            # Clean up any double spaces that might have been created
            while '  ' in resolved_command:
                resolved_command = resolved_command.replace('  ', ' ')
            
            return resolved_command
        except Exception as e:
            print(f"Error resolving intent: {e}")
            # Return the original input if there's an error
            return user_input
