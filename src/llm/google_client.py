"""
Google client for GraphRAG.

This module provides a client for Google's Gemini API.
"""

import os
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        """
        Initialize the Google client.

        Args:
            api_key: Google API key
            model: Model to use
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model

    def generate_text(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> str:
        """
        Generate text from a prompt using Google API.

        Args:
            prompt: The prompt to generate text from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.api_key:
            logger.warning("Google API key not available. Returning empty response.")
            return "[]"

        try:
            # Import here to avoid requiring these dependencies if not used
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)

            # Create a model instance
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            # Generate text with the API
            response = model.generate_content(
                [
                    "You are a helpful assistant that extracts quest information from text.",
                    prompt,
                ]
            )

            # Extract the generated text
            return response.text

        except Exception as e:
            logger.error(f"Error generating text with Google API: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return f"Google Gemini ({self.model})"

    @property
    def description(self) -> str:
        return "Uses Google's Gemini API. Requires an API key and internet connection."
