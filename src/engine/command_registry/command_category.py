from enum import Enum


class CommandCategory(Enum):
    """Categories of commands in the game."""

    MOVEMENT = "movement"
    INTERACTION = "interaction"
    INVENTORY = "inventory"
    COMBAT = "combat"
    SYSTEM = "system"
    CUSTOM = "custom"
