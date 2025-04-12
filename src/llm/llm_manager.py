import time
from typing import Dict, List, Any, Optional, Tuple
import importlib


class LLMManager:
    """Class to manage multiple LLM providers."""

    def __init__(self):
        """Initialize the LLM manager."""
        # Import here to avoid circular imports
        from .providers.base import LLMType, LLMProvider
        from .providers.rule_based import RuleBasedProvider

        self.LLMType = LLMType  # Store reference to enum
        self.providers = {}
        self.active_provider = None
        self.fallback_provider = RuleBasedProvider()

    def create_provider(self, provider_type, **kwargs) -> Any:
        """
        Create a provider of the specified type.

        Args:
            provider_type: Type of LLM provider to create
            **kwargs: Provider-specific arguments

        Returns:
            Instantiated LLM provider
        """
        # Import the appropriate provider class based on type
        if provider_type.value == "openai":
            from .providers.openai import OpenAIProvider

            return OpenAIProvider(
                api_key=kwargs.get("api_key", ""),
                model=kwargs.get("model", "gpt-3.5-turbo"),
            )

        elif provider_type.value == "anthropic":
            from .providers.anthropic import AnthropicProvider

            return AnthropicProvider(
                api_key=kwargs.get("api_key", ""),
                model=kwargs.get("model", "claude-3-haiku-20240307"),
            )

        elif provider_type.value == "google":
            from .providers.google import GoogleProvider

            return GoogleProvider(
                api_key=kwargs.get("api_key", ""),
                model=kwargs.get("model", "gemini-1.5-flash"),
            )

        elif provider_type.value == "rule_based":
            from .providers.rule_based import RuleBasedProvider

            return RuleBasedProvider()

        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def add_provider(self, provider_type, provider) -> None:
        """
        Add a provider to the manager.

        Args:
            provider_type: Type of LLM provider
            provider: Provider instance
        """
        self.providers[provider_type] = provider

        # If this is our first provider, make it active
        if not self.active_provider:
            self.active_provider = provider

    def set_active_provider(self, provider_type) -> bool:
        """
        Set the active provider by type.

        Args:
            provider_type: Type of LLM provider to set as active

        Returns:
            Boolean indicating success
        """
        if provider_type in self.providers:
            self.active_provider = self.providers[provider_type]
            print(f"Active provider set to: {self.active_provider.name}")
            return True
        else:
            print(f"Provider {provider_type.value} not found")
            return False

    def get_available_providers(self) -> List[Tuple]:
        """
        Get a list of available providers.

        Returns:
            List of (provider_type, name) tuples
        """
        return [
            (provider_type, provider.name)
            for provider_type, provider in self.providers.items()
        ]

    def generate_text(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7
    ) -> str:
        """
        Generate text using the active provider with fallback.

        Args:
            prompt: Prompt for text generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.active_provider:
            print("No active provider set, using fallback provider")
            return self.fallback_provider.generate_text(prompt, max_tokens, temperature)

        try:
            start_time = time.time()
            response = self.active_provider.generate_text(
                prompt, max_tokens, temperature
            )
            end_time = time.time()

            print(
                f"Response generated using {self.active_provider.name} in {end_time - start_time:.2f} seconds"
            )
            return response
        except Exception as e:
            print(f"Error using active provider: {e}")
            print("Falling back to rule-based provider")
            return self.fallback_provider.generate_text(prompt, max_tokens, temperature)
