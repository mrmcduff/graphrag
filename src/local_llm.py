"""
Local LLM Service for GraphRAG
------------------------------
This module provides integration with local LLMs, specifically Llama 3 8B,
to provide a lightweight, cost-effective alternative to cloud-based LLMs.
"""

import os
import logging
from typing import Dict, List, Optional, Union, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalLLMService:
    """Service for running Llama 3 8B locally with GraphRAG."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_name: str = "llama3-8b-instruct",
        context_size: int = 4096,
        debug: bool = False
    ):
        """
        Initialize the local LLM service.

        Args:
            model_path: Path to the GGUF model file (required for Llama models)
            model_name: Name/identifier of the model
            context_size: Maximum context window size
            debug: Whether to print debug information
        """
        self.model_path = model_path
        self.model_name = model_name
        self.context_size = context_size
        self.debug = debug
        self.model = None

        # Lazy loading - model will be loaded on first use
        self._model_loaded = False

    def _load_model(self):
        """Load the Llama model using llama-cpp-python."""
        if self._model_loaded:
            return

        try:
            from llama_cpp import Llama

            if self.debug:
                logger.info(f"Loading Llama model: {self.model_name}")

            if not self.model_path or not os.path.exists(self.model_path):
                raise ValueError(
                    "Model path not provided or doesn't exist. "
                    "Download a GGUF format model file and provide the path."
                )

            # Load the model
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.context_size,
                n_gpu_layers=-1,  # Use all available GPU layers
                verbose=self.debug
            )

            self._model_loaded = True

            if self.debug:
                logger.info("Llama model loaded successfully")

        except ImportError:
            logger.error("llama-cpp-python not installed. Run: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"Failed to load Llama model: {e}")
            raise

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate a response from the local LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling (higher = more random)
            top_p: Top-p sampling parameter
            stop_sequences: List of sequences that will stop generation

        Returns:
            Generated text response
        """
        # Load the model if not already loaded
        if not self._model_loaded:
            self._load_model()

        if not self.model:
            raise ValueError("Model failed to load")

        try:
            # Format the prompt according to Llama 3's chat template
            formatted_prompt = self._format_prompt(prompt, system_prompt)

            if self.debug:
                logger.info(f"Generating with prompt: {formatted_prompt[:100]}...")

            # Generate the response
            response = self.model.create_completion(
                prompt=formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop_sequences or [],
                echo=False
            )

            # Extract the generated text
            generated_text = response["choices"][0]["text"].strip()

            if self.debug:
                logger.info(f"Generated response: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

    def _format_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Format the prompt according to Llama 3's expected chat template.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions

        Returns:
            Formatted prompt string
        """
        # Default system prompt for GraphRAG if none provided
        if system_prompt is None:
            system_prompt = (
                "You are an AI assistant in a text adventure game. "
                "Respond to the player's commands and help them navigate the world. "
                "Keep responses concise and focused on the game."
            )

        # Llama 3 chat template format
        formatted_prompt = f"<|system|>\n{system_prompt}\n</s>\n{prompt}"
        return formatted_prompt
