"""
OpenAI client for GraphRAG.

This module provides a client for OpenAI's API.
"""

import os
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI API."""

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model

    def generate_text(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> str:
        """
        Generate text from a prompt using OpenAI API.

        Args:
            prompt: The prompt to generate text from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.api_key:
            logger.warning("OpenAI API key not available. Returning empty response.")
            return "[]"

        try:
            # Import here to avoid requiring these dependencies if not used
            import openai

            openai.api_key = self.api_key

            # Generate text with the API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts quest information from text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract the generated text
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating text with OpenAI API: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return f"OpenAI ({self.model})"

    @property
    def description(self) -> str:
        return "Uses OpenAI's API. Requires an API key and internet connection."
