from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class SystemHandler(CommandHandler):
    """Handler for system commands."""

    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.SYSTEM

    @property
    def supported_intents(self) -> List[IntentType]:
        return [
            IntentType.HELP,
            IntentType.SAVE,
            IntentType.LOAD,
            IntentType.MAP,
            IntentType.QUIT,
        ]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        if intent.type == IntentType.HELP:
            # Display help text
            help_text = """
Available Commands:
------------------
Movement: go [location], move [location], walk [location]
Look: look, examine [object/person]
Interaction: talk [character], take [item], use [item]
Inventory: inventory, equip [item]
Combat: attack [enemy], stats, block, dodge, flee
System: save [filename], load [filename], help, map, quit

Special Commands:
----------------
map - Show the world map
local map - Show detailed map of current location
quit - Exit the game
            """

            return {
                "success": True,
                "message": help_text,
                "action_type": "system",
                "help_displayed": True,
            }

        elif intent.type == IntentType.SAVE:
            # Save the game
            filename = intent.parameters.get("filename", "save.json")
            success = self.game_state.save_game(filename)

            if success:
                return {
                    "success": True,
                    "message": f"Game saved to {filename}.",
                    "action_type": "system",
                    "save_file": filename,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to save game to {filename}.",
                    "action_type": "system",
                }

        elif intent.type == IntentType.LOAD:
            # Load a saved game
            filename = intent.parameters.get("filename", "save.json")
            success = self.game_state.load_game(filename)

            if success:
                return {
                    "success": True,
                    "message": f"Game loaded from {filename}.",
                    "action_type": "system",
                    "load_file": filename,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to load game from {filename}.",
                    "action_type": "system",
                }

        elif intent.type == IntentType.MAP:
            # Show map
            target = intent.parameters.get("target", "")

            if target.lower() == "local":
                return {
                    "success": True,
                    "message": f"Displaying local map of {self.game_state.player_location}...",
                    "action_type": "system",
                    "map_type": "local",
                    "location": self.game_state.player_location,
                    "display_map": True,
                }
            else:
                return {
                    "success": True,
                    "message": "Displaying world map...",
                    "action_type": "system",
                    "map_type": "world",
                    "locations": list(self.game_state.visited_locations),
                    "display_map": True,
                }

        elif intent.type == IntentType.QUIT:
            # Handle quit
            return {
                "success": True,
                "message": "Thanks for playing! The game will now exit.",
                "action_type": "system",
                "quit_game": True,
            }

        # Default response for unknown system commands
        return {
            "success": False,
            "message": "Unknown system command. Try 'help' for a list of commands.",
            "action_type": "system",
        }
