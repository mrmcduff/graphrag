"""
Local direct client for GraphRAG.

This module provides a client for directly loading local LLM models.
"""

import os
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalDirectClient:
    """Client for directly loading local LLM models."""

    def __init__(self, model_path: str):
        """
        Initialize the local direct client.

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

    def generate_text(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> str:
        """
        Generate text from a prompt using a local LLM.

        Args:
            prompt: The prompt to generate text from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

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
                max_tokens=max_tokens,
                temperature=temperature,
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
        return f"Local Direct ({os.path.basename(self.model_path)})"

    @property
    def description(self) -> str:
        return "Directly loads a local LLM model. Requires llama-cpp-python package."
