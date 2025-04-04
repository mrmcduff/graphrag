import re
from typing import Dict, List, Any, Optional
from .base import LLMProvider

class RuleBasedProvider(LLMProvider):
    """Fallback rule-based response provider."""

    def __init__(self):
        super().__init__()
        self.name = "Rule-Based Fallback"

    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate a rule-based response based on prompt patterns.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate (ignored in rule-based)
            temperature: Sampling temperature (ignored in rule-based)

        Returns:
            Generated text response
        """
        # Extract game state from prompt if available
        game_state = self._extract_game_state(prompt)

        # Extract command or query
        command = self._extract_command(prompt)

        # Generate response based on command and state
        return self._generate_response(command, game_state)

    def _extract_game_state(self, prompt: str) -> Dict[str, Any]:
        """
        Extract game state from the prompt.

        Args:
            prompt: The prompt text

        Returns:
            Dictionary containing extracted game state
        """
        state = {
            "location": "Unknown",
            "npcs_present": [],
            "items": []
        }

        # Extract current location
        location_match = re.search(r"You are in ([^\.]+)", prompt)
        if location_match:
            state["location"] = location_match.group(1).strip()

        # Extract NPCs present
        npc_match = re.search(r"Characters present: (.+?)(?=\n|$)", prompt)
        if npc_match:
            npcs_text = npc_match.group(1)
            state["npcs_present"] = [npc.split(" (")[0] for npc in npcs_text.split(", ")]

        # Extract inventory
        inventory_match = re.search(r"Inventory: (.+?)(?=\n|$)", prompt)
        if inventory_match:
            inventory_text = inventory_match.group(1)
            if inventory_text.lower() != "nothing":
                state["inventory"] = inventory_text.split(", ")

        return state

    def _extract_command(self, prompt: str) -> Dict[str, str]:
        """
        Extract the command from the prompt.

        Args:
            prompt: The prompt text

        Returns:
            Dictionary with action and target
        """
        command = {"action": "", "target": ""}

        # Try to find a player command section
        command_match = re.search(r"# Player Command\n(.+?)(?=\n|$)", prompt)

        if command_match:
            command_text = command_match.group(1).strip().lower()
            parts = command_text.split()

            if parts:
                command["action"] = parts[0]
                if len(parts) > 1:
                    command["target"] = " ".join(parts[1:])
        else:
            # If no explicit command section, try to extract from the prompt
            lines = prompt.strip().split("\n")
            last_line = lines[-1].strip().lower()

            # If last line looks like a command
            if len(last_line.split()) <= 5 and not last_line.endswith("?"):
                parts = last_line.split()
                if parts:
                    command["action"] = parts[0]
                    if len(parts) > 1:
                        command["target"] = " ".join(parts[1:])

        return command

    def _generate_response(self, command: Dict[str, str], state: Dict[str, Any]) -> str:
        """
        Generate a response based on the command and state.

        Args:
            command: Dictionary with action and target
            state: Dictionary with game state

        Returns:
            Generated response text
        """
        action = command["action"]
        target = command["target"]
        location = state["location"]

        # Look command
        if action in ["look", "examine", "inspect"]:
            response = f"You take a moment to examine your surroundings in {location}. "

            if state["npcs_present"]:
                response += f"You see {', '.join(state['npcs_present'])}. "

            if state.get("items", []):
                response += f"There are several items here: {', '.join(state['items'])}. "
            else:
                response += "You don't see any notable items. "

            response += "You can see pathways leading to other areas."
            return response

        # Movement command
        elif action in ["go", "move", "travel", "walk"]:
            if target:
                return f"You make your way to {target}."
            else:
                return "Where do you want to go?"

        # Talk command
        elif action in ["talk", "speak", "ask"]:
            if target in state.get("npcs_present", []):
                return f"You approach {target} and begin a conversation. They respond cautiously but seem willing to talk."
            elif target:
                return f"There doesn't seem to be anyone named {target} here."
            else:
                return "Who do you want to talk to?"

        # Take command
        elif action in ["take", "get", "pick"]:
            if target:
                if target in state.get("items", []):
                    return f"You pick up the {target} and add it to your inventory."
                else:
                    return f"You don't see a {target} here that you can take."
            else:
                return "What do you want to take?"

        # Inventory command
        elif action in ["inventory", "items", "i"]:
            if state.get("inventory", []):
                return f"You are carrying: {', '.join(state['inventory'])}."
            else:
                return "You aren't carrying anything."

        # Help command
        elif action in ["help", "commands", "?"]:
            return """
Available commands:
- look: Examine your surroundings
- go [location]: Move to a different location
- talk [character]: Talk to a character
- take [item]: Pick up an item
- inventory: Check what you're carrying
- use [item]: Use an item from your inventory
- help: Display this help message
"""

        # Default response
        elif action:
            return f"You {action} {target} in {location}. Nothing particularly interesting happens."
        else:
            return "I'm not sure what you want to do. You could try 'look' to examine your surroundings, or 'help' to see available commands."
