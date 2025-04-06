from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class CombatHandler(CommandHandler):
    """Handler for combat commands."""

    def __init__(self, game_state, combat_system):
        self.game_state = game_state
        self.combat_system = combat_system

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.COMBAT

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.ATTACK]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        target = intent.parameters.get("target")
        if not target:
            return {
                "success": False,
                "message": "What do you want to attack?",
                "action_type": "combat",
            }

        # Start combat with the target
        combat_started = self.combat_system.start_combat(target)

        if combat_started:
            enemy = self.combat_system.active_combat.get("enemy", {})
            enemy_name = enemy.get("name", target)

            return {
                "success": True,
                "message": f"You engage in combat with {enemy_name}!",
                "action_type": "combat",
                "combat_started": True,
                "enemy": enemy_name,
            }
        else:
            return {
                "success": False,
                "message": f"You can't attack {target}.",
                "action_type": "combat",
            }
