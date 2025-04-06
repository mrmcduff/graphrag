from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
import textwrap


@dataclass
class Effect:
    """Represents an effect of a command on the game state."""

    type: str  # Type of effect (e.g., "state_change", "spawn", "remove")
    entity_type: Optional[str] = None  # Type of entity affected
    entity_id: Optional[str] = None  # ID of entity affected
    property: Optional[str] = None  # Property that was changed
    old_value: Any = None  # Previous value
    new_value: Any = None  # New value
    description: Optional[str] = None  # Human-readable description
    delay: float = 0.0  # Delay in seconds before effect occurs
