import requests
from typing import Dict, Any
from .base import LLMProvider


class GoogleProvider(LLMProvider):
    """Provider for Google Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize the Google provider.

        Args:
            api_key: Google API key
            model: Model to use (default: gemini-1.5-flash)
        """
        super().__init__()
        self.name = "Google Gemini"
        self.api_key = api_key
        self.model = model
        # Add 'models/' prefix if not already present
        model_path = model if model.startswith("models/") else f"models/{model}"
        self.api_url = f"https://generativelanguage.googleapis.com/v1/{model_path}:generateContent"

    def generate_text(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7
    ) -> str:
        """
        Generate text using Google Gemini API.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=30,
            )

            if response.status_code == 200:
                response_json = response.json()
                return response_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Google API error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return f"[Network error: {str(e)}]"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "[Error generating response]"
