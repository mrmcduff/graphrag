import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class CommandType(Enum):
    """Types of commands the player can input."""

    MOVEMENT = "movement"
    INTERACTION = "interaction"
    INVENTORY = "inventory"
    COMBAT = "combat"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class CommandProcessor:
    """Process and execute player commands."""

    def __init__(self, game_state, graph_rag_engine, combat_system, llm_manager):
        """
        Initialize the command processor.

        Args:
            game_state: The current game state
            graph_rag_engine: The GraphRAG engine
            combat_system: The combat system
            llm_manager: The LLM manager
        """
        self.game_state = game_state
        self.graph_rag_engine = graph_rag_engine
        self.combat_system = combat_system
        self.llm_manager = llm_manager
        
        # Initialize the intent resolver for natural language processing
        from .intent_resolver import IntentResolver
        self.intent_resolver = IntentResolver(llm_manager)

        # Command patterns - regular expressions to match different command types
        self.command_patterns = {
            CommandType.MOVEMENT: re.compile(
                r"^(go|move|travel|walk)\s+(.+)$", re.IGNORECASE
            ),
            CommandType.INTERACTION: re.compile(
                r"^(look|examine|talk|speak|take|get|use)\s*(.*)$", re.IGNORECASE
            ),
            CommandType.INVENTORY: re.compile(
                r"^(inventory|items|i|equip)\s*(.*)$", re.IGNORECASE
            ),
            CommandType.COMBAT: re.compile(
                r"^(attack|fight|stats|block|dodge|flee)\s*(.*)$", re.IGNORECASE
            ),
            CommandType.SYSTEM: re.compile(
                r"^(save|load|help|map|settings|llm)\s*(.*)$", re.IGNORECASE
            ),
        }

    def setup_llm_provider(self, choice: int) -> None:
        """
        Set up the LLM provider based on user choice.

        Args:
            choice: Integer representing the LLM provider choice (1-6)
        """
        from llm.providers.base import LLMType
        from util.config import get_api_key, load_environment_variables

        # Load environment variables from .env file
        load_environment_variables()

        if choice == 1:
            # Local API
            host = input("Enter host (default: localhost): ") or "localhost"
            port = input("Enter port (default: 8000): ") or "8000"
            self.llm_manager.add_provider(
                LLMType.LOCAL_API,
                self.llm_manager.create_provider(
                    LLMType.LOCAL_API, host=host, port=int(port)
                ),
            )
            self.llm_manager.set_active_provider(LLMType.LOCAL_API)

        elif choice == 2:
            # Local direct
            model_path = input("Enter model path: ")
            self.llm_manager.add_provider(
                LLMType.LOCAL_DIRECT,
                self.llm_manager.create_provider(
                    LLMType.LOCAL_DIRECT, model_path=model_path
                ),
            )
            self.llm_manager.set_active_provider(LLMType.LOCAL_DIRECT)

        elif choice == 3:
            # OpenAI
            api_key = get_api_key("openai")
            if not api_key:
                api_key = input("Enter OpenAI API key: ")
            model = (
                input("Enter model name (default: gpt-3.5-turbo): ") or "gpt-3.5-turbo"
            )
            self.llm_manager.add_provider(
                LLMType.OPENAI,
                self.llm_manager.create_provider(
                    LLMType.OPENAI, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.OPENAI)

        elif choice == 4:
            # Anthropic
            api_key = get_api_key("anthropic")
            if not api_key:
                api_key = input("Enter Anthropic API key: ")
            model = (
                input("Enter model name (default: claude-3-haiku-20240307): ")
                or "claude-3-haiku-20240307"
            )
            self.llm_manager.add_provider(
                LLMType.ANTHROPIC,
                self.llm_manager.create_provider(
                    LLMType.ANTHROPIC, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.ANTHROPIC)

        elif choice == 5:
            # Google
            api_key = get_api_key("google")
            if not api_key:
                api_key = input("Enter Google API key: ")
            model = input("Enter model name (default: gemini-pro): ") or "gemini-pro"
            self.llm_manager.add_provider(
                LLMType.GOOGLE,
                self.llm_manager.create_provider(
                    LLMType.GOOGLE, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.GOOGLE)

        else:
            # Rule-based (fallback)
            self.llm_manager.add_provider(
                LLMType.RULE_BASED, self.llm_manager.create_provider(LLMType.RULE_BASED)
            )
            self.llm_manager.set_active_provider(LLMType.RULE_BASED)

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a player command.

        Args:
            command: The player's command string

        Returns:
            Dictionary with the results of the command
        """
        # Default result
        result = {
            "success": False,
            "message": "I don't understand that command.",
            "action_type": CommandType.UNKNOWN.value,
        }

        # Check if we're in combat
        if self.combat_system.active_combat:
            return self._process_combat_command(command)
            
        # First, try to resolve the natural language intent
        original_command = command
        resolved_command = self.intent_resolver.resolve_intent(command, self.game_state)
        
        # If the resolved command is different from the original, use it
        if resolved_command != original_command:
            print(f"Resolved '{original_command}' to '{resolved_command}'")
            command = resolved_command
            
            # Store the original and resolved commands for reference
            result["original_input"] = original_command
            result["resolved_command"] = resolved_command
            
            # Add a debug flag to help diagnose command parsing issues
            result["intent_resolved"] = True

        # Try to match command against patterns
        command_type, action, target = self._parse_command(command)

        # Process based on command type
        if command_type == CommandType.MOVEMENT:
            result = self._process_movement(action, target)

        elif command_type == CommandType.INTERACTION:
            result = self._process_interaction(action, target)

        elif command_type == CommandType.INVENTORY:
            result = self._process_inventory(action, target)

        elif command_type == CommandType.COMBAT:
            result = self._process_combat_initiation(action, target)

        elif command_type == CommandType.SYSTEM:
            result = self._process_system_command(action, target)

        else:
            # Use the GraphRAG engine for unknown commands
            response = self.graph_rag_engine.generate_response(command, self.game_state)
            result = {"success": True, "message": response, "action_type": "narrative"}

        # Update game turn only if action was successful
        if result.get("success", False):
            self.game_state.game_turn += 1

        return result

    def _parse_command(self, command: str) -> Tuple[CommandType, str, str]:
        """
        Parse the command to determine type, action, and target.

        Args:
            command: The player's command string

        Returns:
            Tuple of (command_type, action, target)
        """
        # Try to match against patterns
        for cmd_type, pattern in self.command_patterns.items():
            match = pattern.match(command)
            if match:
                action = match.group(1).lower()
                target = match.group(2).strip() if match.group(2) else ""
                return cmd_type, action, target

        # If no match, check for simple commands
        simple_command = command.lower().strip()

        if simple_command in ["look", "l"]:
            return CommandType.INTERACTION, "look", ""

        if simple_command in ["inventory", "i"]:
            return CommandType.INVENTORY, "inventory", ""

        if simple_command in ["help", "h", "?"]:
            return CommandType.SYSTEM, "help", ""

        # No match found - treat as unknown
        words = simple_command.split()
        action = words[0] if words else ""
        target = " ".join(words[1:]) if len(words) > 1 else ""

        return CommandType.UNKNOWN, action, target

    def _process_movement(self, action: str, target: str) -> Dict[str, Any]:
        """
        Process movement commands.

        Args:
            action: The movement action (go, move, etc.)
            target: The destination location

        Returns:
            Dictionary with the results of the movement
        """
        if not target:
            return {
                "success": False,
                "message": "Where do you want to go?",
                "action_type": CommandType.MOVEMENT.value,
            }

        # Try to move to the target location
        success = self.game_state.update_state(action, target)

        if success:
            # Just set basic info - the actual description will be handled by the game loop
            return {
                "success": True,
                "message": f"You travel to {target}.",
                "action_type": CommandType.MOVEMENT.value,
                "location": self.game_state.player_location,
            }
        else:
            return {
                "success": False,
                "message": f"You can't go to {target} from here.",
                "action_type": CommandType.MOVEMENT.value,
            }

    def _process_interaction(self, action: str, target: str) -> Dict[str, Any]:
        """
        Process interaction commands (look, talk, take, use).

        Args:
            action: The interaction action
            target: The target of the interaction

        Returns:
            Dictionary with the results of the interaction
        """
        if action == "look" and not target:
            # Look around the current location
            description = self.graph_rag_engine.generate_response(
                "look around", self.game_state
            )
            return {
                "success": True,
                "message": description,
                "action_type": CommandType.INTERACTION.value,
            }

        elif action in ["talk", "speak"] and target:
            # Talk to an NPC
            success = self.game_state.update_state(action, target)
            if success:
                query = f"talk to {target}"
                response = self.graph_rag_engine.generate_response(
                    query, self.game_state
                )
                return {
                    "success": True,
                    "message": response,
                    "action_type": CommandType.INTERACTION.value,
                    "target": target,
                }
            else:
                # Check if the target might contain prepositions that weren't properly removed
                words = target.split()
                if len(words) > 1:
                    # Try with just the last word, which is likely the actual name
                    potential_name = words[-1]
                    success = self.game_state.update_state(action, potential_name)
                    if success:
                        query = f"talk to {potential_name}"
                        response = self.graph_rag_engine.generate_response(
                            query, self.game_state
                        )
                        return {
                            "success": True,
                            "message": response,
                            "action_type": CommandType.INTERACTION.value,
                            "target": potential_name,
                            "original_target": target,
                        }
                
                return {
                    "success": False,
                    "message": f"There's no one named {target} here.",
                    "action_type": CommandType.INTERACTION.value,
                }

        elif action in ["take", "get"] and target:
            # Take an item
            success = self.game_state.update_state(action, target)
            if success:
                return {
                    "success": True,
                    "message": f"You take the {target} and add it to your inventory.",
                    "action_type": CommandType.INTERACTION.value,
                    "target": target,
                }
            else:
                return {
                    "success": False,
                    "message": f"There's no {target} here that you can take.",
                    "action_type": CommandType.INTERACTION.value,
                }

        elif action == "use" and target:
            # Use an item
            if target in self.game_state.inventory:
                success = self.game_state.update_state(action, target)
                if success:
                    response = self.graph_rag_engine.generate_response(
                        f"use {target}", self.game_state
                    )
                    return {
                        "success": True,
                        "message": response,
                        "action_type": CommandType.INTERACTION.value,
                        "target": target,
                    }

            return {
                "success": False,
                "message": f"You don't have {target} in your inventory.",
                "action_type": CommandType.INTERACTION.value,
            }

        elif action in ["examine", "inspect"] and target:
            # Examine something specific
            response = self.graph_rag_engine.generate_response(
                f"examine {target}", self.game_state
            )
            return {
                "success": True,
                "message": response,
                "action_type": CommandType.INTERACTION.value,
                "target": target,
            }

        # Default response for other interactions
        query = f"{action} {target}".strip()
        response = self.graph_rag_engine.generate_response(query, self.game_state)
        return {
            "success": True,
            "message": response,
            "action_type": CommandType.INTERACTION.value,
        }

    def _process_inventory(self, action: str, target: str) -> Dict[str, Any]:
        """
        Process inventory-related commands.

        Args:
            action: The inventory action
            target: The target item

        Returns:
            Dictionary with the results of the inventory action
        """
        if action in ["inventory", "items", "i"] and not target:
            # Display inventory
            if not self.game_state.inventory:
                return {
                    "success": True,
                    "message": "Your inventory is empty.",
                    "action_type": CommandType.INVENTORY.value,
                }

            items = ", ".join(self.game_state.inventory)
            return {
                "success": True,
                "message": f"Inventory: {items}",
                "action_type": CommandType.INVENTORY.value,
                "inventory": self.game_state.inventory,
            }

        elif action == "equip" and target:
            # Equip an item
            if target not in self.game_state.inventory:
                return {
                    "success": False,
                    "message": f"You don't have {target} in your inventory.",
                    "action_type": CommandType.INVENTORY.value,
                }

            # Check if it's a weapon or armor
            is_weapon = target in self.combat_system.weapon_database
            is_armor = target in self.combat_system.armor_database

            if is_weapon:
                self.combat_system.player_stats["equipped_weapon"] = target
                return {
                    "success": True,
                    "message": f"You equip the {target}.",
                    "action_type": CommandType.INVENTORY.value,
                    "equipped": target,
                    "slot": "weapon",
                }
            elif is_armor:
                self.combat_system.player_stats["equipped_armor"] = target
                return {
                    "success": True,
                    "message": f"You equip the {target}.",
                    "action_type": CommandType.INVENTORY.value,
                    "equipped": target,
                    "slot": "armor",
                }
            else:
                return {
                    "success": False,
                    "message": f"You can't equip {target}.",
                    "action_type": CommandType.INVENTORY.value,
                }

        # Default response
        return {
            "success": False,
            "message": "Invalid inventory command.",
            "action_type": CommandType.INVENTORY.value,
        }

    def _process_combat_initiation(self, action: str, target: str) -> Dict[str, Any]:
        """
        Process commands that initiate combat.

        Args:
            action: The combat action
            target: The combat target

        Returns:
            Dictionary with the results of the combat initiation
        """
        if action in ["attack", "fight"] and target:
            # Start combat with the target
            combat_started = self.combat_system.start_combat(target)

            if combat_started:
                enemy_name = self.combat_system.active_combat["enemy"]["name"]
                return {
                    "success": True,
                    "message": f"You engage in combat with {enemy_name}!",
                    "action_type": CommandType.COMBAT.value,
                    "combat_started": True,
                    "enemy": enemy_name,
                }
            else:
                return {
                    "success": False,
                    "message": f"You can't attack {target}.",
                    "action_type": CommandType.COMBAT.value,
                }

        elif action == "stats":
            # Display player stats
            stats = self.combat_system.player_stats
            weapon = stats.get("equipped_weapon", "None")
            armor = stats.get("equipped_armor", "None")

            stats_message = (
                f"Player Stats:\n"
                f"Health: {stats['health']}/{stats['max_health']}\n"
                f"Strength: {stats['strength']}\n"
                f"Dexterity: {stats['dexterity']}\n"
                f"Intelligence: {stats['intelligence']}\n"
                f"Defense: {stats['defense']}\n"
                f"Equipped Weapon: {weapon}\n"
                f"Equipped Armor: {armor}"
            )

            return {
                "success": True,
                "message": stats_message,
                "action_type": CommandType.COMBAT.value,
                "stats": stats,
            }

        # Default response
        return {
            "success": False,
            "message": "Invalid combat command.",
            "action_type": CommandType.COMBAT.value,
        }

    def _process_combat_command(self, command: str) -> Dict[str, Any]:
        """
        Process commands during active combat.

        Args:
            command: The combat command

        Returns:
            Dictionary with the results of the combat action
        """
        words = command.lower().split()
        action = words[0] if words else ""
        target = " ".join(words[1:]) if len(words) > 1 else ""

        if action in ["attack", "block", "dodge"]:
            # Basic combat actions
            result = self.combat_system.process_combat_action(action, target)

            if result["success"]:
                # Format the combat log for display
                log_entries = result["combat_log"]
                combat_message = "\n".join(log_entries)

                # Check if combat has ended
                is_active = result["combat_status"] == "active"

                # Determine combat result if combat has ended
                combat_result = None
                if not is_active:
                    if result["combat_status"] == "player_victory":
                        combat_result = "victory"
                    elif result["combat_status"] == "player_defeated":
                        combat_result = "defeat"
                    elif result["combat_status"] == "player_fled":
                        combat_result = "fled"

                return {
                    "success": True,
                    "message": combat_message,
                    "action_type": CommandType.COMBAT.value,
                    "combat_active": is_active,
                    "combat_result": combat_result,
                    "player_health": result["player_health"],
                    "enemy_health": result["enemy_health"],
                }
            else:
                return {
                    "success": False,
                    "message": result["message"],
                    "action_type": CommandType.COMBAT.value,
                }

        elif action == "use" and target:
            # Use an item in combat
            if target in self.game_state.inventory:
                result = self.combat_system.process_combat_action(action, target)

                if result["success"]:
                    log_entries = result["combat_log"]
                    combat_message = "\n".join(log_entries)

                    return {
                        "success": True,
                        "message": combat_message,
                        "action_type": CommandType.COMBAT.value,
                        "combat_active": result["combat_status"] == "active",
                        "item_used": target,
                    }
                else:
                    return {
                        "success": False,
                        "message": result["message"],
                        "action_type": CommandType.COMBAT.value,
                    }
            else:
                return {
                    "success": False,
                    "message": f"You don't have {target} in your inventory.",
                    "action_type": CommandType.COMBAT.value,
                }

        elif action == "flee":
            # Attempt to flee from combat
            # 50% chance of success
            import random

            success = random.random() > 0.5

            if success:
                self.combat_system.active_combat["status"] = "player_fled"
                self.combat_system.active_combat = None
                return {
                    "success": True,
                    "message": "You successfully flee from combat!",
                    "action_type": CommandType.COMBAT.value,
                    "combat_active": False,
                    "combat_result": "fled",
                }
            else:
                # Failed to flee, enemy gets a free attack
                enemy_action = self.combat_system._process_enemy_combat_action()
                return {
                    "success": False,
                    "message": f"You fail to escape! {enemy_action.get('message', 'The enemy attacks you!')}",
                    "action_type": CommandType.COMBAT.value,
                    "combat_active": True,
                }

        # Default response
        return {
            "success": False,
            "message": "Invalid combat command. You can 'attack', 'block', 'dodge', 'use [item]', or 'flee'.",
            "action_type": CommandType.COMBAT.value,
        }

    def _process_system_command(self, action: str, target: str) -> Dict[str, Any]:
        """
        Process system commands.

        Args:
            action: The system action
            target: The target of the system action

        Returns:
            Dictionary with the results of the system command
        """
        if action == "save":
            # Save the game
            save_file = target if target else "save.json"
            success = self.game_state.save_game(save_file)

            if success:
                return {
                    "success": True,
                    "message": f"Game saved to {save_file}.",
                    "action_type": CommandType.SYSTEM.value,
                    "save_file": save_file,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to save game to {save_file}.",
                    "action_type": CommandType.SYSTEM.value,
                }

        elif action == "load":
            # Load a saved game
            load_file = target if target else "save.json"
            success = self.game_state.load_game(load_file)

            if success:
                return {
                    "success": True,
                    "message": f"Game loaded from {load_file}.",
                    "action_type": CommandType.SYSTEM.value,
                    "load_file": load_file,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to load game from {load_file}.",
                    "action_type": CommandType.SYSTEM.value,
                }

        elif action == "help":
            # Display help
            help_text = """
Available Commands:
------------------
Movement: go [location], move [location], walk [location]
Look: look, examine [object/person]
Interaction: talk [character], take [item], use [item]
Inventory: inventory, equip [item]
Combat: attack [enemy], stats, block, dodge, flee
System: save [filename], load [filename], help, map, quit

Special Commands:
----------------
map - Show the world map
local map - Show detailed map of current location
quit - Exit the game
            """

            return {
                "success": True,
                "message": help_text,
                "action_type": CommandType.SYSTEM.value,
                "help_displayed": True,
            }

        elif action == "map":
            # Show map
            if target and target.lower() == "local":
                return {
                    "success": True,
                    "message": f"Displaying local map of {self.game_state.player_location}...",
                    "action_type": CommandType.SYSTEM.value,
                    "map_type": "local",
                    "location": self.game_state.player_location,
                    "display_map": True,
                }
            else:
                return {
                    "success": True,
                    "message": "Displaying world map...",
                    "action_type": CommandType.SYSTEM.value,
                    "map_type": "world",
                    "locations": list(self.game_state.visited_locations),
                    "display_map": True,
                }

        elif action == "llm" and target == "info":
            # Display LLM information
            provider = self.llm_manager.active_provider
            provider_name = provider.name if provider else "None"

            return {
                "success": True,
                "message": f"Current LLM provider: {provider_name}",
                "action_type": CommandType.SYSTEM.value,
                "llm_info": True,
            }

        elif action == "llm" and target == "change":
            # Change LLM provider
            self.setup_llm_provider(int(input("Enter new LLM provider (1-6): ")))
            provider = self.llm_manager.active_provider
            provider_name = provider.name if provider else "None"

            return {
                "success": True,
                "message": f"LLM provider changed to {provider_name}.",
                "action_type": CommandType.SYSTEM.value,
                "llm_changed": True,
            }

        # Default response
        return {
            "success": False,
            "message": "Unknown system command. Try 'help' for a list of commands.",
            "action_type": CommandType.SYSTEM.value,
        }
