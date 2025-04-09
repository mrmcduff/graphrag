"""
GraphRAG Text Adventure Game API Client.

This module provides a simple client for interacting with the GraphRAG text adventure game API.
"""
import requests
import json
import argparse
import sys
from typing import Dict, Any, Optional


class GraphRAGApiClient:
    """Client for interacting with the GraphRAG text adventure game API."""
    
    def __init__(self, api_url: str = "http://localhost:8000/api"):
        """
        Initialize the client.
        
        Args:
            api_url: Base URL for the API
        """
        self.api_url = api_url
        self.session_id: Optional[str] = None
        
    def create_new_game(self, game_data_dir: str = "data/output", config: Dict[str, Any] = None, 
                     provider_id: int = 4, provider_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new game session.
        
        Args:
            game_data_dir: Directory containing game data files
            config: Optional configuration dictionary
            provider_id: LLM provider ID (1-6, default: 4 for Anthropic)
            provider_config: Optional configuration for the LLM provider (e.g., model, api_key)
            
        Returns:
            Initial game state
        """
        response = requests.post(f"{self.api_url}/game/new", json={
            "game_data_dir": game_data_dir,
            "config": config or {},
            "provider_id": provider_id,
            "provider_config": provider_config or {}
        })
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
            return data
        else:
            raise Exception(f"Failed to create game: {response.text}")
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """
        Send a command to the game.
        
        Args:
            command: Command to send
            
        Returns:
            Command result
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        response = requests.post(f"{self.api_url}/game/{self.session_id}/command", json={
            "command": command
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to send command: {response.text}")
    
    def save_game(self, filename: str = None) -> Dict[str, Any]:
        """
        Save the current game state.
        
        Args:
            filename: Save file name
            
        Returns:
            Save result
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        payload = {}
        if filename:
            payload["filename"] = filename
        
        response = requests.post(f"{self.api_url}/game/{self.session_id}/save", json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to save game: {response.text}")
    
    def load_game(self, filename: str) -> Dict[str, Any]:
        """
        Load a saved game state.
        
        Args:
            filename: Save file name
            
        Returns:
            Load result
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        response = requests.post(f"{self.api_url}/game/{self.session_id}/load", json={
            "filename": filename
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to load game: {response.text}")
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Get the current game state.
        
        Returns:
            Current game state
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        response = requests.get(f"{self.api_url}/game/{self.session_id}/state")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get game state: {response.text}")
    
    def set_llm_provider(self, provider_id: int) -> Dict[str, Any]:
        """
        Set the LLM provider for the game session.
        
        Args:
            provider_id: LLM provider ID (1-6)
            
        Returns:
            Result
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        response = requests.post(f"{self.api_url}/game/{self.session_id}/llm", json={
            "provider_id": provider_id
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to set LLM provider: {response.text}")
    
    def end_game_session(self) -> Dict[str, Any]:
        """
        End the current game session.
        
        Returns:
            Result
        """
        if not self.session_id:
            raise Exception("No active game session. Call create_new_game() first.")
        
        response = requests.delete(f"{self.api_url}/game/{self.session_id}")
        
        if response.status_code == 200:
            result = response.json()
            self.session_id = None
            return result
        else:
            raise Exception(f"Failed to end game session: {response.text}")


def display_response(response: Dict[str, Any]) -> None:
    """
    Display the formatted response from the API.
    
    Args:
        response: API response
    """
    print("\n" + "=" * 60)
    
    # Display content with formatting
    for content in response.get("content", []):
        text = content.get("text", "")
        format_type = content.get("format", "normal")
        
        # In a real client, you would use the format and color for display
        # Here we just add some simple formatting for the console
        if format_type == "combat":
            print(f"🗡️  {text}")
        elif format_type == "location":
            print(f"📍 {text}")
        elif format_type == "inventory":
            print(f"🎒 {text}")
        elif format_type == "welcome":
            print(f"✨ {text}")
        else:
            print(text)
    
    print("=" * 60)


def interactive_mode(client: GraphRAGApiClient) -> None:
    """
    Run an interactive game session.
    
    Args:
        client: GraphRAG API client
    """
    try:
        # Let the user choose the LLM provider
        print("Choose an LLM provider:")
        print("1. Local API (e.g., llama.cpp server)")
        print("2. Local direct model loading")
        print("3. OpenAI")
        print("4. Anthropic Claude (default)")
        print("5. Google Gemini")
        print("6. Rule-based (no LLM)")
        
        provider_choice = input("Enter your choice (1-6) [4]: ").strip()
        
        # Default to Anthropic (4) if no input
        if not provider_choice:
            provider_id = 4
        else:
            try:
                provider_id = int(provider_choice)
                if provider_id < 1 or provider_id > 6:
                    print("Invalid choice. Using default (4. Anthropic Claude).")
                    provider_id = 4
            except ValueError:
                print("Invalid input. Using default (4. Anthropic Claude).")
                provider_id = 4
        
        # Get additional configuration based on provider
        provider_config = {}
        
        # For providers that need a model name
        if provider_id == 3:  # OpenAI
            default_model = "gpt-3.5-turbo"
            model = input(f"Enter model name [default: {default_model}]: ").strip() or default_model
            provider_config['model'] = model
        elif provider_id == 4:  # Anthropic
            default_model = "claude-3-haiku-20240307"
            model = input(f"Enter model name [default: {default_model}]: ").strip() or default_model
            provider_config['model'] = model
        elif provider_id == 5:  # Google
            default_model = "gemini-pro"
            model = input(f"Enter model name [default: {default_model}]: ").strip() or default_model
            provider_config['model'] = model
        elif provider_id == 1:  # Local API
            host = input("Enter host [default: localhost]: ").strip() or "localhost"
            port = input("Enter port [default: 8000]: ").strip() or "8000"
            provider_config['host'] = host
            provider_config['port'] = port
        elif provider_id == 2:  # Local direct
            model_path = input("Enter model path: ").strip()
            if model_path:
                provider_config['model_path'] = model_path
        
        # Create a new game with the chosen provider and configuration
        print(f"Creating a new game session with provider {provider_id}...")
        game = client.create_new_game(provider_id=provider_id, provider_config=provider_config)
        
        print(f"Game session created with ID: {client.session_id}")
        display_response(game)
        
        # Game loop
        running = True
        while running:
            command = input("\n> ").strip()
            
            if command.lower() in ["quit", "exit"]:
                running = False
                print("Thanks for playing!")
                client.end_game_session()
                break
            
            # Send command to API
            try:
                response = client.send_command(command)
                display_response(response)
            except Exception as e:
                print(f"Error: {str(e)}")
    
    except KeyboardInterrupt:
        print("\nGame session terminated.")
        if client.session_id:
            client.end_game_session()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        if client.session_id:
            try:
                client.end_game_session()
            except:
                pass


def main():
    """Run the API client."""
    parser = argparse.ArgumentParser(description='GraphRAG Text Adventure Game API Client')
    parser.add_argument('--api-url', type=str, default='http://localhost:5000/api',
                        help='Base URL for the API')
    parser.add_argument('--game-data-dir', type=str, default='data/output',
                        help='Directory containing game data files')
    
    args = parser.parse_args()
    
    client = GraphRAGApiClient(api_url=args.api_url)
    
    try:
        interactive_mode(client)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
