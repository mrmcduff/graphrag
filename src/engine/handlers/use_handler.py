from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class UseHandler(CommandHandler):
    """Handler for using items."""

    def __init__(self, game_state, graph_rag_engine):
        self.game_state = game_state
        self.graph_rag_engine = graph_rag_engine

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INTERACTION

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.USE]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        item = intent.parameters.get("item")
        target = intent.parameters.get("target")

        if not item:
            return {
                "success": False,
                "message": "What do you want to use?",
                "action_type": "interaction",
            }

        # Check if item is in inventory
        if item not in self.game_state.inventory:
            return {
                "success": False,
                "message": f"You don't have {item} in your inventory.",
                "action_type": "interaction",
            }

        # Try to use the item
        query = f"use {item}"
        if target:
            query += f" on {target}"

        success = self.game_state.update_state("use", item)

        if success:
            # Use GraphRAG to generate a response
            response = self.graph_rag_engine.generate_response(query, self.game_state)

            # Update context to focus on this item
            context.add_interaction(IntentType.USE, ("items", item))

            return {
                "success": True,
                "message": response,
                "action_type": "interaction",
                "item": item,
                "target": target,
            }
        else:
            return {
                "success": False,
                "message": f"You can't use {item} right now.",
                "action_type": "interaction",
            }
