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
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are a helpful assistant that extracts quest information from text.",
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
