from engine.command_registry.command_category import CommandCategory
from engine.intent_recognition.intent import IntentType, Intent
from typing import Dict, Any, List

from engine.context.command_context import CommandContext


class CommandHandler:
    """Base class for command handlers."""

    @property
    def command_category(self) -> CommandCategory:
        """Get the category of commands this handler processes."""
        raise NotImplementedError

    @property
    def supported_intents(self) -> List[IntentType]:
        """Get the intent types this handler can process."""
        raise NotImplementedError

    def can_handle(self, intent: Intent) -> bool:
        """Check if this handler can process the given intent."""
        return intent.type in self.supported_intents

    def handle(self, intent: Intent, context: CommandContext) -> Dict[str, Any]:
        """Process the intent and return a result."""
        raise NotImplementedError
