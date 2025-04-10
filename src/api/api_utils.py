"""
Utility functions for API-specific operations.
"""

import os
from typing import Dict, Any, Optional

# Import API key utility
from util.config import get_api_key, load_environment_variables


def get_non_interactive_llm_config(
    provider_id: int, provider_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a complete LLM configuration for non-interactive API usage.

    This function ensures that all necessary configuration parameters are set
    without requiring interactive console input.

    Args:
        provider_id: The LLM provider ID (1-6)
        provider_config: Optional configuration provided by the client

    Returns:
        A complete configuration dictionary for the LLM provider
    """
    # Load environment variables from .env file
    load_environment_variables()

    config = provider_config or {}

    # Default configurations for each provider
    if provider_id == 1:  # Local API
        if "host" not in config:
            config["host"] = os.environ.get("LOCAL_LLM_HOST", "localhost")
        if "port" not in config:
            config["port"] = int(os.environ.get("LOCAL_LLM_PORT", "8000"))

    elif provider_id == 2:  # Local Direct
        if "model_path" not in config:
            config["model_path"] = os.environ.get("LOCAL_MODEL_PATH", "")

    elif provider_id == 3:  # OpenAI
        if "api_key" not in config:
            # Try to get API key from environment or config file
            api_key = get_api_key("openai")
            config["api_key"] = api_key if api_key else ""
        if "model" not in config:
            config["model"] = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

    elif provider_id == 4:  # Anthropic
        if "api_key" not in config:
            # Try to get API key from environment or config file
            api_key = get_api_key("anthropic")
            config["api_key"] = api_key if api_key else ""
        if "model" not in config:
            config["model"] = os.environ.get(
                "ANTHROPIC_MODEL", "claude-3-haiku-20240307"
            )

    elif provider_id == 5:  # Google
        if "api_key" not in config:
            # Try to get API key from environment or config file
            api_key = get_api_key("google")
            config["api_key"] = api_key if api_key else ""
        if "model" not in config:
            config["model"] = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

    # No additional config needed for rule-based (provider_id == 6)

    return config
