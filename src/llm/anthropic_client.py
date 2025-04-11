"""
Anthropic client for GraphRAG.

This module provides a client for Anthropic's Claude API.
"""

import os
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for Anthropic Claude API."""

    def __init__(self, api_key: str = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model

    def generate_text(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> str:
        """
        Generate text from a prompt using Anthropic API.

        Args:
            prompt: The prompt to generate text from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.api_key:
            logger.warning("Anthropic API key not available. Returning empty response.")
            return "[]"

        try:
            # Import here to avoid requiring these dependencies if not used
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Generate text with the API
            system_message = (
                "You are an expert quest designer for RPG games. Your task is to extract quest information from text and format it as structured JSON. "
                "A quest in the game can be one of the following types: FETCH (get an item and bring it to an NPC), "
                "LOCATION (travel to a specific location), COMBAT (defeat a specific enemy), or INFORMATION (deliver information between NPCs). "
                "For each quest, include the following fields in your JSON response: "
                "title (creative and engaging), description (detailed), quest_type (FETCH, LOCATION, COMBAT, or INFORMATION), "
                "giver (NPC who gives the quest), and type-specific fields such as: "
                "target_location (for LOCATION quests), item_to_fetch and recipient (for FETCH quests), "
                "target_enemy (for COMBAT quests), or information, source, and target (for INFORMATION quests). "
                "Also include reward (specific amount and type), difficulty (EASY, MEDIUM, HARD), "
                "time_limit (if mentioned), and failure_consequences (as an array of specific consequences). "
                "If information is missing, use your creativity to suggest appropriate values. "
                "Format your response as a JSON array containing quest objects. If no quests are found, return an empty array: []. "
                "Always ensure the JSON is valid and complete."
            )

            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the generated text
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating text with Anthropic API: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return f"Anthropic Claude ({self.model})"

    @property
    def description(self) -> str:
        return (
            "Uses Anthropic's Claude API. Requires an API key and internet connection."
        )
