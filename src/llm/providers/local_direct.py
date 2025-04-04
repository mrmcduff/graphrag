from typing import Dict, Any, Optional
from .base import LLMProvider


class LocalDirectProvider(LLMProvider):
    """Provider for directly loaded local models."""

    def __init__(self, model_path: str):
        """
        Initialize the Local Direct provider.

        Args:
            model_path: Path to the local model file
        """
        super().__init__()
        self.name = "Local Direct Model"
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the local model."""
        try:
            # Try to load using llama-cpp-python if available
            try:
                from llama_cpp import Llama

                print(f"Loading model from {self.model_path}...")
                self.model = Llama(model_path=self.model_path, n_ctx=4096, n_threads=4)
                print("Model loaded successfully with llama-cpp-python")
                return
            except ImportError:
                print("llama-cpp-python not found, trying alternative libraries...")

            # Try to load using ctransformers if available
            try:
                from ctransformers import AutoModelForCausalLM

                print(f"Loading model using ctransformers from {self.model_path}...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path, model_type="llama"
                )
                print("Model loaded successfully with ctransformers")
                return
            except ImportError:
                print("ctransformers not found, trying alternative libraries...")

            # If we got here, no suitable library was found
            print(
                "No supported local model library found. Please install llama-cpp-python or ctransformers."
            )
            self.model = None

        except Exception as e:
            print(f"Error loading model: {e}")
            import traceback

            traceback.print_exc()
            self.model = None

    def generate_text(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7
    ) -> str:
        """
        Generate text using the directly loaded model.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if not self.model:
            return "[Error: No model loaded]"

        try:
            # Add a system prompt for text adventure context
            system_prompt = "You are an AI game master for a text adventure game. Provide immersive, descriptive responses based on the game world context."
            full_prompt = f"{system_prompt}\n\n{prompt}"

            # Handle different model interfaces
            if hasattr(self.model, "__call__"):  # For llama_cpp.Llama
                output = self.model(
                    prompt=full_prompt, max_tokens=max_tokens, temperature=temperature
                )
                return output["choices"][0]["text"]

            elif hasattr(self.model, "generate"):  # For ctransformers
                output = self.model.generate(
                    full_prompt, max_new_tokens=max_tokens, temperature=temperature
                )
                return output

            # Add more interfaces as needed for other libraries

            return "[Error: Unsupported model interface]"
        except Exception as e:
            print(f"Error generating with local model: {e}")
            import traceback

            traceback.print_exc()
            return "[Error generating response with local model]"
