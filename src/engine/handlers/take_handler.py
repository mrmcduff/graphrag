from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class TakeHandler(CommandHandler):
    """Handler for taking items."""

    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INTERACTION

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.TAKE]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        item = intent.parameters.get("item")
        if not item:
            return {
                "success": False,
                "message": "What do you want to take?",
                "action_type": "interaction",
            }

        # Try to take the item
        success = self.game_state.update_state("take", item)

        if success:
            # Update context to focus on this item
            context.add_interaction(IntentType.TAKE, ("items", item))

            return {
                "success": True,
                "message": f"You take the {item} and add it to your inventory.",
                "action_type": "interaction",
                "target": item,
            }
        else:
            return {
                "success": False,
                "message": f"There's no {item} here that you can take.",
                "action_type": "interaction",
            }
