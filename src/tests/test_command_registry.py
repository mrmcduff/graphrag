import unittest
from unittest.mock import MagicMock
from engine.intent_recognition.intent import IntentType, Intent
from engine.command_registry.command_category import CommandCategory
from engine.handlers.command_handler import CommandHandler
from engine.command_registry.command_registry import CommandRegistry
from engine.context.command_context import CommandContext


# Define a test command handler
class TestMovementHandler(CommandHandler):
    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.MOVEMENT

    @property
    def supported_intents(self) -> list:
        return [IntentType.MOVE]

    def handle(self, intent, context):
        direction = intent.parameters.get("direction")
        if direction:
            return {
                "success": True,
                "message": f"You move {direction}.",
                "action_type": "movement",
            }
        return {
            "success": False,
            "message": "Where do you want to go?",
            "action_type": "movement",
        }


# Define a test examine handler
class TestExamineHandler(CommandHandler):
    def __init__(self, game_state):
        self.game_state = game_state

    @property
    def command_category(self) -> CommandCategory:
        return CommandCategory.INTERACTION

    @property
    def supported_intents(self) -> list:
        return [IntentType.EXAMINE]

    def handle(self, intent, context):
        target = intent.parameters.get("target", "surroundings")
        return {
            "success": True,
            "message": f"You examine the {target}.",
            "action_type": "interaction",
        }


class TestCommandRegistry(unittest.TestCase):
    def setUp(self):
        # Create a mock game state
        self.game_state = MagicMock()

        # Create the registry
        self.registry = CommandRegistry(self.game_state)

        # Register test handlers
        self.move_handler = TestMovementHandler(self.game_state)
        self.examine_handler = TestExamineHandler(self.game_state)

        self.registry.register_handler(self.move_handler)
        self.registry.register_handler(self.examine_handler)

        # Create a context
        self.context = CommandContext(self.game_state)

    def test_register_handler(self):
        # Check that handlers were registered correctly
        movement_handlers = self.registry.handlers[CommandCategory.MOVEMENT]
        interaction_handlers = self.registry.handlers[CommandCategory.INTERACTION]

        self.assertEqual(len(movement_handlers), 1)
        self.assertEqual(len(interaction_handlers), 1)

        # Check that handlers are of correct type
        self.assertIsInstance(movement_handlers[0], TestMovementHandler)
        self.assertIsInstance(interaction_handlers[0], TestExamineHandler)

    def test_get_handler_for_intent(self):
        # Create a move intent
        move_intent = Intent(
            type=IntentType.MOVE,
            confidence=0.9,
            parameters={"direction": "north"},
            original_text="go north",
        )

        # Get handler for move intent
        handler = self.registry.get_handler_for_intent(move_intent)

        # Check that correct handler was returned
        self.assertIsInstance(handler, TestMovementHandler)

        # Create an examine intent
        examine_intent = Intent(
            type=IntentType.EXAMINE,
            confidence=0.9,
            parameters={"target": "sword"},
            original_text="examine sword",
        )

        # Get handler for examine intent
        handler = self.registry.get_handler_for_intent(examine_intent)

        # Check that correct handler was returned
        self.assertIsInstance(handler, TestExamineHandler)

        # Create an unknown intent
        unknown_intent = Intent(
            type=IntentType.UNKNOWN,
            confidence=0.1,
            parameters={},
            original_text="xyzzy",
        )

        # Get handler for unknown intent
        handler = self.registry.get_handler_for_intent(unknown_intent)

        # Check that no handler was returned
        self.assertIsNone(handler)

    def test_handler_execution(self):
        # Create a move intent
        move_intent = Intent(
            type=IntentType.MOVE,
            confidence=0.9,
            parameters={"direction": "north"},
            original_text="go north",
        )

        # Get handler for move intent
        handler = self.registry.get_handler_for_intent(move_intent)

        # Execute the handler
        result = handler.handle(move_intent, self.context)

        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "You move north.")
        self.assertEqual(result["action_type"], "movement")


if __name__ == "__main__":
    unittest.main()
