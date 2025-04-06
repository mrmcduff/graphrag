from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.intent_recognition.intent import Intent, IntentType
from engine.handlers.command_handler import CommandHandler


class InventoryHandler(CommandHandler):
    """Handler for inventory commands."""

    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INVENTORY

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.INVENTORY]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        if not self.game_state.inventory:
            return {
                "success": True,
                "message": "Your inventory is empty.",
                "action_type": "inventory",
            }

        # Format the inventory list
        items = ", ".join(self.game_state.inventory)
        return {
            "success": True,
            "message": f"Inventory: {items}",
            "action_type": "inventory",
            "inventory": self.game_state.inventory,
        }
