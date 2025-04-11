"""
Quest parser for GraphRAG text adventure game.

This module provides functionality to extract quest information from documents
using an LLM and create quest objects based on the extracted information.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import logging

# Import the quest system
from gamestate.quest_system import (
    Quest,
    FetchQuest,
    LocationQuest,
    CombatQuest,
    InformationQuest,
    QuestCondition,
    QuestConsequence,
    QuestStatus,
    QuestType,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestParser:
    """Class to parse quest information from text using an LLM."""

    def __init__(self, llm_client=None, debug=False):
        """
        Initialize the quest parser.

        Args:
            llm_client: Client for the LLM API (optional)
            debug: Whether to print debug information
        """
        self.llm_client = llm_client
        self.debug = debug

    def set_llm_client(self, llm_client):
        """
        Set the LLM client.

        Args:
            llm_client: Client for the LLM API
        """
        self.llm_client = llm_client

    def extract_quests_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract quest information from text using an LLM.

        Args:
            text: Text to extract quest information from

        Returns:
            List of dictionaries containing quest information
        """
        if not self.llm_client:
            logger.warning("No LLM client set. Using rule-based extraction instead.")
            return self._rule_based_extraction(text)

        # Prepare the prompt for the LLM
        prompt = self._create_quest_extraction_prompt(text)

        try:
            # Call the LLM API
            response = self.llm_client.generate_text(prompt)

            # Print raw response only if debug mode is enabled
            if self.debug:
                print("\nRaw LLM response:")
                print(response)

            # Parse the response
            quest_data = self._parse_llm_response(response)

            # Validate the quest data
            validated_quests = []
            for quest in quest_data:
                if self._validate_quest_data(quest):
                    validated_quests.append(quest)
                else:
                    logger.warning(f"Invalid quest data: {quest}")

            return validated_quests

        except Exception as e:
            logger.error(f"Error extracting quests with LLM: {e}")
            # Fall back to rule-based extraction
            return self._rule_based_extraction(text)

    def _create_quest_extraction_prompt(self, text: str) -> str:
        """
        Create a prompt for the LLM to extract quest information.

        Args:
            text: Text to extract quest information from

        Returns:
            Prompt for the LLM
        """
        return f"""
You are an AI assistant for a text adventure game. Your task is to identify and extract quest information from the following text, and create a complete quest object formatted according to our JSON schema.

A quest in the game can be one of the following types:
1. FETCH: Get an item and bring it to an NPC
2. LOCATION: Travel to a specific location
3. COMBAT: Defeat a specific enemy
4. INFORMATION: Deliver information between NPCs

For each quest you identify, extract the following information:
- title: A creative, engaging title for the quest (if not explicitly given, suggest an appropriate title)
- description: A detailed description of the quest
- quest_type: One of FETCH, LOCATION, COMBAT, or INFORMATION
- giver: The NPC who gives the quest (if mentioned)
- target_location: For LOCATION quests, the location to travel to
- item_to_fetch: For FETCH quests, the item to retrieve
- recipient: For FETCH quests, the NPC to bring the item to
- target_enemy: For COMBAT quests, the enemy to defeat
- information: For INFORMATION quests, the information to deliver
- source: For INFORMATION quests, the NPC who provides the information
- target: For INFORMATION quests, the NPC to deliver the information to
- reward: Any reward mentioned for completing the quest (e.g., gold, items, reputation). Be specific about the amount and type.
- difficulty: Suggest a difficulty level (EASY, MEDIUM, HARD) based on the quest description
- time_limit: If a time limit is mentioned, include it; otherwise, suggest a reasonable one
- failure_consequences: List ALL consequences for failing the quest as separate items in an array. Common consequences include reputation loss, loss of future opportunities, or other penalties.

TEXT:
{text}

Important instructions:
1. Generate a complete quest object with all relevant fields for the quest type
2. If information is missing from the text, use your creativity to suggest appropriate values
3. Make sure the quest title is engaging and thematic for a fantasy adventure game
4. Be creative but stay consistent with the information provided in the text
5. Format your response as a JSON array containing the quest object

Example response format:
```json
[
  {{
    "title": "The Blacksmith's Lost Masterpiece",
    "description": "The blacksmith has lost his prized sword and asks you to find it. It was last seen in the abandoned mine to the north. Return it to him for a reward of 50 gold pieces.",
    "quest_type": "FETCH",
    "giver": "Blacksmith",
    "item_to_fetch": "Prized Sword",
    "recipient": "Blacksmith",
    "reward": "50 gold pieces",
    "difficulty": "MEDIUM",
    "time_limit": "3 days",
    "failure_consequences": [
      "The blacksmith will be disappointed and less willing to help you in the future",
      "You will lose access to special blacksmith equipment upgrades",
      "Your reputation with the town merchants will decrease slightly"
    ]
  }}
]
```

If no quests are found in the text, return an empty array: []
"""

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response to extract quest information.

        Args:
            response: Response from the LLM

        Returns:
            List of dictionaries containing quest information
        """
        try:
            logger.info(f"Parsing LLM response of length {len(response)}")

            # Log the first 100 characters of the response for debugging
            preview = response[:100] + "..." if len(response) > 100 else response
            logger.info(f"Response preview: {preview}")

            # Check if the response is already a valid JSON array
            if response.strip().startswith("[") and response.strip().endswith("]"):
                try:
                    logger.info(
                        "Response appears to be a JSON array, attempting direct parse"
                    )
                    quest_data = json.loads(response)
                    if isinstance(quest_data, list):
                        logger.info(
                            f"Successfully parsed JSON array with {len(quest_data)} quests"
                        )
                        return quest_data
                except json.JSONDecodeError:
                    logger.info("Direct JSON parse failed, continuing with extraction")

            # Extract JSON from the response
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
            if json_match:
                logger.info("Found JSON in markdown code block")
                json_str = json_match.group(1)
            else:
                # Try to find JSON without the markdown code block
                json_match = re.search(r"\[\s*{[\s\S]*}\s*\]", response)
                if json_match:
                    logger.info("Found JSON array without markdown code block")
                    json_str = json_match.group(0)
                else:
                    # Try to find a single JSON object
                    json_match = re.search(r"{[\s\S]*}", response)
                    if json_match:
                        logger.info("Found single JSON object")
                        json_str = json_match.group(0)
                    else:
                        logger.warning("No JSON found in LLM response. Full response:")
                        logger.warning(response)

                        # Try to extract structured information from the text
                        return self._extract_quest_from_text(response)

            # Parse the JSON
            try:
                # Clean up the JSON string
                json_str = json_str.strip()
                # If the string contains example JSON, extract only the relevant part
                if "Example response format:" in json_str:
                    logger.info(
                        "Found example format in JSON string, extracting relevant part"
                    )
                    # Try to find the actual JSON array
                    example_match = re.search(r"\[\s*{[\s\S]*?}\s*\]", json_str)
                    if example_match:
                        json_str = example_match.group(0)

                quest_data = json.loads(json_str)
                logger.info(f"Successfully parsed JSON: {type(quest_data)}")

                # Ensure the result is a list
                if not isinstance(quest_data, list):
                    quest_data = [quest_data]
                    logger.info("Converted single quest to list")

                logger.info(f"Found {len(quest_data)} quests in JSON")
                return quest_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Problematic JSON string: {json_str}")
                # Try to fix common JSON issues
                fixed_json = self._fix_json_string(json_str)
                if fixed_json != json_str:
                    try:
                        quest_data = json.loads(fixed_json)
                        logger.info("Successfully parsed fixed JSON")

                        # Ensure the result is a list
                        if not isinstance(quest_data, list):
                            quest_data = [quest_data]

                        return quest_data
                    except json.JSONDecodeError:
                        logger.error("Failed to parse fixed JSON")

                # If we can't parse the JSON, try to extract structured information from the text
                return self._extract_quest_from_text(response)

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []

    def _fix_json_string(self, json_str: str) -> str:
        """
        Fix common JSON formatting issues.

        Args:
            json_str: JSON string to fix

        Returns:
            Fixed JSON string
        """
        # Replace single quotes with double quotes
        json_str = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'(,|\s*})", r':"\1"\2', json_str)

        # Fix missing quotes around keys
        json_str = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', json_str)

        # Fix trailing commas
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*\]", "]", json_str)

        return json_str

    def _extract_quest_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract quest information from unstructured text.

        Args:
            text: Text to extract quest information from

        Returns:
            List of dictionaries containing quest information
        """
        logger.info("Attempting to extract quest from unstructured text")

        # Look for quest name/title
        title_match = re.search(r"(?i)(?:quest|title|name)\s*[:-]\s*([^\n]+)", text)
        if not title_match:
            logger.warning("Could not find quest title in text")
            return []

        title = title_match.group(1).strip()
        logger.info(f"Found quest title: {title}")

        # Look for quest type indicators
        quest_type = "FETCH"  # Default
        if re.search(r"(?i)(?:find|go to|reach|visit|travel to)\s+([^\n,.]+)", text):
            quest_type = "LOCATION"
        elif re.search(r"(?i)(?:defeat|kill|slay|fight)\s+([^\n,.]+)", text):
            quest_type = "COMBAT"
        elif re.search(r"(?i)(?:tell|inform|message|deliver)\s+([^\n,.]+)", text):
            quest_type = "INFORMATION"

        # Create quest data
        quest_data = {"title": title, "description": text, "quest_type": quest_type}

        # Look for giver
        giver_match = re.search(r"(?i)([\w\s]+)\s+(?:asks|requested|needs|wants)", text)
        if giver_match:
            quest_data["giver"] = giver_match.group(1).strip()

        # Look for reward
        reward_match = re.search(
            r"(?i)(?:reward|give)\s+(?:of|is|the player)?\s*([\w\s\d]+)", text
        )
        if reward_match:
            quest_data["reward"] = reward_match.group(1).strip()

        # Extract type-specific fields
        if quest_type == "LOCATION":
            location_match = re.search(
                r"(?i)(?:find|go to|reach|visit|travel to)\s+([^\n,.]+)", text
            )
            if location_match:
                quest_data["target_location"] = location_match.group(1).strip()
        elif quest_type == "COMBAT":
            enemy_match = re.search(
                r"(?i)(?:defeat|kill|slay|fight)\s+([^\n,.]+)", text
            )
            if enemy_match:
                quest_data["target_enemy"] = enemy_match.group(1).strip()
        elif quest_type == "FETCH":
            item_match = re.search(
                r"(?i)(?:find|bring|get|retrieve|collect)\s+(?:the|a|an)?\s+([^\n,.]+)",
                text,
            )
            if item_match:
                quest_data["item_to_fetch"] = item_match.group(1).strip()

        logger.info(f"Extracted quest data from text: {quest_data}")
        return [quest_data]

    def _validate_quest_data(self, quest_data: Dict[str, Any]) -> bool:
        """
        Validate quest data to ensure it has the required fields.

        Args:
            quest_data: Dictionary containing quest information

        Returns:
            Boolean indicating if the quest data is valid
        """
        # Required fields for all quest types
        required_fields = ["title", "description", "quest_type"]

        # Check required fields
        for field in required_fields:
            if field not in quest_data or not quest_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate quest type
        quest_type = quest_data.get("quest_type")
        if quest_type not in ["FETCH", "LOCATION", "COMBAT", "INFORMATION"]:
            logger.warning(f"Invalid quest type: {quest_type}")
            return False

        # Validate type-specific fields
        if quest_type == "FETCH":
            if "item_to_fetch" not in quest_data or not quest_data["item_to_fetch"]:
                logger.warning("FETCH quest missing item_to_fetch")
                return False

        elif quest_type == "LOCATION":
            if "target_location" not in quest_data or not quest_data["target_location"]:
                logger.warning("LOCATION quest missing target_location")
                return False

        elif quest_type == "COMBAT":
            if "target_enemy" not in quest_data or not quest_data["target_enemy"]:
                logger.warning("COMBAT quest missing target_enemy")
                return False

        elif quest_type == "INFORMATION":
            if "information" not in quest_data or not quest_data["information"]:
                logger.warning("INFORMATION quest missing information")
                return False

        return True

    def _rule_based_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract quest information using rule-based methods as a fallback.

        Args:
            text: Text to extract quest information from

        Returns:
            List of dictionaries containing quest information
        """
        quests = []
        logger.info(f"Using rule-based extraction on text of length {len(text)}")

        # First try to find explicit quest markers
        quest_sections = re.split(r"(?i)QUEST:|MISSION:", text)

        if len(quest_sections) > 1:
            logger.info(f"Found {len(quest_sections) - 1} explicit quest sections")
            # Process each quest section
            for i in range(1, len(quest_sections)):
                section = quest_sections[i].strip()
                lines = section.split("\n")

                # Extract title (first line)
                title = lines[0].strip()
                description = "\n".join(lines[1:]).strip()

                # Try to determine quest type
                quest_type = self._determine_quest_type(description)

                # Create quest data
                quest_data = {
                    "title": title,
                    "description": description,
                    "quest_type": quest_type,
                }

                # Extract additional fields based on quest type
                self._extract_additional_fields(quest_data, description)

                quests.append(quest_data)
                logger.info(f"Added quest: {title} (type: {quest_type})")
        else:
            logger.info(
                "No explicit quest markers found, trying to extract from document structure"
            )

            # Look for common quest document patterns
            # Pattern 0: Quest Name: format (specific to GraphRAG)
            quest_name_match = re.search(
                r"(?i)Quest Name:\s*(.+?)\s*$", text, re.MULTILINE
            )

            if quest_name_match:
                logger.info("Found 'Quest Name:' format document")
                title = quest_name_match.group(1).strip()
                # The rest of the text is the description
                description_start = (
                    text.lower().find("quest name:")
                    + len("quest name:")
                    + len(title)
                    + 1
                )
                description = text[description_start:].strip()

                # Create quest data
                quest_type = self._determine_quest_type(description)
                quest_data = {
                    "title": title,
                    "description": description,
                    "quest_type": quest_type,
                }

                # Extract additional fields
                self._extract_additional_fields(quest_data, description)

                quests.append(quest_data)
                logger.info(
                    f"Added quest from 'Quest Name:' format: {title} (type: {quest_type})"
                )
                return quests  # Return early since we found a quest

            # Pattern 1: Title followed by description and objectives
            title_match = re.search(
                r"(?i)^\s*(.+?)\s*$\s*(?:Description|Overview|Summary):\s*(.+?)(?:\s*Objectives?:|\s*Goals?:|\s*Tasks?:|$)",
                text,
                re.MULTILINE | re.DOTALL,
            )

            if title_match:
                logger.info(
                    "Found structured quest document with title and description"
                )
                title = title_match.group(1).strip()
                description = title_match.group(2).strip()

                # Look for objectives
                objectives_match = re.search(
                    r"(?i)Objectives?:|Goals?:|Tasks?:\s*(.+?)(?:\s*Rewards?:|$)",
                    text,
                    re.MULTILINE | re.DOTALL,
                )

                if objectives_match:
                    description += (
                        "\n\nObjectives: " + objectives_match.group(1).strip()
                    )

                # Determine quest type
                quest_type = self._determine_quest_type(description)

                # Create quest data
                quest_data = {
                    "title": title,
                    "description": description,
                    "quest_type": quest_type,
                }

                # Look for reward information
                reward_match = re.search(
                    r"(?i)Rewards?:\s*(.+?)(?:\s*Notes?:|$)",
                    text,
                    re.MULTILINE | re.DOTALL,
                )

                if reward_match:
                    quest_data["reward"] = reward_match.group(1).strip()

                # Extract additional fields
                self._extract_additional_fields(quest_data, text)

                quests.append(quest_data)
                logger.info(f"Added quest: {title} (type: {quest_type})")
            else:
                logger.info(
                    "No structured quest document found, trying to extract from paragraphs"
                )
                # Try to identify quests from context
                # Look for common quest indicators
                indicators = [
                    r"(?i)can you help me",
                    r"(?i)I need your help",
                    r"(?i)if you could .* I would",
                    r"(?i)reward",
                    r"(?i)bring me",
                    r"(?i)find (?:the|my)",
                    r"(?i)defeat (?:the|a)",
                    r"(?i)tell .* that",
                ]

                for indicator in indicators:
                    matches = re.finditer(indicator, text)
                    for match in matches:
                        # Extract a chunk of text around the match
                        start = max(0, match.start() - 200)
                        end = min(len(text), match.end() + 200)
                        chunk = text[start:end]

                        # Generate a title
                        title = self._generate_title(chunk)

                        # Determine quest type
                        quest_type = self._determine_quest_type(chunk)

                        # Create quest data
                        quest_data = {
                            "title": title,
                            "description": chunk,
                            "quest_type": quest_type,
                        }

                        # Extract additional fields
                        self._extract_additional_fields(quest_data, chunk)

                        # Check if this quest is similar to any existing quests
                        if not self._is_duplicate_quest(quest_data, quests):
                            quests.append(quest_data)
                            logger.info(
                                f"Added quest from indicator: {title} (type: {quest_type})"
                            )

        # If we still haven't found any quests, try one more approach - treat the entire document as a single quest
        if not quests and len(text.strip()) > 100:
            logger.info(
                "No quests found with other methods, treating entire document as a single quest"
            )

            # Try to extract a title from the first line
            lines = text.strip().split("\n")
            title = (
                lines[0].strip() if lines and len(lines[0]) < 80 else "Finding Mt. Dorn"
            )

            # Use the rest as description, or the whole text if no clear title
            description = (
                "\n".join(lines[1:]).strip()
                if len(lines) > 1 and len(lines[0]) < 80
                else text
            )

            # Determine quest type
            quest_type = self._determine_quest_type(text)

            # Create quest data
            quest_data = {
                "title": title,
                "description": description,
                "quest_type": quest_type,
            }

            # Extract additional fields
            self._extract_additional_fields(quest_data, text)

            quests.append(quest_data)
            logger.info(f"Added document as single quest: {title} (type: {quest_type})")

        logger.info(f"Rule-based extraction found {len(quests)} quests")
        return quests

    def _determine_quest_type(self, text: str) -> str:
        """
        Determine the quest type based on the text.

        Args:
            text: Quest description text

        Returns:
            Quest type (FETCH, LOCATION, COMBAT, or INFORMATION)
        """
        # Check for FETCH quest indicators
        fetch_indicators = [
            r"(?i)bring .* to",
            r"(?i)find .* and return",
            r"(?i)retrieve",
            r"(?i)get .* for",
            r"(?i)collect",
            r"(?i)gather",
        ]

        for indicator in fetch_indicators:
            if re.search(indicator, text):
                return "FETCH"

        # Check for LOCATION quest indicators
        location_indicators = [
            r"(?i)go to",
            r"(?i)travel to",
            r"(?i)reach",
            r"(?i)visit",
            r"(?i)explore",
        ]

        for indicator in location_indicators:
            if re.search(indicator, text):
                return "LOCATION"

        # Check for COMBAT quest indicators
        combat_indicators = [
            r"(?i)defeat",
            r"(?i)kill",
            r"(?i)slay",
            r"(?i)fight",
            r"(?i)battle",
        ]

        for indicator in combat_indicators:
            if re.search(indicator, text):
                return "COMBAT"

        # Check for INFORMATION quest indicators
        information_indicators = [
            r"(?i)tell .* that",
            r"(?i)inform",
            r"(?i)message",
            r"(?i)deliver .* news",
            r"(?i)report",
        ]

        for indicator in information_indicators:
            if re.search(indicator, text):
                return "INFORMATION"

        # Default to FETCH as it's the most common
        return "FETCH"

    def _extract_additional_fields(self, quest_data: Dict[str, Any], text: str) -> None:
        """
        Extract additional fields based on quest type.

        Args:
            quest_data: Dictionary containing quest information
            text: Quest description text
        """
        quest_type = quest_data["quest_type"]

        # Extract giver (common to all quest types)
        giver_match = re.search(r"(?i)([\w\s]+) (?:asks|requested|needs|wants)", text)
        if giver_match:
            quest_data["giver"] = giver_match.group(1).strip()

        # Extract reward (common to all quest types)
        reward_match = re.search(r"(?i)reward (?:of|is) ([\w\s\d]+)", text)
        if reward_match:
            quest_data["reward"] = reward_match.group(1).strip()

        # Extract type-specific fields
        if quest_type == "FETCH":
            # Extract item to fetch
            item_match = re.search(
                r"(?i)(?:find|bring|get|retrieve|collect) (?:the|a|an)? ([\w\s]+)", text
            )
            if item_match:
                quest_data["item_to_fetch"] = item_match.group(1).strip()

            # Extract recipient
            recipient_match = re.search(
                r"(?i)(?:bring|return|give) (?:it|them)? to (?:the)? ([\w\s]+)", text
            )
            if recipient_match:
                quest_data["recipient"] = recipient_match.group(1).strip()

        elif quest_type == "LOCATION":
            # Extract target location
            location_match = re.search(
                r"(?i)(?:go|travel|reach|visit|explore) (?:to|the)? ([\w\s]+)", text
            )
            if location_match:
                quest_data["target_location"] = location_match.group(1).strip()

        elif quest_type == "COMBAT":
            # Extract target enemy
            enemy_match = re.search(
                r"(?i)(?:defeat|kill|slay|fight) (?:the|a|an)? ([\w\s]+)", text
            )
            if enemy_match:
                quest_data["target_enemy"] = enemy_match.group(1).strip()

        elif quest_type == "INFORMATION":
            # Extract information
            info_match = re.search(
                r"(?i)(?:tell|inform|message|report) .* (?:that|about) ([\w\s]+)", text
            )
            if info_match:
                quest_data["information"] = info_match.group(1).strip()

            # Extract source
            source_match = re.search(r"(?i)([\w\s]+) (?:tells|informs|says)", text)
            if source_match:
                quest_data["source"] = source_match.group(1).strip()

            # Extract target
            target_match = re.search(
                r"(?i)(?:tell|inform|message|report) ([\w\s]+)", text
            )
            if target_match:
                quest_data["target"] = target_match.group(1).strip()

    def _generate_title(self, text: str) -> str:
        """
        Generate a title for a quest based on the text.

        Args:
            text: Quest description text

        Returns:
            Generated title
        """
        # Look for key nouns
        nouns = re.findall(
            r"(?i)\b(sword|ring|amulet|treasure|monster|dragon|goblin|bandit|cave|dungeon|castle|forest|mountain)\b",
            text,
        )

        if nouns:
            # Use the most frequent noun
            noun_counts = {}
            for noun in nouns:
                noun_counts[noun] = noun_counts.get(noun, 0) + 1

            main_noun = max(noun_counts.items(), key=lambda x: x[1])[0]

            # Generate a title based on the noun and quest type
            quest_type = self._determine_quest_type(text)

            if quest_type == "FETCH":
                return f"The Lost {main_noun.title()}"
            elif quest_type == "LOCATION":
                return f"Journey to the {main_noun.title()}"
            elif quest_type == "COMBAT":
                return f"Defeat the {main_noun.title()}"
            elif quest_type == "INFORMATION":
                return f"Message about the {main_noun.title()}"

        # Default title if no nouns found
        return "Mysterious Quest"

    def _is_duplicate_quest(
        self, new_quest: Dict[str, Any], existing_quests: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if a quest is similar to any existing quests.

        Args:
            new_quest: New quest data
            existing_quests: List of existing quest data

        Returns:
            Boolean indicating if the quest is a duplicate
        """
        for quest in existing_quests:
            # Check if titles are similar
            if new_quest["title"] == quest["title"]:
                return True

            # Check if descriptions are similar (simple check)
            if new_quest["description"] == quest["description"]:
                return True

            # Check if key fields are the same
            if new_quest["quest_type"] == quest["quest_type"]:
                if (
                    new_quest["quest_type"] == "FETCH"
                    and "item_to_fetch" in new_quest
                    and "item_to_fetch" in quest
                ):
                    if new_quest["item_to_fetch"] == quest["item_to_fetch"]:
                        return True
                elif (
                    new_quest["quest_type"] == "LOCATION"
                    and "target_location" in new_quest
                    and "target_location" in quest
                ):
                    if new_quest["target_location"] == quest["target_location"]:
                        return True
                elif (
                    new_quest["quest_type"] == "COMBAT"
                    and "target_enemy" in new_quest
                    and "target_enemy" in quest
                ):
                    if new_quest["target_enemy"] == quest["target_enemy"]:
                        return True
                elif (
                    new_quest["quest_type"] == "INFORMATION"
                    and "information" in new_quest
                    and "information" in quest
                ):
                    if new_quest["information"] == quest["information"]:
                        return True

        return False

    def create_quest_from_data(self, quest_data: Dict[str, Any]) -> Optional[Quest]:
        """
        Create a quest object from quest data.

        Args:
            quest_data: Dictionary containing quest information

        Returns:
            Quest object or None if creation fails
        """
        try:
            quest_type = quest_data["quest_type"]

            # Create basic quest parameters
            quest_params = {
                "title": quest_data["title"],
                "description": quest_data["description"],
                "giver": quest_data.get("giver"),
                "status": QuestStatus.NOT_STARTED,
            }

            # Create quest-specific objects
            if quest_type == "FETCH":
                if "item_to_fetch" not in quest_data or "recipient" not in quest_data:
                    logger.warning("FETCH quest missing required fields")
                    return None

                quest = FetchQuest(
                    item_to_fetch=quest_data["item_to_fetch"],
                    recipient=quest_data["recipient"],
                    **quest_params,
                )

            elif quest_type == "LOCATION":
                if "target_location" not in quest_data:
                    logger.warning("LOCATION quest missing required fields")
                    return None

                quest = LocationQuest(
                    target_location=quest_data["target_location"], **quest_params
                )

            elif quest_type == "COMBAT":
                if "target_enemy" not in quest_data:
                    logger.warning("COMBAT quest missing required fields")
                    return None

                quest = CombatQuest(
                    target_enemy=quest_data["target_enemy"], **quest_params
                )

            elif quest_type == "INFORMATION":
                if (
                    "information" not in quest_data
                    or "source" not in quest_data
                    or "target" not in quest_data
                ):
                    logger.warning("INFORMATION quest missing required fields")
                    return None

                quest = InformationQuest(
                    information=quest_data["information"],
                    source=quest_data["source"],
                    target=quest_data["target"],
                    **quest_params,
                )

            else:
                logger.warning(f"Unknown quest type: {quest_type}")
                return None

            # Add reward as a success consequence if present
            if "reward" in quest_data and quest_data["reward"]:
                # Parse the reward to determine its type
                reward = quest_data["reward"]

                # Check if it's gold
                gold_match = re.search(r"(\d+) gold", reward)
                if gold_match:
                    gold_amount = int(gold_match.group(1))
                    quest.success_consequences.append(
                        QuestConsequence(
                            consequence_type="change_world_state",
                            target="player.gold",
                            parameters={"value": gold_amount},
                        )
                    )

                # Check if it's an item
                item_match = re.search(r"(?:a|an|the) ([\w\s]+)", reward)
                if item_match and not gold_match:
                    item_name = item_match.group(1).strip()
                    quest.success_consequences.append(
                        QuestConsequence(consequence_type="add_item", target=item_name)
                    )

                # Add the reward description to the quest notes
                quest.notes.append(f"Reward: {reward}")

            # Add failure consequences if present
            if (
                "failure_consequences" in quest_data
                and quest_data["failure_consequences"]
            ):
                failure_consequences = quest_data["failure_consequences"]

                # Handle both string and list formats
                if isinstance(failure_consequences, str):
                    consequences = [failure_consequences]
                elif isinstance(failure_consequences, list):
                    consequences = failure_consequences
                else:
                    consequences = []

                # Add each consequence
                for consequence in consequences:
                    # Check for reputation loss
                    reputation_match = re.search(
                        r"reputation with ([\w\s]+)", consequence, re.IGNORECASE
                    )
                    if reputation_match:
                        faction = reputation_match.group(1).strip()
                        quest.failure_consequences.append(
                            QuestConsequence(
                                consequence_type="change_world_state",
                                target=f"player.reputation.{faction}",
                                parameters={"value": -10},  # Default reputation loss
                            )
                        )

                    # Check for quest giver relationship
                    if re.search(
                        r"(no more|not give|never give|no longer) quests",
                        consequence,
                        re.IGNORECASE,
                    ):
                        if quest.giver:
                            quest.failure_consequences.append(
                                QuestConsequence(
                                    consequence_type="change_world_state",
                                    target=f"npc.{quest.giver}.quest_giver_status",
                                    parameters={"value": "inactive"},
                                )
                            )

                    # Add the consequence description to the quest notes
                    quest.notes.append(f"Failure Consequence: {consequence}")

            return quest

        except Exception as e:
            logger.error(f"Error creating quest from data: {e}")
            return None
