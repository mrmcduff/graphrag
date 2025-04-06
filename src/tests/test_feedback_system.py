import unittest
from unittest.mock import MagicMock
from engine.intent_recognition.intent import IntentType, Intent
from engine.feedback import CommandResult, Effect, FeedbackGenerator


class TestFeedbackSystem(unittest.TestCase):
    def setUp(self):
        # Create a mock game state
        self.game_state = MagicMock()

        # Configure game state methods
        self.game_state.player_location = "forest"
        self.game_state._get_location_info.return_value = {
            "connected_locations": ["castle", "village"],
            "items": ["sword", "potion"],
        }
        self.game_state.inventory = ["map", "coin"]

        # Create feedback generator
        self.feedback_generator = FeedbackGenerator(self.game_state)

    def test_command_result(self):
        # Create a basic command result
        result = CommandResult(
            success=True, message="You examine the sword.", action_type="interaction"
        )

        # Add an effect
        result.add_effect(
            Effect(
                type="state_change",
                entity_type="player",
                property="knowledge",
                old_value="unknown",
                new_value="known",
                description="You now know more about the sword.",
            )
        )

        # Check result properties
        self.assertTrue(result.success)
        self.assertEqual(result.message, "You examine the sword.")
        self.assertEqual(result.action_type, "interaction")
        self.assertEqual(len(result.effects), 1)

        # Check effect properties
        effect = result.effects[0]
        self.assertEqual(effect.type, "state_change")
        self.assertEqual(effect.entity_type, "player")
        self.assertEqual(effect.property, "knowledge")
        self.assertEqual(effect.description, "You now know more about the sword.")

        # Add an alternative
        result.suggest_alternative("look at the blade")

        # Check alternatives
        self.assertEqual(len(result.alternatives), 1)
        self.assertEqual(result.alternatives[0], "look at the blade")

    def test_generate_feedback_success(self):
        # Create a successful movement intent
        intent = Intent(
            type=IntentType.MOVE,
            confidence=0.9,
            parameters={"direction": "castle"},
            original_text="go to the castle",
        )

        # Create a basic result
        result = {
            "success": True,
            "message": "You travel to the castle.",
            "action_type": "movement",
            "old_location": "forest",
            "new_location": "castle",
        }

        # Generate feedback
        cmd_result = self.feedback_generator.generate_feedback(
            "go to the castle", intent, result
        )

        # Check command result
        self.assertTrue(cmd_result.success)
        self.assertEqual(cmd_result.message, "You travel to the castle.")
        self.assertEqual(cmd_result.action_type, "movement")

        # Check generated effects
        self.assertGreaterEqual(len(cmd_result.effects), 1)
        found_location_change = False
        for effect in cmd_result.effects:
            if (
                effect.type == "state_change"
                and effect.entity_type == "player"
                and effect.property == "location"
            ):
                found_location_change = True
                self.assertEqual(effect.old_value, "forest")
                self.assertEqual(effect.new_value, "castle")
        self.assertTrue(found_location_change, "Location change effect not found")

    def test_generate_feedback_failure(self):
        # Create a failed movement intent
        intent = Intent(
            type=IntentType.MOVE,
            confidence=0.9,
            parameters={"direction": "mountain"},
            original_text="go to the mountain",
        )

        # Create a failed result
        result = {
            "success": False,
            "message": "You can't go to mountain from here.",
            "action_type": "movement",
        }

        # Generate feedback
        cmd_result = self.feedback_generator.generate_feedback(
            "go to the mountain", intent, result
        )

        # Check command result
        self.assertFalse(cmd_result.success)
        self.assertEqual(cmd_result.message, "You can't go to mountain from here.")
        self.assertEqual(cmd_result.action_type, "movement")

        # Check alternatives
        self.assertGreaterEqual(len(cmd_result.alternatives), 1)

        # Alternatives should include valid directions
        alternatives = set(cmd_result.alternatives)
        self.assertTrue(any("castle" in alt for alt in alternatives))
        self.assertTrue(any("village" in alt for alt in alternatives))


if __name__ == "__main__":
    unittest.main()
