"""
Test script for the local LLM integration with GraphRAG
"""

import os
import sys
from src.llm_integration import GraphRAGLLMIntegration, download_llama_model

def main():
    print("GraphRAG Local LLM Test")
    print("======================")
    
    # Download or locate the model
    model_path = download_llama_model()
    
    # Check if model exists
    if not os.path.exists(model_path):
        print("Please download the model as instructed above and run this script again.")
        return
    
    # Initialize the LLM integration
    print(f"Initializing LLM with model: {os.path.basename(model_path)}")
    llm = GraphRAGLLMIntegration(model_path=model_path, debug=True)
    
    # Example game state
    game_state = {
        "current_location": "Forest Edge",
        "visited_locations": ["Riverdale", "Forest Edge"],
        "inventory": ["Map", "Compass"],
        "characters_present": ["Old Man"]
    }
    
    # Interactive command loop
    print("\nEnter commands to test the LLM (type 'exit' to quit):")
    while True:
        command = input("\n> ")
        
        if command.lower() in ('exit', 'quit'):
            break
        
        # Process the command
        print("Generating response...")
        response = llm.process_command(command, game_state)
        
        # Print the response
        print(f"\n{response}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
