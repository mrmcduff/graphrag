from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class MovementHandler(CommandHandler):
    """Handler for movement commands."""

    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.MOVEMENT

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.MOVE]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        direction = intent.parameters.get("direction")
        if not direction:
            return {
                "success": False,
                "message": "Which direction do you want to go?",
                "action_type": "movement",
            }

        # Check if the direction is valid from current location
        location_info = self.game_state._get_location_info(
            self.game_state.player_location
        )
        connected_locations = location_info.get("connected_locations", [])

        # Try to find a matching location
        for location in connected_locations:
            if direction.lower() in location.lower():
                # Move player
                old_location = self.game_state.player_location
                success = self.game_state.update_state("go", location)

                if success:
                    return {
                        "success": True,
                        "message": f"You go to {location}.",
                        "action_type": "movement",
                        "old_location": old_location,
                        "new_location": self.game_state.player_location,
                    }

        # Try to interpret the direction as a cardinal direction
        direction_map = {
            "north": "north",
            "n": "north",
            "south": "south",
            "s": "south",
            "east": "east",
            "e": "east",
            "west": "west",
            "w": "west",
            "up": "up",
            "down": "down",
        }

        normalized_direction = direction_map.get(direction.lower())
        if normalized_direction:
            # Try to find an exit in that direction
            for location in connected_locations:
                if normalized_direction in location.lower():
                    # Move player
                    old_location = self.game_state.player_location
                    success = self.game_state.update_state("go", location)

                    if success:
                        return {
                            "success": True,
                            "message": f"You go {normalized_direction} to {location}.",
                            "action_type": "movement",
                            "old_location": old_location,
                            "new_location": self.game_state.player_location,
                        }

        return {
            "success": False,
            "message": f"You can't go {direction} from here.",
            "action_type": "movement",
        }
