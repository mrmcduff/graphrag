"""
LLM clients for GraphRAG.

This module provides interfaces to different LLM providers for use in the GraphRAG game.
"""

import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the LLM client."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of the LLM client."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM client is available."""
        pass


class RuleBasedClient(LLMClient):
    """A fallback client that uses rule-based processing instead of an LLM."""

    def __init__(self, debug_mode: bool = False):
        """
        Initialize the rule-based client.

        Args:
            debug_mode: Whether to enable debug mode for quest parsing
        """
        self.debug_mode = debug_mode

    def generate_text(self, prompt: str) -> str:
        """
        Generate text using rule-based processing.

        Args:
            prompt: The prompt to process

        Returns:
            Processed text
        """
        if self.debug_mode:
            logger.info(f"Rule-based client received prompt: {prompt[:100]}...")

        # Check if this is a quest extraction prompt
        if "quest" in prompt.lower() and (
            "extract" in prompt.lower() or "identify" in prompt.lower()
        ):
            # Extract the document text from the prompt
            text_start = prompt.find("TEXT:")
            if text_start > 0:
                text = prompt[text_start + 5 :].strip()

                if self.debug_mode:
                    logger.info(f"Extracted text from prompt: {text[:100]}...")

                # Look for quest name/title
                title_match = re.search(r"(?i)Quest Name:\s*([^\n]+)", text)
                if title_match:
                    title = title_match.group(1).strip()

                    # Extract the rest as description
                    description_start = text.find(title) + len(title)
                    description = text[description_start:].strip()

                    # Determine quest type
                    quest_type = "LOCATION"  # Default for the Mt. Dorn quest
                    if (
                        "defeat" in text.lower()
                        or "kill" in text.lower()
                        or "slay" in text.lower()
                    ):
                        quest_type = "COMBAT"
                    elif "find" in text.lower() and not "find a way" in text.lower():
                        quest_type = "FETCH"

                    # Look for giver
                    giver_match = re.search(r"(?i)([\w\s]+)\s+asks", text)
                    giver = giver_match.group(1).strip() if giver_match else ""

                    # Look for reward
                    reward_match = re.search(r"(?i)give the player (\d+ gold)", text)
                    reward = reward_match.group(1) if reward_match else ""

                    # Create quest JSON
                    quest_json = {
                        "title": title,
                        "description": description,
                        "quest_type": quest_type,
                        "giver": giver,
                        "target_location": "Mt. Dorn"
                        if quest_type == "LOCATION"
                        else "",
                        "reward": reward,
                    }

                    if self.debug_mode:
                        logger.info(f"Generated quest JSON: {quest_json}")

                    # Return properly formatted JSON array
                    return "[" + json.dumps(quest_json, indent=2) + "]"

        # Default response is an empty JSON array
        return "[]"

    @property
    def name(self) -> str:
        return "Rule-Based (No LLM)"

    @property
    def description(self) -> str:
        return "Uses rule-based processing instead of an LLM. Limited capabilities but no external dependencies."

    @property
    def is_available(self) -> bool:
        return True


class LocalLLMClient(LLMClient):
    """Client for local LLM models using llama.cpp or similar."""

    def __init__(self, model_path: str = None):
        """
        Initialize the local LLM client.

        Args:
            model_path: Path to the model file
        """
        self.model_path = model_path
        self._model = None

    def _load_model(self):
        """Load the model if not already loaded."""
        if self._model is None and self.model_path:
            try:
                # Import here to avoid requiring these dependencies if not used
                from llama_cpp import Llama

                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=2048,  # Context window size
                    n_threads=4,  # Number of CPU threads to use
                )
                logger.info(f"Loaded local LLM model from {self.model_path}")
            except Exception as e:
                logger.error(f"Error loading local LLM model: {e}")
                self._model = None

    def generate_text(self, prompt: str) -> str:
        """
        Generate text from a prompt using a local LLM.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text
        """
        self._load_model()

        if not self._model:
            logger.warning("Local LLM model not available. Returning empty response.")
            return "[]"

        try:
            # Generate text with the model
            response = self._model(
                prompt,
                max_tokens=1024,
                temperature=0.1,  # Low temperature for more deterministic responses
                stop=["</s>", "Human:", "USER:"],  # Stop tokens
            )

            # Extract the generated text
            if isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["text"]
            else:
                return response

        except Exception as e:
            logger.error(f"Error generating text with local LLM: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return "Local LLM (llama.cpp)"

    @property
    def description(self) -> str:
        return "Uses a local LLM model with llama.cpp. Requires downloading a compatible model file."

    @property
    def is_available(self) -> bool:
        try:
            import llama_cpp

            return self.model_path and os.path.exists(self.model_path)
        except ImportError:
            return False


class OpenAIClient(LLMClient):
    """Client for OpenAI API."""

    def __init__(self, api_key: str = None):
        """
        Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def generate_text(self, prompt: str) -> str:
        """
        Generate text from a prompt using OpenAI API.

        Args:
            prompt: The prompt to generate text from

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
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts quest information from text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for more deterministic responses
                max_tokens=1024,
            )

            # Extract the generated text
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating text with OpenAI API: {e}")
            return "[]"

    @property
    def name(self) -> str:
        return "OpenAI GPT-3.5"

    @property
    def description(self) -> str:
        return "Uses OpenAI's GPT-3.5 API. Requires an API key and internet connection."

    @property
    def is_available(self) -> bool:
        try:
            import openai

            return bool(self.api_key)
        except ImportError:
            return False


def get_available_llm_clients() -> List[LLMClient]:
    """
    Get a list of available LLM clients.

    Returns:
        List of available LLM clients
    """
    clients = []

    # Always add the rule-based client as a fallback
    clients.append(RuleBasedClient())

    # Check for local LLM models
    local_models_dir = os.path.join("models", "llm")
    if os.path.exists(local_models_dir):
        for filename in os.listdir(local_models_dir):
            if filename.endswith((".bin", ".gguf")):
                model_path = os.path.join(local_models_dir, filename)
                client = LocalLLMClient(model_path)
                if client.is_available:
                    clients.append(client)

    # Check for OpenAI API key
    openai_client = OpenAIClient()
    if openai_client.is_available:
        clients.append(openai_client)

    return clients


def select_llm_client(interactive: bool = True, debug_mode: bool = True) -> LLMClient:
    """
    Select an LLM client to use.

    Args:
        interactive: Whether to prompt the user to select a client
        debug_mode: Whether to enable debug mode for quest parsing

    Returns:
        Selected LLM client
    """
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        import os

        # Try to load from project root .env file
        env_file = ".env"
        if not os.path.exists(env_file):
            # Try to find .env in parent directory
            env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
    except ImportError:
        logger.warning(
            "python-dotenv not installed. Environment variables from .env file will not be loaded."
        )
    except Exception as e:
        logger.warning(f"Error loading environment variables: {e}")
    if not interactive:
        # Use the rule-based client if not interactive
        return RuleBasedClient(debug_mode=debug_mode)

    # Print available options (simplified for quest processing)
    print("\nSelect an LLM provider for quest parsing:")
    print("1. Local LLM (llama.cpp)")
    print("2. OpenAI GPT-3.5")
    print("3. Rule-based (no LLM)")
    print("4. Advanced options (Anthropic, Google, etc.)")

    # Prompt for selection
    choice = input("Enter your choice (1-4): ")
    try:
        choice = int(choice)
        if choice < 1 or choice > 4:
            raise ValueError("Invalid choice")
    except ValueError:
        print("Invalid choice, defaulting to rule-based provider")
        choice = 3

    # Create the appropriate client based on the choice
    if choice == 1:  # Local LLM
        print("\nSelect local LLM option:")
        print("1. Use llama.cpp server (API)")
        print("2. Use direct library integration")

        local_choice = input("Enter your choice (1-2): ")
        try:
            local_choice = int(local_choice)
            if local_choice < 1 or local_choice > 2:
                raise ValueError("Invalid choice")
        except ValueError:
            print("Invalid choice, defaulting to rule-based provider")
            return RuleBasedClient(debug_mode=debug_mode)

        if local_choice == 1:  # Local API
            host = input("Enter host (default: localhost): ") or "localhost"
            port = input("Enter port (default: 8000): ") or "8000"
            try:
                # Import here to avoid requiring these dependencies if not used
                from llm.local_api_client import LocalAPIClient

                return LocalAPIClient(host=host, port=int(port))
            except ImportError:
                print("LocalAPIClient not available. Falling back to rule-based.")
                return RuleBasedClient(debug_mode=debug_mode)
        else:  # Local direct
            model_path = input(
                "Enter model path (or press Enter to search models/llm): "
            )
            if not model_path:
                # Look for models in the models/llm directory
                local_models_dir = os.path.join("models", "llm")
                if os.path.exists(local_models_dir):
                    models = [
                        f
                        for f in os.listdir(local_models_dir)
                        if f.endswith((".bin", ".gguf"))
                    ]
                    if models:
                        print("\nAvailable models:")
                        for i, model in enumerate(models):
                            print(f"{i + 1}. {model}")
                        model_choice = input(
                            "\nSelect a model (or press Enter to cancel): "
                        )
                        if model_choice:
                            try:
                                model_index = int(model_choice) - 1
                                if 0 <= model_index < len(models):
                                    model_path = os.path.join(
                                        local_models_dir, models[model_index]
                                    )
                            except ValueError:
                                print("Invalid selection.")

            if model_path and os.path.exists(model_path):
                try:
                    # Import here to avoid requiring these dependencies if not used
                    from llm.local_direct_client import LocalDirectClient

                    return LocalDirectClient(model_path=model_path)
                except ImportError:
                    print(
                        "LocalDirectClient not available. Falling back to rule-based."
                    )
                    return RuleBasedClient(debug_mode=debug_mode)
            else:
                print("No valid model path provided. Falling back to rule-based.")
                return RuleBasedClient(debug_mode=debug_mode)

    elif choice == 2:  # OpenAI
        api_key = input(
            "Enter OpenAI API key (or press Enter to use OPENAI_API_KEY env var): "
        ) or os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                # Import here to avoid requiring these dependencies if not used
                from llm.openai_client import OpenAIClient

                return OpenAIClient(api_key=api_key)
            except ImportError:
                print("OpenAIClient not available. Falling back to rule-based.")
                return RuleBasedClient(debug_mode=debug_mode)
        else:
            print("No API key provided. Falling back to rule-based.")
            return RuleBasedClient(debug_mode=debug_mode)

    elif choice == 3:  # Rule-based
        print("Using rule-based quest extraction (no LLM).")
        return RuleBasedClient(debug_mode=debug_mode)

    elif choice == 4:  # Advanced options
        print("\nAdvanced LLM options:")
        print("1. Anthropic Claude")
        print("2. Google Gemini")
        print("3. Back to main menu")

        adv_choice = input("Enter your choice (1-3): ")
        try:
            adv_choice = int(adv_choice)
            if adv_choice < 1 or adv_choice > 3:
                raise ValueError("Invalid choice")
        except ValueError:
            print("Invalid choice, defaulting to rule-based provider")
            return RuleBasedClient(debug_mode=debug_mode)

        if adv_choice == 1:  # Anthropic
            api_key = input(
                "Enter Anthropic API key (or press Enter to use ANTHROPIC_API_KEY env var): "
            ) or os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    # Import here to avoid requiring these dependencies if not used
                    from llm.anthropic_client import AnthropicClient

                    return AnthropicClient(api_key=api_key)
                except ImportError:
                    print("AnthropicClient not available. Falling back to rule-based.")
                    return RuleBasedClient(debug_mode=debug_mode)
            else:
                print("No API key provided. Falling back to rule-based.")
                return RuleBasedClient(debug_mode=debug_mode)

        elif adv_choice == 2:  # Google
            api_key = input(
                "Enter Google API key (or press Enter to use GOOGLE_API_KEY env var): "
            ) or os.environ.get("GOOGLE_API_KEY")
            if api_key:
                try:
                    # Import here to avoid requiring these dependencies if not used
                    from llm.google_client import GoogleClient

                    return GoogleClient(api_key=api_key)
                except ImportError:
                    print("GoogleClient not available. Falling back to rule-based.")
                    return RuleBasedClient(debug_mode=debug_mode)
            else:
                print("No API key provided. Falling back to rule-based.")
                return RuleBasedClient(debug_mode=debug_mode)

        else:  # Back to main menu
            return select_llm_client(interactive=True, debug_mode=debug_mode)

    else:  # Should not reach here, but just in case
        return RuleBasedClient(debug_mode=debug_mode)
