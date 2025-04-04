import requests
from typing import Dict, Any
from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    """Provider for Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-haiku-20240307)
        """
        super().__init__()
        self.name = "Anthropic Claude"
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text using Anthropic API.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "system": "You are an AI game master for a text adventure game. Provide immersive, descriptive responses based on the game world context.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                print(f"Anthropic API error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return f"[Network error: {str(e)}]"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "[Error generating response]"
