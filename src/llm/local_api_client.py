"""
Local API client for GraphRAG.

This module provides a client for local LLM API servers.
"""

import requests
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalAPIClient:
    """Client for local LLM API servers like llama.cpp server."""

    def __init__(
        self, host: str = "localhost", port: int = 8000, api_path: str = "/api/generate"
    ):
        """
        Initialize the local API client.

        Args:
            host: Host of the API server
            port: Port of the API server
            api_path: Path to the API endpoint
        """
        self.host = host
        self.port = port
        self.api_path = api_path
        self.base_url = f"http://{host}:{port}"

    def generate_text(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> str:
        """
        Generate text from a prompt using a local API server.

        Args:
            prompt: The prompt to generate text from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        try:
            # Prepare the request
            url = f"{self.base_url}{self.api_path}"
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop": ["</s>", "Human:", "USER:"],
            }

            # Make the request
            response = requests.post(url, json=payload, timeout=60)

            # Check for errors
            if response.status_code != 200:
                logger.error(
                    f"Error from API: {response.status_code} - {response.text}"
                )
                return "[]"

            # Parse the response
            result = response.json()

            # Extract the generated text
            if "text" in result:
                return result["text"]
            elif "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["text"]
            else:
                logger.error(f"Unexpected response format: {result}")
                return "[]"

        except Exception as e:
            logger.error(f"Error generating text with local API: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return f"Local API ({self.host}:{self.port})"

    @property
    def description(self) -> str:
        return "Uses a local LLM API server. Requires a running server like llama.cpp server."
