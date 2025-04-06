from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class TalkHandler(CommandHandler):
    """Handler for talking to NPCs."""

    def __init__(self, game_state, graph_rag_engine):
        self.game_state = game_state
        self.graph_rag_engine = graph_rag_engine

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INTERACTION

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.TALK]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        character = intent.parameters.get("character")
        if not character:
            return {
                "success": False,
                "message": "Who do you want to talk to?",
                "action_type": "interaction",
            }

        # Check if character is in the current location
        npcs_here = [
            npc
            for npc, data in self.game_state.npc_states.items()
            if data["location"] == self.game_state.player_location
        ]

        # Try to find a matching NPC
        matching_npcs = [npc for npc in npcs_here if character.lower() in npc.lower()]

        if not matching_npcs:
            return {
                "success": False,
                "message": f"There's no one named {character} here.",
                "action_type": "interaction",
            }

        # Use the closest match
        npc = matching_npcs[0]

        # Try to talk to the NPC
        success = self.game_state.update_state("talk", npc)

        if success:
            # Use GraphRAG to generate dialogue
            response = self.graph_rag_engine.generate_response(
                f"talk to {npc}", self.game_state
            )

            # Update context to focus on this NPC
            context.add_interaction(IntentType.TALK, ("npcs", npc))

            return {
                "success": True,
                "message": response,
                "action_type": "interaction",
                "target": npc,
            }
        else:
            return {
                "success": False,
                "message": f"You can't talk to {npc} right now.",
                "action_type": "interaction",
            }
