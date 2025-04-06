from enum import Enum


class CombatStatus(Enum):
    """Enum for the status of a combat encounter."""

    ACTIVE = "active"
    PLAYER_VICTORY = "player_victory"
    PLAYER_DEFEATED = "player_defeated"
    PLAYER_FLED = "player_fled"
    ENDED = "ended"  # Generic ended state (e.g., through dialogue/surrender)


class AttackType(Enum):
    """Types of attacks available in combat."""

    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"
    SPECIAL = "special"


class StatusEffect(Enum):
    """Status effects that can be applied during combat."""

    NONE = "none"
    POISONED = "poisoned"
    STUNNED = "stunned"
    WEAKENED = "weakened"
    PROTECTED = "protected"
    ENRAGED = "enraged"
    BLESSED = "blessed"
    CURSED = "cursed"
