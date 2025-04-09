import time
from typing import Dict, Any, Optional
import os
import sys
import subprocess
import platform


class GameLoop:
    """Main game loop that coordinates all components of the text adventure game."""

    def __init__(self, game_data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the game loop and all required components.

        Args:
            game_data_dir: Directory containing game data files
            config: Optional configuration dictionary
        """
        # Import here to avoid circular imports
        from llm.llm_manager import LLMManager
        from gamestate.game_state import GameState
        from graphrag.graph_rag_engine import GraphRAGEngine
        from combat.combat_system import CombatSystem
        from .command_processor import CommandProcessor
        from .output_manager import OutputManager

        # Set defaults for config if not provided
        self.config = config or {}

        # Initialize components
        print("Initializing LLM Manager...")
        self.llm_manager = LLMManager()

        print(f"Loading game data from {game_data_dir}...")
        self.game_state = GameState(game_data_dir)

        print("Initializing GraphRAG Engine...")
        self.graph_rag_engine = GraphRAGEngine(game_data_dir, self.llm_manager)

        print("Initializing Combat System...")
        self.combat_system = CombatSystem(
            game_state_data=self.game_state.data,
            game_state=self.game_state,
            graph=self.game_state.graph,
            relations_df=self.game_state.relations_df
        )

        print("Initializing Command Processor...")
        self.command_processor = CommandProcessor(
            self.game_state, self.graph_rag_engine, self.combat_system, self.llm_manager
        )

        print("Initializing Output Manager...")
        self.output_manager = OutputManager(self.config.get("output_config", {}))

        # Game control flags
        self.running = False
        self.game_data_dir = game_data_dir

        # Setup initial LLM provider
        print("Setting up LLM provider...")
        self._setup_llm_provider()

    def _setup_llm_provider(self) -> None:
        """Set up the LLM provider based on user choice."""
        print("\nSelect an LLM provider:")
        print("1. Local API (e.g., llama.cpp server)")
        print("2. Local direct model loading")
        print("3. OpenAI")
        print("4. Anthropic Claude")
        print("5. Google Gemini")
        print("6. Rule-based (no LLM)")

        choice = input("Enter your choice (1-6): ")
        try:
            choice = int(choice)
            if choice < 1 or choice > 6:
                raise ValueError("Invalid choice")
        except ValueError:
            print("Invalid choice, defaulting to rule-based provider")
            choice = 6

        # Set up the chosen provider
        self.command_processor.setup_llm_provider(choice)

    def start(self) -> None:
        """Start the game loop."""
        self.running = True

        # Display welcome message
        welcome_message = self._generate_welcome_message()
        self.output_manager.display_text(welcome_message)

        # Show initial location description
        self._display_location_description()

        # Main game loop
        while self.running:
            try:
                # Get player input
                user_input = input("\n> ").strip()

                # Check for quit command
                if user_input.lower() in ["quit", "exit"]:
                    self._handle_quit()
                    break

                # Process command
                result = self.command_processor.process_command(user_input)

                # Display result
                self.output_manager.display_result(result)

                # Handle state changes
                self._handle_state_changes(result)

                # Small pause between commands for readability
                time.sleep(0.2)

            except KeyboardInterrupt:
                print("\nGame interrupted. Saving game...")
                self._handle_quit()
                break
            except Exception as e:
                print(f"\nError in game loop: {e}")
                import traceback

                traceback.print_exc()
                print("\nThe game will try to continue...")

    def _generate_welcome_message(self) -> str:
        """Generate a welcome message using the LLM."""
        current_location = self.game_state.player_location

        prompt = f"""
# Welcome Message
You are starting a text adventure game set in a rich world. You are in {current_location}.

Generate a brief, engaging welcome message that introduces the player to the game world.
Keep it atmospheric and immersive. Describe the starting location briefly and suggest
some initial actions the player might take.

The message should be 3-4 sentences long.
"""

        try:
            # Try to use the LLM for a custom welcome message
            welcome = self.llm_manager.generate_text(prompt)
            return f"\n=== GRAPHRAG TEXT ADVENTURE ===\n\n{welcome}\n\nType 'help' for available commands."
        except Exception as e:
            # Fall back to a default message
            print(f"Could not generate welcome message: {e}")
            return f"\n=== GRAPHRAG TEXT ADVENTURE ===\n\nWelcome to the text adventure! You find yourself in {current_location}. Look around to see what's here.\n\nType 'help' for available commands."

    def _display_location_description(self) -> None:
        """Display a description of the current location."""
        location_query = f"look around {self.game_state.player_location}"
        description = self.graph_rag_engine.generate_response(
            location_query, self.game_state
        )
        self.output_manager.display_text(f"\n{description}")

    def _handle_state_changes(self, result: Dict[str, Any]) -> None:
        """Handle any necessary state changes based on command result."""
        # If location changed, display new location description
        if result.get("action_type") == "movement" and result.get("success", False):
            self._display_location_description()

        # If combat ended, update game state and display result
        if result.get("action_type") == "combat" and not result.get(
            "combat_active", True
        ):
            if result.get("combat_result") == "victory":
                self.output_manager.display_text("\nYou have defeated your enemy!")
            elif result.get("combat_result") == "defeat":
                self.output_manager.display_text("\nYou have been defeated!")
                # Handle player defeat (could be game over or respawn)
                self._handle_player_defeat()
                
        # Handle map display
        if result.get("action_type") == "system":
            from util.debug import debug_print
            debug_print(f"DEBUG: System action detected in game loop: {result}")
            if result.get("display_map", False):
                debug_print("DEBUG: Display map flag detected, calling _display_map")
                self._display_map(result)

    def _handle_player_defeat(self) -> None:
        """Handle player defeat in combat."""
        self.output_manager.display_text(
            "\nYou wake up later, feeling weakened but alive..."
        )
        # Restore some health
        self.combat_system.player_stats["health"] = (
            self.combat_system.player_stats["max_health"] // 2
        )

    def _handle_quit(self) -> None:
        """Handle game exit with optional save."""
        save_on_exit = input("\nSave game before exiting? (y/n): ").lower() == "y"

        if save_on_exit:
            save_file = (
                input("Enter save filename (default: autosave.json): ")
                or "autosave.json"
            )
            success = self.game_state.save_game(save_file)
            if success:
                print(f"Game saved to {save_file}")
            else:
                print(f"Failed to save game to {save_file}")

        self.running = False
        print("\nThanks for playing!")
        
    def _display_map(self, result: Dict[str, Any]) -> None:
        """Generate and display a map image.
        
        Args:
            result: Dictionary with map information
        """
        from util.debug import debug_print
        debug_print(f"DEBUG: Inside _display_map with result: {result}")
        try:
            # Import the map generator
            from map_generator import MapGenerator
            debug_print("DEBUG: Successfully imported MapGenerator")
            
            # Create a map generator with the current game state
            debug_print(f"DEBUG: Creating MapGenerator with game_state.data: {self.game_state.data} and graph: {self.game_state.graph}")
            map_generator = MapGenerator(self.game_state.data, self.game_state.graph)
            debug_print("DEBUG: Successfully created MapGenerator")
            
            # Generate the map based on the map type
            map_type = result.get("map_type", "world")
            current_location = result.get("location", self.game_state.player_location)
            debug_print(f"DEBUG: Map type: {map_type}, Current location: {current_location}")
            
            # Generate the appropriate map
            if map_type == "local":
                self.output_manager.display_text(f"Generating detailed map of {current_location}...", "system")
                debug_print(f"DEBUG: Generating zoomed map for {current_location}")
                map_path = map_generator.generate_zoomed_map(current_location)
                debug_print(f"DEBUG: Generated zoomed map at {map_path}")
            else:
                self.output_manager.display_text("Generating world map...", "system")
                debug_print(f"DEBUG: Generating world map centered on {current_location}")
                map_path = map_generator.generate_map(current_location)
                debug_print(f"DEBUG: Generated world map at {map_path}")
                
            # Display the map
            debug_print(f"DEBUG: Opening image at {map_path}")
            self._open_image(map_path)
            
        except Exception as e:
            import traceback
            from util.debug import debug_print
            debug_print(f"DEBUG: Error in _display_map: {e}")
            if debug_print(""): # Only print traceback in debug mode
                traceback.print_exc()
            self.output_manager.display_text(f"Error generating map: {e}", "error")
            
    def _open_image(self, image_path: str) -> None:
        """Open an image file with the default image viewer.
        
        Args:
            image_path: Path to the image file
        """
        try:
            # Check if the file exists
            from util.debug import debug_print
            debug_print(f"DEBUG: Checking if image exists at {image_path}")
            if not os.path.exists(image_path):
                debug_print(f"DEBUG: Image file not found at {image_path}")
                self.output_manager.display_text(f"Map file not found: {image_path}", "error")
                return
            
            debug_print(f"DEBUG: Image file exists at {image_path}")
            # Open the image with the default viewer based on the OS
            system = platform.system()
            debug_print(f"DEBUG: Operating system: {system}")
            if system == "Darwin":  # macOS
                debug_print(f"DEBUG: Opening image with 'open' command on macOS")
                subprocess.call(["open", image_path])
            elif system == "Windows":
                debug_print(f"DEBUG: Opening image with os.startfile on Windows")
                os.startfile(image_path)
            else:  # Linux
                debug_print(f"DEBUG: Opening image with 'xdg-open' command on Linux")
                subprocess.call(["xdg-open", image_path])
                
            self.output_manager.display_text(f"Map opened in image viewer: {image_path}", "system")
            
        except Exception as e:
            import traceback
            from util.debug import debug_print
            debug_print(f"DEBUG: Error in _open_image: {e}")
            if debug_print(""): # Only print traceback in debug mode
                traceback.print_exc()
            self.output_manager.display_text(f"Error opening map image: {e}", "error")
