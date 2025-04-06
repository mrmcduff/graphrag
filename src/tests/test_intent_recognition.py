import unittest

import sys
import os

# Print current directory and Python path for debugging
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    # Try to import and see what happens
    from engine.intent_recognition import IntentType, Intent
    from engine.intent_recognition import IntentRecognizer

    print("Imports successful!")
except ImportError as e:
    print(f"Import error: {e}")

    # Try to locate the modules
    for path in sys.path:
        engine_path = os.path.join(path, "engine")
        if os.path.exists(engine_path):
            print(f"Found engine module at: {engine_path}")
            intent_path = os.path.join(engine_path, "intent_recognition")
            if os.path.exists(intent_path):
                print(f"Found intent_recognition module at: {intent_path}")

from engine.intent_recognition import IntentType, Intent
from engine.intent_recognition import IntentRecognizer


class TestIntentRecognizer(unittest.TestCase):
    def setUp(self):
        self.recognizer = IntentRecognizer()  # No LLM manager for basic tests

    def test_pattern_recognition(self):
        # Test move commands
        intents = self.recognizer.recognize("go to castle")
        self.assertGreaterEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.MOVE)
        self.assertEqual(intents[0].parameters.get("direction"), "castle")

        # Test examine commands
        intents = self.recognizer.recognize("look at sword")
        self.assertGreaterEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.EXAMINE)
        self.assertEqual(intents[0].parameters.get("target"), "sword")

        # Test simple look
        intents = self.recognizer.recognize("look")
        self.assertGreaterEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.EXAMINE)

        # Test take commands
        intents = self.recognizer.recognize("take potion")
        self.assertGreaterEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.TAKE)
        self.assertEqual(intents[0].parameters.get("item"), "potion")

    def test_keyword_recognition(self):
        # Test with just a keyword
        intents = self.recognizer.recognize("inventory")
        self.assertGreaterEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.INVENTORY)

        # Test with a keyword in a sentence
        intents = self.recognizer.recognize("I want to attack the goblin")
        found_attack = False
        for intent in intents:
            if intent.type == IntentType.ATTACK:
                found_attack = True
                self.assertIn("goblin", intent.parameters.get("target", ""))
        self.assertTrue(found_attack, "Failed to recognize attack intent")

    def test_ambiguous_input(self):
        # Test with ambiguous input that could be interpreted multiple ways
        intents = self.recognizer.recognize("use key on door")
        self.assertGreaterEqual(len(intents), 1)

        # The top intent should be USE
        self.assertEqual(intents[0].type, IntentType.USE)
        self.assertEqual(intents[0].parameters.get("item"), "key")
        self.assertEqual(intents[0].parameters.get("target"), "door")

    def test_unknown_input(self):
        # Test with completely unknown input
        intents = self.recognizer.recognize("xyzzy plugh")
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].type, IntentType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
