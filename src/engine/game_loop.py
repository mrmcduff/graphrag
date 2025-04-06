import time
from typing import Dict, Any, Optional

from src.engine.feedback.command_result import CommandResult


# Updated GameLoop class
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
        from engine.command_processor import CommandProcessor
        from engine.output_manager import OutputManager

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
        self.combat_system = CombatSystem(self.game_state)

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
        # This method remains unchanged from your original implementation
        # ...

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
                # Process any queued commands
                self._process_queue()

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

    def _process_queue(self) -> None:
        """Process all ready commands in the command queue."""
        results = self.command_processor.command_queue.process_queue()

        for result in results:
            if isinstance(result, CommandResult):
                self.output_manager.display_result(result)
            elif isinstance(result, dict) and "message" in result:
                # Handle legacy result format
                print(result["message"])

    def _generate_welcome_message(self) -> str:
        """Generate a welcome message using the LLM."""
        # This method remains largely unchanged from your original implementation
        # ...

    def _display_location_description(self) -> None:
        """Display a description of the current location."""
        location_query = f"look around {self.game_state.player_location}"
        description = self.graph_rag_engine.generate_response(
            location_query, self.game_state
        )
        self.output_manager.display_text(f"\n{description}")

    def _handle_state_changes(self, result: CommandResult) -> None:
        """
        Handle any necessary state changes based on command result.

        Args:
            result: The command result
        """
        # Check for location change
        location_change = False
        for effect in result.effects:
            if (
                effect.type == "state_change"
                and effect.entity_type == "player"
                and effect.property == "location"
            ):
                location_change = True
                break

        if location_change or result.action_type == "movement" and result.success:
            self._display_location_description()

        # Check for combat end
        combat_end = False
        combat_result = None
        for effect in result.effects:
            if (
                effect.type == "state_change"
                and effect.entity_type == "combat"
                and effect.property == "active"
                and effect.new_value is False
            ):
                combat_end = True
                combat_result = effect.description
                break

        if combat_end:
            if "victory" in combat_result:
                self.output_manager.display_text("\nYou have defeated your enemy!")
            elif "defeat" in combat_result:
                self.output_manager.display_text("\nYou have been defeated!")
                self._handle_player_defeat()
            elif "fled" in combat_result:
                self.output_manager.display_text(
                    "\nYou have successfully fled from combat!"
                )

        # Check for game quit
        if (
            result.action_type == "system"
            and hasattr(result, "quit_game")
            and result.quit_game
        ):
            self._handle_quit()

    def _handle_player_defeat(self) -> None:
        """Handle player defeat in combat."""
        self.output_manager.display_text(
            "\nYou wake up later, feeling weakened but alive..."
        )
        # Restore some health
        if hasattr(self.combat_system, "player_stats"):
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
