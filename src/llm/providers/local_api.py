import requests
from typing import Dict, Any
from .base import LLMProvider


class LocalAPIProvider(LLMProvider):
    """Provider for local LLM API servers."""

    def __init__(
        self, host: str = "localhost", port: int = 8000, api_path: str = "/api/generate"
    ):
        """
        Initialize the Local API provider.

        Args:
            host: Host address of the local API server
            port: Port number of the local API server
            api_path: API endpoint path
        """
        super().__init__()
        self.name = "Local LLM API"
        self.host = host
        self.port = port
        self.api_url = f"http://{host}:{port}{api_path}"

    def generate_text(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7
    ) -> str:
        """
        Generate text using a local LLM API server.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        try:
            # Construct the request with a system prompt for a text adventure context
            system_prompt = "You are an AI game master for a text adventure game. Provide immersive, descriptive responses based on the game world context."
            full_prompt = f"{system_prompt}\n\n{prompt}"

            response = requests.post(
                self.api_url,
                json={
                    "prompt": full_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=30,
            )

            if response.status_code == 200:
                # The response format may vary depending on the local API implementation
                # This assumes a simple response format with a "response" field
                return response.json().get("response", "[No response received]")
            else:
                print(f"Local API error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return f"[Network error: {str(e)}]"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "[Error generating response]"
