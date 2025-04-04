import requests
from typing import Dict, Any
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-3.5-turbo)
        """
        super().__init__()
        self.name = "OpenAI"
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text using OpenAI API.

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
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an AI game master for a text adventure game. Provide immersive, descriptive responses based on the game world context."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return f"[Network error: {str(e)}]"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "[Error generating response]"
