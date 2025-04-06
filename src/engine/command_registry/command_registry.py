from typing import Dict, Any, List, Callable, Optional, Type
import importlib
import inspect
from command_category import CommandCategory
from engine.intent_recognition import Intent
from engine.handlers import CommandHandler, MovementHandler


class CommandRegistry:
    """Registry of command handlers that can be dynamically extended."""

    def __init__(self, game_state):
        """
        Initialize the command registry.

        Args:
            game_state: The current game state
        """
        self.game_state = game_state
        self.handlers: Dict[CommandCategory, List[CommandHandler]] = {
            category: [] for category in CommandCategory
        }
        self._register_built_in_handlers()

    def _register_built_in_handlers(self):
        """Register the built-in command handlers."""
        self.register_handler(MovementHandler(self.game_state))
        # Register other built-in handlers...

    def register_handler(self, handler: CommandHandler) -> None:
        """
        Register a new command handler.

        Args:
            handler: The command handler to register
        """
        self.handlers[handler.command_category].append(handler)

    def get_handler_for_intent(self, intent: Intent) -> Optional[CommandHandler]:
        """
        Find a handler that can process the given intent.

        Args:
            intent: The intent to process

        Returns:
            A command handler or None if no handler is found
        """
        # First try exact intent type matches
        for handlers in self.handlers.values():
            for handler in handlers:
                if handler.can_handle(intent):
                    return handler

        # If no handler found, return None
        return None

    def load_handlers_from_module(self, module_name: str) -> None:
        """
        Dynamically load command handlers from a Python module.

        Args:
            module_name: Name of the module to load handlers from
        """
        try:
            module = importlib.import_module(module_name)

            # Find all CommandHandler subclasses in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, CommandHandler)
                    and obj is not CommandHandler
                ):
                    try:
                        # Instantiate the handler and register it
                        handler = obj(self.game_state)
                        self.register_handler(handler)
                        print(f"Registered command handler: {name}")
                    except Exception as e:
                        print(f"Error instantiating handler {name}: {e}")
        except Exception as e:
            print(f"Error loading module {module_name}: {e}")
