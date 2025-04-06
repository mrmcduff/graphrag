from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class ExamineHandler(CommandHandler):
    """Handler for examining things."""

    def __init__(self, game_state, graph_rag_engine):
        self.game_state = game_state
        self.graph_rag_engine = graph_rag_engine

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INTERACTION

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.EXAMINE]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        target = intent.parameters.get("target", "surroundings")

        if target in ["surroundings", "around", "room", "area", "here"]:
            # Look at the current location
            response = self.graph_rag_engine.generate_response(
                "look around", self.game_state
            )
            return {"success": True, "message": response, "action_type": "interaction"}

        # Use GraphRAG to examine the specific target
        response = self.graph_rag_engine.generate_response(
            f"examine {target}", self.game_state
        )

        # Try to update context with a focus on this entity
        resolved_ref = context.resolve_reference(target)
        if resolved_ref:
            context.add_interaction(IntentType.EXAMINE, resolved_ref)

        return {
            "success": True,
            "message": response,
            "action_type": "interaction",
            "target": target,
        }
