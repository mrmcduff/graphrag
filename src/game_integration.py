# Add these imports to the top of your enhanced-llm-game-engine.py file
from map_generator import MapGenerator
from combat.combat_system import CombatSystem, CombatStatus


# Modify the TextAdventureGame class to include the new systems
class TextAdventureGame:
    """Main class for running the text adventure game."""

    def __init__(self, game_data_dir: str):
        """
        Initialize the game.

        Args:
            game_data_dir: Directory containing game data files
        """
        self.game_data_dir = game_data_dir

        # Initialize LLM manager
        self.llm_manager = LLMManager()

        # Initialize game state
        self.game_state = GameState(game_data_dir)

        # Initialize RAG engine
        self.rag_engine = GraphRAGEngine(game_data_dir, self.llm_manager)

        # Initialize map generator with GameStateData and graph
        self.map_generator = MapGenerator(self.game_state.data, self.game_state.graph)

        # Initialize combat system with full GameState object
        # Note: This could be refactored in the future to use GameStateData
        self.combat_system = CombatSystem(self.game_state)

        self.running = False
        self.in_combat = False

    def configure_llm(self):
        """Configure LLM options interactively."""
        print("\n=== LLM Configuration ===")
        print("Select LLM provider:")
        print("1. Local API (e.g., llama.cpp server)")
        print("2. Local direct model loading")
        print("3. OpenAI")
        print("4. Anthropic Claude")
        print("5. Google Gemini")
        print("6. Rule-based (no LLM)")

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            host = input("Enter host (default: localhost): ").strip() or "localhost"
            port = input("Enter port (default: 8000): ").strip() or "8000"

            provider = LocalAPIProvider(host=host, port=int(port))
            self.llm_manager.add_provider(LLMType.LOCAL_API, provider)
            self.llm_manager.set_active_provider(LLMType.LOCAL_API)

        elif choice == "2":
            model_path = input("Enter path to model file: ").strip()
            if os.path.exists(model_path):
                provider = LocalDirectProvider(model_path=model_path)
                self.llm_manager.add_provider(LLMType.LOCAL_DIRECT, provider)
                self.llm_manager.set_active_provider(LLMType.LOCAL_DIRECT)
            else:
                print(f"Model file not found: {model_path}")
                print("Using rule-based fallback instead")
                self.llm_manager.add_provider(LLMType.RULE_BASED, RuleBasedProvider())
                self.llm_manager.set_active_provider(LLMType.RULE_BASED)

        elif choice == "3":
            api_key = input("Enter OpenAI API key: ").strip()
            model = (
                input("Enter model name (default: gpt-3.5-turbo): ").strip()
                or "gpt-3.5-turbo"
            )

            if api_key:
                provider = OpenAIProvider(api_key=api_key, model=model)
                self.llm_manager.add_provider(LLMType.OPENAI, provider)
                self.llm_manager.set_active_provider(LLMType.OPENAI)
            else:
                print("No API key provided. Using rule-based fallback instead")
                self.llm_manager.add_provider(LLMType.RULE_BASED, RuleBasedProvider())
                self.llm_manager.set_active_provider(LLMType.RULE_BASED)

        elif choice == "4":
            api_key = input("Enter Anthropic API key: ").strip()
            model = (
                input("Enter model name (default: claude-3-haiku-20240307): ").strip()
                or "claude-3-haiku-20240307"
            )

            if api_key:
                provider = AnthropicProvider(api_key=api_key, model=model)
                self.llm_manager.add_provider(LLMType.ANTHROPIC, provider)
                self.llm_manager.set_active_provider(LLMType.ANTHROPIC)
            else:
                print("No API key provided. Using rule-based fallback instead")
                self.llm_manager.add_provider(LLMType.RULE_BASED, RuleBasedProvider())
                self.llm_manager.set_active_provider(LLMType.RULE_BASED)

        elif choice == "5":
            api_key = input("Enter Google API key: ").strip()
            model = (
                input("Enter model name (default: gemini-pro): ").strip()
                or "gemini-pro"
            )

            if api_key:
                provider = GoogleProvider(api_key=api_key, model=model)
                self.llm_manager.add_provider(LLMType.GOOGLE, provider)
                self.llm_manager.set_active_provider(LLMType.GOOGLE)
            else:
                print("No API key provided. Using rule-based fallback instead")
                self.llm_manager.add_provider(LLMType.RULE_BASED, RuleBasedProvider())
                self.llm_manager.set_active_provider(LLMType.RULE_BASED)

        elif choice == "6":
            provider = RuleBasedProvider()
            self.llm_manager.add_provider(LLMType.RULE_BASED, provider)
            self.llm_manager.set_active_provider(LLMType.RULE_BASED)

        else:
            print("Invalid choice. Using rule-based fallback instead")
            self.llm_manager.add_provider(LLMType.RULE_BASED, RuleBasedProvider())
            self.llm_manager.set_active_provider(LLMType.RULE_BASED)

    def start(self):
        """Start the game."""
        # Configure LLM first
        self.configure_llm()

        self.running = True

        # Display welcome message
        print("\n" + "=" * 60)
        print("Welcome to the Text Adventure Game with GraphRAG!")
        print("Type 'help' for commands or 'quit' to exit.")
        print("=" * 60 + "\n")

        # Show initial location
        initial_context = self.game_state.get_current_context()
        print(f"You find yourself in {initial_context['player']['location']}.")

        if initial_context["npcs_present"]:
            npcs = list(initial_context["npcs_present"].keys())
            print(f"You can see: {', '.join(npcs)}.")

        print("\nWhat would you like to do?")

        # Main game loop
        while self.running:
            # Get player input
            command = input("\n> ").strip()

            # Skip empty commands
            if not command:
                continue

            # Check if we're in combat mode
            if self.in_combat:
                self._handle_combat_command(command)
                continue

            # Handle special commands
            if self._handle_special_command(command):
                continue

            # Process regular command through the RAG engine
            response = self.rag_engine.generate_response(command, self.game_state)
            print("\n" + response)

    def _handle_special_command(self, command: str) -> bool:
        """
        Handle special game commands.

        Args:
            command: The command to handle

        Returns:
            Boolean indicating if the command was handled
        """
        command_lower = command.lower()

        # Exit commands
        if command_lower in ["quit", "exit"]:
            self.running = False
            print("Thanks for playing!")
            return True

        # Help command
        elif command_lower == "help":
            self._show_help()
            return True

        # Save and load commands
        elif command_lower == "save":
            save_path = os.path.join(self.game_data_dir, "savegame.json")
            if self.game_state.save_game(save_path):
                print(f"Game saved to {save_path}")
            else:
                print("Failed to save game")
            return True

        elif command_lower == "load":
            save_path = os.path.join(self.game_data_dir, "savegame.json")
            if os.path.exists(save_path):
                if self.game_state.load_game(save_path):
                    print("Game loaded successfully")

                    # Show current location after loading
                    context = self.game_state.get_current_context()
                    print(f"You are in {context['player']['location']}.")
                else:
                    print("Failed to load game")
            else:
                print("No save file found")
            return True

        # Inventory command
        elif command_lower == "inventory":
            self._show_inventory()
            return True

        # LLM management commands
        elif command_lower == "change llm":
            self.configure_llm()
            return True

        elif command_lower == "llm info":
            self._show_llm_info()
            return True

        # Map commands
        elif command_lower == "map":
            self._show_map()
            return True

        elif command_lower == "local map":
            self._show_local_map()
            return True

        # Combat commands
        elif command_lower.startswith("attack "):
            target = command_lower[7:].strip()
            self._start_combat(target)
            return True

        elif command_lower == "stats":
            self._show_stats()
            return True

        elif command_lower.startswith("equip "):
            item = command_lower[6:].strip()
            self._equip_item(item)
            return True

        # Not a special command
        return False

    def _handle_combat_command(self, command: str):
        """
        Handle commands during combat.

        Args:
            command: The combat command
        """
        command_lower = command.lower()

        # Check for combat exit commands
        if command_lower in ["quit", "exit"]:
            self.running = False
            print("Thanks for playing!")
            return

        elif command_lower == "help":
            print(self.combat_system.get_combat_help())
            return

        elif command_lower == "status":
            self._show_combat_status()
            return

        # Parse combat commands
        action = command_lower
        target = None

        # Check for commands with targets
        if " " in command_lower:
            action, target = command_lower.split(" ", 1)

        # Process combat action
        if (
            action in ["attack", "block", "dodge", "flee"]
            or action in ["use", "cast"]
            and target
        ):
            result = self.combat_system.process_combat_action(action, target)

            # Display combat log
            if "combat_log" in result:
                for log_entry in result["combat_log"]:
                    print(log_entry)

            # Check if combat has ended
            combat_status = self.combat_system.get_combat_status()
            if combat_status["in_combat"] and combat_status["status"] != "active":
                # Combat has ended
                end_result = self.combat_system.end_combat()

                # Display end results
                if end_result["status"] == "player_victory":
                    print(f"\nYou have defeated {end_result['enemy']}!")

                    if "experience_gained" in end_result:
                        print(
                            f"You gained {end_result['experience_gained']} experience."
                        )

                    if "drops" in end_result:
                        print(f"You obtained: {', '.join(end_result['drops'])}")

                    if (
                        "player_level" in end_result
                        and end_result["player_level"]
                        > self.combat_system.player_stats["level"]
                    ):
                        print(f"You leveled up to level {end_result['player_level']}!")

                elif end_result["status"] == "player_defeated":
                    print("\nYou have been defeated. You wake up later, barely alive.")

                elif end_result["status"] == "player_fled":
                    print("\nYou successfully fled from combat.")

                # Exit combat mode
                self.in_combat = False
                print("\nWhat would you like to do now?")
        else:
            print("Unknown combat command. Type 'help' to see available commands.")

    def _show_help(self):
        """Display help information."""
        print("\n--- COMMAND HELP ---")
        print("look: Examine your surroundings")
        print("go [location]: Move to a connected location")
        print("talk [character]: Talk to a character in your location")
        print("take [item]: Pick up an item")
        print("use [item]: Use an item in your inventory")
        print("inventory: Check your inventory")
        print("stats: Show your character stats")
        print("equip [item]: Equip a weapon or armor")
        print("attack [enemy]: Start combat with an enemy")
        print("map: Show the world map")
        print("local map: Show a detailed map of your current location")
        print("save: Save your game")
        print("load: Load a saved game")
        print("change llm: Change LLM provider")
        print("llm info: Show information about configured LLMs")
        print("quit: Exit the game")
        print("-------------------")

    def _show_inventory(self):
        """Display the player's inventory."""
        if self.game_state.inventory:
            print("You are carrying:")
            for item in self.game_state.inventory:
                equipped = ""
                if item == self.combat_system.player_stats.get("equipped_weapon"):
                    equipped = " (Equipped Weapon)"
                elif item == self.combat_system.player_stats.get("equipped_armor"):
                    equipped = " (Equipped Armor)"

                print(f"- {item}{equipped}")
        else:
            print("Your inventory is empty.")

    def _show_llm_info(self):
        """Display information about configured LLMs."""
        available_providers = self.llm_manager.get_available_providers()
        print("\nConfigured LLM providers:")
        for i, (provider_type, provider_name) in enumerate(available_providers, 1):
            active = (
                " (active)"
                if self.llm_manager.active_provider.name == provider_name
                else ""
            )
            print(f"{i}. {provider_name}{active}")

    def _show_map(self):
        """Display the world map."""
        try:
            # Generate map centered on current location
            map_path = self.map_generator.generate_map(self.game_state.player_location)

            # In a terminal, we can't show the actual image, so provide information
            print(f"World map has been generated and saved to: {map_path}")
            print("Locations you've visited:")

            for i, location in enumerate(sorted(self.game_state.visited_locations), 1):
                current = (
                    " (You are here)"
                    if location == self.game_state.player_location
                    else ""
                )
                print(f"{i}. {location}{current}")

            print("\nConnected locations:")
            location_info = self.map_generator._get_location_info(
                self.game_state.player_location
            )
            for i, connected in enumerate(
                sorted(location_info["connected_locations"]), 1
            ):
                visited = (
                    " (Visited)"
                    if connected in self.game_state.visited_locations
                    else ""
                )
                print(f"{i}. {connected}{visited}")

        except Exception as e:
            print(f"Error generating map: {e}")

    def _show_local_map(self):
        """Display a detailed map of the current location."""
        try:
            # Generate detailed map of current location
            map_path = self.map_generator.generate_zoomed_map(
                self.game_state.player_location
            )

            # In a terminal, we can't show the actual image, so provide information
            print(
                f"Local map of {self.game_state.player_location} has been generated and saved to: {map_path}"
            )
            print("Points of interest:")

            # Define some generic points of interest based on location type
            location_type = self.map_generator.location_types.get(
                self.game_state.player_location, "default"
            )

            if location_type == "town":
                points = ["Town Square", "Marketplace", "Inn", "Blacksmith"]
            elif location_type == "forest":
                points = ["Clearing", "Ancient Tree", "Stream", "Dense Woods"]
            elif location_type == "mountain":
                points = [
                    "Mountain Pass",
                    "Lookout Point",
                    "Cave Entrance",
                    "Rocky Slope",
                ]
            elif location_type == "water":
                points = ["Shore", "Deep Water", "Small Island", "Current"]
            elif location_type == "dungeon":
                points = ["Entrance", "Main Hall", "Dark Corridor", "Treasure Room"]
            elif location_type == "castle":
                points = ["Main Gate", "Courtyard", "Keep", "Throne Room"]
            else:
                points = ["Central Area", "Path Junction", "Landmark", "Resting Spot"]

            for i, point in enumerate(points, 1):
                print(f"{i}. {point}")

            print("\nCharacters present:")
            npcs_here = [
                npc
                for npc, data in self.game_state.npc_states.items()
                if data["location"] == self.game_state.player_location
            ]

            if npcs_here:
                for i, npc in enumerate(npcs_here, 1):
                    print(f"{i}. {npc}")
            else:
                print("None")

        except Exception as e:
            print(f"Error generating local map: {e}")

    def _start_combat(self, target: str):
        """
        Start combat with the specified target.

        Args:
            target: Name of the enemy to attack
        """
        # Check if target exists and is valid
        available_enemies = self.combat_system.get_available_enemies()

        if target not in available_enemies:
            print(f"There is no enemy named '{target}' here that you can attack.")
            return

        # Start combat
        success = self.combat_system.start_combat(target)

        if success:
            print(f"\n=== COMBAT: {target} ===")
            print(f"You engage in combat with {target}!")

            # Show initial combat status
            self._show_combat_status()

            # Enter combat mode
            self.in_combat = True

            print("\nEnter combat commands (type 'help' for combat help):")
        else:
            print(f"Failed to start combat with {target}.")

    def _show_combat_status(self):
        """Display the current combat status."""
        status = self.combat_system.get_combat_status()

        if not status["in_combat"]:
            print("You are not in combat.")
            return

        print("\n--- Combat Status ---")
        print(f"Enemy: {status['enemy']} (Level {status['enemy_level']})")
        print(f"Enemy Health: {status['enemy_health']}")
        print(f"Your Health: {status['player_health']}")
        print(f"Your Mana: {status['player_mana']}")
        print(f"Turn: {status['combat_turn']}")

        print("\nRecent Events:")
        for log_entry in status["combat_log"]:
            print(f"- {log_entry}")

    def _show_stats(self):
        """Display the player's stats."""
        stats = self.combat_system.player_stats

        print("\n--- Character Stats ---")
        print(f"Level: {stats['level']} (Experience: {stats['experience']})")
        print(f"Health: {stats['health']}/{stats['max_health']}")
        print(f"Stamina: {stats['stamina']}/{stats['max_stamina']}")
        print(f"Mana: {stats['mana']}/{stats['max_mana']}")
        print(f"Strength: {stats['strength']}")
        print(f"Dexterity: {stats['dexterity']}")
        print(f"Intelligence: {stats['intelligence']}")
        print(f"Defense: {stats['defense']}")
        print(f"Evasion: {stats['evasion']}")
        print(f"Critical Chance: {stats['critical_chance']}%")

        print("\nEquipment:")
        weapon = stats.get("equipped_weapon", "None")
        armor = stats.get("equipped_armor", "None")
        print(f"Weapon: {weapon}")
        print(f"Armor: {armor}")

        print("\nAbilities:")
        for ability in stats.get("abilities", []):
            print(f"- {ability}")

    def _equip_item(self, item: str):
        """
        Equip the specified item.

        Args:
            item: Name of the item to equip
        """
        # Check if item is in inventory
        if item not in self.game_state.inventory:
            print(f"You don't have {item} in your inventory.")
            return

        # Try to equip as weapon first
        if self.combat_system.equip_weapon(item):
            print(f"You equip {item} as your weapon.")
            return

        # Try to equip as armor
        if self.combat_system.equip_armor(item):
            print(f"You equip {item} as your armor.")
            return

        # Item can't be equipped
        print(f"{item} cannot be equipped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a GraphRAG-based text adventure game with flexible LLM options"
    )
    parser.add_argument(
        "--game_data_dir", required=True, help="Directory containing game data files"
    )

    args = parser.parse_args()

    game = TextAdventureGame(args.game_data_dir)
    game.start()
