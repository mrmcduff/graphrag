from dataclasses import dataclass, field
from typing import List
from engine.feedback import Effect


@dataclass
class CommandResult:
    """Detailed result of a command execution."""

    success: bool
    message: str
    effects: List[Effect] = field(default_factory=list)
    alternatives: List[str] = field(
        default_factory=list
    )  # Alternative commands when this one fails
    feedback_type: str = "text"  # Type of feedback (text, visual, sound)
    action_type: str = "unknown"  # Type of action performed

    def add_effect(self, effect: Effect) -> None:
        """Add an effect to the result."""
        self.effects.append(effect)

    def suggest_alternative(self, alternative: str) -> None:
        """Add a suggested alternative command."""
        self.alternatives.append(alternative)
