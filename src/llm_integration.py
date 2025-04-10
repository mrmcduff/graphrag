"""
GraphRAG LLM Integration
------------------------
This module provides integration between the GraphRAG game and local LLMs.
It includes a wrapper for the local LLM service and utility functions
for using the LLM within the game context.
"""

import os
import logging
from typing import Dict, Optional, Any, List

# Import the LocalLLMService
from src.local_llm import LocalLLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphRAGLLMIntegration:
    """Integration between GraphRAG game and local LLMs."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        debug: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ):
        """
        Initialize the GraphRAG LLM integration.

        Args:
            model_path: Path to the GGUF model file
            debug: Whether to print debug information
            temperature: Temperature for LLM generation
            max_tokens: Maximum tokens to generate
        """
        self.model_path = model_path
        self.debug = debug
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize the LLM service
        self.llm_service = LocalLLMService(model_path=model_path, debug=debug)

        # Default system prompt for the game
        self.default_system_prompt = (
            "You are an AI assistant in the GraphRAG text adventure game. "
            "The game is set in a fantasy world with locations, characters, and items. "
            "Your role is to interpret player commands and provide appropriate responses. "
            "Keep your responses concise, engaging, and in the style of a text adventure game. "
            "Do not break character or reference that you are an AI."
        )

    def process_command(
        self, command: str, game_state: Dict[str, Any], context: Optional[str] = None
    ) -> str:
        """
        Process a player command using the local LLM.

        Args:
            command: The player's command
            game_state: The current game state
            context: Additional context to provide to the LLM

        Returns:
            The LLM's response to the command
        """
        # Create a prompt with the game state and command
        prompt = self._create_game_prompt(command, game_state, context)

        # Generate a response using the LLM
        response = self.llm_service.generate_response(
            prompt=prompt,
            system_prompt=self.default_system_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response

    def _create_game_prompt(
        self, command: str, game_state: Dict[str, Any], context: Optional[str] = None
    ) -> str:
        """
        Create a prompt for the LLM based on the game state and command.

        Args:
            command: The player's command
            game_state: The current game state
            context: Additional context to provide to the LLM

        Returns:
            A formatted prompt string
        """
        # Extract relevant information from the game state
        current_location = game_state.get("current_location", "unknown")
        visited_locations = game_state.get("visited_locations", [])
        inventory = game_state.get("inventory", [])
        characters_present = game_state.get("characters_present", [])

        # Format the prompt with the game state information
        prompt = f"Current location: {current_location}\n"

        if visited_locations:
            prompt += f"Visited locations: {', '.join(visited_locations)}\n"

        if inventory:
            prompt += f"Inventory: {', '.join(inventory)}\n"

        if characters_present:
            prompt += f"Characters present: {', '.join(characters_present)}\n"

        if context:
            prompt += f"\nContext: {context}\n"

        # Add the player's command
        prompt += f"\nPlayer command: {command}\n"

        return prompt


def download_llama_model(model_name: str = "llama-3-8b-instruct.Q4_K_M.gguf") -> str:
    """
    Download the Llama 3 model if it doesn't exist.

    Args:
        model_name: Name of the model file to download

    Returns:
        Path to the downloaded model
    """
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, model_name)

    # Check if model already exists
    if os.path.exists(model_path):
        logger.info(f"Model already exists at {model_path}")
        return model_path

    # Model doesn't exist, provide instructions for downloading
    logger.info(
        f"Model not found at {model_path}. "
        f"Please download the model from https://huggingface.co/PawanKrd/Meta-Llama-3-8B-Instruct-GGUF "
        f"and place it in the {models_dir} directory."
    )

    # Provide a more specific message about which file to download
    print(f"""
    =====================================================================
    MODEL DOWNLOAD REQUIRED
    =====================================================================
    
    To use the local LLM feature, you need to download the Llama 3 8B model.
    
    1. Visit: https://huggingface.co/PawanKrd/Meta-Llama-3-8B-Instruct-GGUF
    2. Download the file: {model_name}
    3. Save it to: {model_path}
    
    The Q4_K_M quantization provides a good balance between quality and 
    resource usage, requiring about 4.7GB of RAM/VRAM.
    
    For lower resource usage, consider Q3_K_M (~3.6GB) or Q2_K (~2.5GB) variants.
    For higher quality, consider Q5_K_M (~5.8GB) or Q6_K (~7GB) variants.
    
    After downloading, restart the application.
    =====================================================================
    """)

    return model_path


# Example usage
if __name__ == "__main__":
    # Download the model if it doesn't exist
    model_path = download_llama_model()

    # Create the LLM integration
    llm = GraphRAGLLMIntegration(model_path=model_path, debug=True)

    # Example game state
    game_state = {
        "current_location": "Forest Edge",
        "visited_locations": ["Riverdale", "Forest Edge"],
        "inventory": ["Map", "Compass"],
        "characters_present": ["Old Man"],
    }

    # Process a command
    response = llm.process_command("look around", game_state)
    print(f"LLM Response: {response}")
