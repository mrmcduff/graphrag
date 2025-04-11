#!/usr/bin/env python3
"""
Test script for quest extraction using the updated Anthropic client.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the necessary modules
from llm.anthropic_client import AnthropicClient
from quest_parser import QuestParser

# Load environment variables
load_dotenv()


def test_quest_extraction():
    """Test quest extraction with the Anthropic client."""
    # Sample quest text
    sample_text = """
    The village elder approaches you with a worried look. "Our sacred Crystal of Wisdom has been stolen 
    by the goblin chief who lives in the Dark Cave to the north. Without it, our crops will fail and 
    our people will starve. Please, brave adventurer, retrieve the crystal and bring it back to me. 
    I can offer you 100 gold pieces and our eternal gratitude. But be warned - if you fail, the goblins 
    may become emboldened and attack our village, and we will lose trust in outsiders for generations."
    
    In another part of the village, the blacksmith mentions that the nearby mine has been infested with 
    giant spiders. "No one can get to the iron ore we need. If someone could clear out those spiders, 
    especially their queen, I'd craft them a fine set of armor worth at least 200 gold."
    """

    # Initialize the Anthropic client
    anthropic_client = AnthropicClient()

    # Check if API key is available
    if not anthropic_client.api_key:
        print(
            "Error: Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable."
        )
        return

    # Initialize the quest parser with the Anthropic client
    quest_parser = QuestParser(anthropic_client)

    # Extract quests from the sample text
    print("Extracting quests from sample text...")
    quests_data = quest_parser.extract_quests_from_text(sample_text)

    # Print the extracted quest data
    print("\nExtracted Quest Data:")
    print(json.dumps(quests_data, indent=2))

    # Create quest objects from the data
    print("\nCreating Quest Objects:")
    for i, quest_data in enumerate(quests_data):
        quest = quest_parser.create_quest_from_data(quest_data)
        if quest:
            print(f"\nQuest {i + 1}: {quest.title}")
            print(f"Type: {quest.quest_type}")
            print(f"Description: {quest.description}")
            print(f"Giver: {quest.giver}")

            # Print type-specific details
            if hasattr(quest, "item_to_fetch"):
                print(f"Item to Fetch: {quest.item_to_fetch}")
                print(f"Recipient: {quest.recipient}")
            elif hasattr(quest, "target_location"):
                print(f"Target Location: {quest.target_location}")
            elif hasattr(quest, "target_enemy"):
                print(f"Target Enemy: {quest.target_enemy}")
            elif hasattr(quest, "information"):
                print(f"Information: {quest.information}")
                print(f"Source: {quest.source}")
                print(f"Target: {quest.target}")

            # Print consequences
            if quest.success_consequences:
                print("Success Consequences:")
                for consequence in quest.success_consequences:
                    print(f"  - {consequence.consequence_type}: {consequence.target}")
                    if consequence.parameters:
                        print(f"    Parameters: {consequence.parameters}")

            if quest.failure_consequences:
                print("Failure Consequences:")
                for consequence in quest.failure_consequences:
                    print(f"  - {consequence.consequence_type}: {consequence.target}")
                    if consequence.parameters:
                        print(f"    Parameters: {consequence.parameters}")

            # Print notes
            if quest.notes:
                print("Notes:")
                for note in quest.notes:
                    print(f"  - {note}")
        else:
            print(f"\nFailed to create quest from data: {quest_data}")


if __name__ == "__main__":
    test_quest_extraction()
