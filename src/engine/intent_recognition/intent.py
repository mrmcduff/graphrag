from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


class IntentType(Enum):
    """Types of intents the player might have."""

    MOVE = auto()
    EXAMINE = auto()
    TAKE = auto()
    USE = auto()
    TALK = auto()
    ATTACK = auto()
    INVENTORY = auto()
    EQUIP = auto()
    HELP = auto()
    QUIT = auto()
    SAVE = auto()
    LOAD = auto()
    MAP = auto()
    UNKNOWN = auto()


@dataclass
class Intent:
    """Represents a detected intent from player input."""

    type: IntentType
    confidence: float  # 0.0 to 1.0
    parameters: Dict[str, Any]
    original_text: str
