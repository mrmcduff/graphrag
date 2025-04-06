from typing import Any, Dict, List
from engine.command_registry.command_category import CommandCategory
from engine.context.command_context import CommandContext
from engine.handlers.command_handler import CommandHandler
from engine.intent_recognition.intent import Intent, IntentType


class EquipHandler(CommandHandler):
    """Handler for equipping items."""

    def __init__(self, game_state, combat_system):
        self.game_state = game_state
        self.combat_system = combat_system

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INVENTORY

    @property
    def supported_intents(self) -> List[IntentType]:
        return [IntentType.EQUIP]

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        item = intent.parameters.get("item")
        if not item:
            return {
                "success": False,
                "message": "What do you want to equip?",
                "action_type": "inventory",
            }

        # Check if item is in inventory
        if item not in self.game_state.inventory:
            return {
                "success": False,
                "message": f"You don't have {item} in your inventory.",
                "action_type": "inventory",
            }

        # Check if it's a weapon or armor
        is_weapon = (
            hasattr(self.combat_system, "weapon_database")
            and item in self.combat_system.weapon_database
        )
        is_armor = (
            hasattr(self.combat_system, "armor_database")
            and item in self.combat_system.armor_database
        )

        if is_weapon:
            self.combat_system.player_stats["equipped_weapon"] = item
            return {
                "success": True,
                "message": f"You equip the {item}.",
                "action_type": "inventory",
                "equipped": item,
                "slot": "weapon",
            }
        elif is_armor:
            self.combat_system.player_stats["equipped_armor"] = item
            return {
                "success": True,
                "message": f"You equip the {item}.",
                "action_type": "inventory",
                "equipped": item,
                "slot": "armor",
            }
        else:
            return {
                "success": False,
                "message": f"You can't equip {item}.",
                "action_type": "inventory",
            }
