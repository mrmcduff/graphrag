from enum import Enum
from typing import Dict, List, Any


class LLMType(Enum):
    """Enum for types of LLM backends."""

    LOCAL_API = "local_api"  # Local server API (e.g., llama.cpp server)
    LOCAL_DIRECT = "local_direct"  # Direct model loading (e.g., llama-cpp-python)
    OPENAI = "openai"  # OpenAI API
    ANTHROPIC = "anthropic"  # Anthropic API
    GOOGLE = "google"  # Google API (Gemini)
    RULE_BASED = "rule_based"  # Fallback rule-based system


class LLMProvider:
    """Abstract base class for LLM providers."""

    def __init__(self):
        """Initialize the provider."""
        self.name = "Base LLM Provider"

    def generate_text(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        raise NotImplementedError("Subclasses must implement generate_text()")
