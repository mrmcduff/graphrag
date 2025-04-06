import unittest
from unittest.mock import MagicMock
from engine.intent_recognition.intent import IntentType
from engine.context.command_context import CommandContext


class TestCommandContext(unittest.TestCase):
    def setUp(self):
        # Create a mock game state
        self.game_state = MagicMock()

        # Configure mock game state methods
        self.game_state.player_location = "forest"
        self.game_state.get_items_at_location.return_value = {
            "sword": {"name": "Rusty Sword"},
            "potion": {"name": "Health Potion"},
        }
        self.game_state.get_npcs_at_location.return_value = {
            "wizard": {"name": "Old Wizard", "gender": "male"},
            "elf": {"name": "Forest Elf", "gender": "female"},
        }
        self.game_state.get_features_at_location.return_value = {
            "tree": {"name": "Ancient Tree"},
            "stream": {"name": "Bubbling Stream"},
        }
        self.game_state.get_exits_from_location.return_value = {
            "cave": {"direction": "north", "destination": "dark cave"},
            "meadow": {"direction": "east", "destination": "sunny meadow"},
        }
        self.game_state.get_inventory.return_value = {
            "map": {"name": "World Map"},
            "coin": {"name": "Gold Coin"},
        }

        # Create the context object
        self.context = CommandContext(self.game_state)

    def test_add_interaction(self):
        # Test adding interactions
        self.context.add_interaction(IntentType.EXAMINE, ("items", "sword"))
        self.assertEqual(len(self.context.recent_interactions), 1)
        self.assertEqual(self.context.current_focus, ("items", "sword"))

        # Test pronoun tracking
        self.assertIn("it", self.context.last_referenced_entities)
        self.assertEqual(
            self.context.last_referenced_entities["it"], ("items", "sword")
        )

        # Add NPC interaction
        self.context.add_interaction(IntentType.TALK, ("npcs", "wizard"))
        self.assertEqual(len(self.context.recent_interactions), 2)
        self.assertEqual(self.context.current_focus, ("npcs", "wizard"))

        # Check pronouns were updated
        self.assertIn("him", self.context.last_referenced_entities)
        self.assertEqual(
            self.context.last_referenced_entities["him"], ("npcs", "wizard")
        )

    def test_get_visible_entities(self):
        # Test getting visible entities
        visible = self.context.get_visible_entities()

        # Check each entity type is present
        self.assertIn("items", visible)
        self.assertIn("npcs", visible)
        self.assertIn("features", visible)
        self.assertIn("exits", visible)

        # Check specific entities
        self.assertIn("sword", visible["items"])
        self.assertIn("wizard", visible["npcs"])
        self.assertIn("tree", visible["features"])
        self.assertIn("cave", visible["exits"])

    def test_resolve_reference(self):
        # Set up some references
        self.context.add_interaction(IntentType.EXAMINE, ("items", "sword"))
        self.context.add_interaction(IntentType.TALK, ("npcs", "wizard"))

        # Test resolving pronouns
        self.assertEqual(self.context.resolve_reference("it"), ("items", "sword"))
        self.assertEqual(self.context.resolve_reference("him"), ("npcs", "wizard"))

        # Test resolving exact entity names
        self.assertEqual(
            self.context.resolve_reference("rusty sword"), ("items", "sword")
        )
        self.assertEqual(
            self.context.resolve_reference("old wizard"), ("npcs", "wizard")
        )

        # Test resolving partial names
        self.assertEqual(self.context.resolve_reference("sword"), ("items", "sword"))
        self.assertEqual(self.context.resolve_reference("elf"), ("npcs", "elf"))

        # Test resolving inventory items
        self.assertEqual(self.context.resolve_reference("map"), ("inventory", "map"))

        # Test unknown reference
        self.assertIsNone(self.context.resolve_reference("dragon"))


if __name__ == "__main__":
    unittest.main()
