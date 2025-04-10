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
    formatted_prompt = f"<|system|>\n{system_prompt}\n</s>\n
