import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Import helper for cross-environment compatibility
try:
    from util.import_helper import import_from
except ModuleNotFoundError:
    from src.util.import_helper import import_from


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
                r"^(save|load|help|map|settings|llm|options)\s*(.*)$", re.IGNORECASE
            ),
        }

    def setup_llm_provider(
        self, choice: int, config: dict = None, interactive: bool = True
    ) -> None:
        """
        Set up the LLM provider based on user choice.

        Args:
            choice: Integer representing the LLM provider choice (1-3)
            config: Optional dictionary with configuration parameters for the provider
            interactive: Whether to prompt for input if configuration is missing
        """
        # Initialize config if not provided
        if config is None:
            config = {}

        # Import required modules using the import helper
        LLMType = import_from("llm.providers.base", "LLMType")
        get_api_key = import_from("util.config", "get_api_key")
        load_environment_variables = import_from(
            "util.config", "load_environment_variables"
        )

        # Load environment variables from .env file
        load_environment_variables()

        if choice == 1:
            # OpenAI
            api_key = config.get("api_key")
            if not api_key:
                api_key = get_api_key("openai")
                if not api_key and interactive:
                    api_key = input("Enter OpenAI API key: ")

            # Use the model from config if provided, otherwise use default or prompt if interactive
            if "model" in config:
                model = config["model"]
            elif interactive:
                model = (
                    input("Enter model name (default: gpt-3.5-turbo): ")
                    or "gpt-3.5-turbo"
                )
            else:
                model = "gpt-3.5-turbo"
            self.llm_manager.add_provider(
                LLMType.OPENAI,
                self.llm_manager.create_provider(
                    LLMType.OPENAI, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.OPENAI)

        elif choice == 2:
            # Anthropic
            api_key = config.get("api_key")
            if not api_key:
                api_key = get_api_key("anthropic")
                if not api_key and interactive:
                    api_key = input("Enter Anthropic API key: ")

            # Use the model from config if provided, otherwise use default or prompt if interactive
            if "model" in config:
                model = config["model"]
            elif interactive:
                model = (
                    input("Enter model name (default: claude-3-haiku-20240307): ")
                    or "claude-3-haiku-20240307"
                )
            else:
                model = "claude-3-haiku-20240307"
            self.llm_manager.add_provider(
                LLMType.ANTHROPIC,
                self.llm_manager.create_provider(
                    LLMType.ANTHROPIC, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.ANTHROPIC)

        elif choice == 3:
            # Google
            api_key = config.get("api_key")
            if not api_key:
                api_key = get_api_key("google")
                if not api_key and interactive:
                    api_key = input("Enter Google API key: ")

            # Use the model from config if provided, otherwise use default or prompt if interactive
            if "model" in config:
                model = config["model"]
            elif interactive:
                model = (
                    input("Enter model name (default: gemini-1.5-flash): ")
                    or "gemini-1.5-flash"
                )
            else:
                model = "gemini-1.5-flash"
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

    def _process_map_movement(self, direction: str) -> Dict[str, Any]:
        """
        Process movement using the enhanced map system.

        Args:
            direction: The direction to move in

        Returns:
            Dictionary with the results of the movement
        """
        if not hasattr(self.graph_rag_engine, "map_integrator"):
            return {
                "success": False,
                "message": f"Cannot move {direction} - map system not available.",
                "action_type": CommandType.MOVEMENT.value,
            }

        print(f"Processing map movement: {direction}")
        # Get the current area and attempt to move
        success, new_area = self.graph_rag_engine.map_integrator.move_player(direction)

        if success and new_area:
            # Generate a response about the new area
            response = self.graph_rag_engine.generate_response(
                f"You moved {direction} to {new_area.name}", self.game_state
            )

            # Update the game state's location to match the new area's location
            self.game_state.player_location = new_area.location

            return {
                "success": True,
                "message": response,
                "action_type": CommandType.MOVEMENT.value,
                "new_location": new_area.name,
                "direction": direction,
            }
        else:
            return {
                "success": False,
                "message": f"You cannot go {direction} from here.",
                "action_type": CommandType.MOVEMENT.value,
            }

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a player command.

        Args:
            command: The player's command string

        Returns:
            Dictionary with the results of the command
        """
        # Import debug_print using the import helper
        debug_print = import_from("util.debug", "debug_print")

        debug_print(f"DEBUG: Processing command: '{command}'")

        # Special handling for direct commands
        command_lower = command.lower().strip()
        if command_lower == "map":
            debug_print("DEBUG: Detected map command directly")
            return self._process_system_command("map", "")
        elif command_lower == "local map":
            debug_print("DEBUG: Detected local map command directly")
            return self._process_system_command("map", "local")
        elif command_lower == "options":
            debug_print("DEBUG: Detected options command directly")
            return self._process_system_command("options", "")

        # Default result
        result = {
            "success": False,
            "message": "I don't understand that command.",
            "action_type": CommandType.UNKNOWN.value,
        }

        # Check if we're in combat
        if self.combat_system.active_combat:
            # Import debug_print using the import helper
            debug_print = import_from("util.debug", "debug_print")

            debug_print("DEBUG: In combat mode, processing as combat command")
            return self._process_combat_command(command)

        # SPECIAL HANDLING FOR DIRECTIONS FROM ENHANCED MAPS
        if hasattr(self.graph_rag_engine, "map_integrator"):
            current_area = self.graph_rag_engine.map_integrator.get_current_area()
            if current_area and any(
                cmd in command.lower() for cmd in ["go", "move", "walk"]
            ):
                # Extract direction from command
                parts = command.lower().split()
                if len(parts) > 1 and parts[0] in ["go", "move", "walk"]:
                    direction = parts[1]
                    # Check if it's a valid exit direction
                    if direction in current_area.exits:
                        print(f"✅ Detected direct map movement: {direction}")
                        # Skip intent resolution for direct map movements
                        return self._process_map_movement(direction)

        # For all other commands, try to resolve natural language intent
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

        if simple_command in ["map", "m"]:
            return CommandType.SYSTEM, "map", ""

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
            # First, check for named NPCs from the game state
            game_state_npcs = []
            try:
                # Try to extract NPCs that might be nearby in the game state
                context = self.game_state.get_current_context()
                if "npcs_present" in context:
                    game_state_npcs = list(context["npcs_present"].keys())
                print(f"DEBUG: Game state NPCs: {game_state_npcs}")
            except Exception as e:
                print(f"Error getting game state NPCs: {e}")

            # Check if the target matches one of the game state NPCs
            target_lower = target.lower()
            for npc in game_state_npcs:
                npc_lower = npc.lower()
                # Check for exact or partial name match
                if (
                    target_lower == npc_lower
                    or target_lower in npc_lower
                    or npc_lower in target_lower
                ):
                    print(f"DEBUG: Matched named character from game state: {npc}")
                    query = f"talk to {npc}"
                    response = self.graph_rag_engine.generate_response(
                        query, self.game_state
                    )
                    return {
                        "success": True,
                        "message": response,
                        "action_type": CommandType.INTERACTION.value,
                        "target": npc,
                    }

            # Check if we have a map area with NPCs
            map_npc_found = False
            if hasattr(self.graph_rag_engine, "map_integrator"):
                current_area = self.graph_rag_engine.map_integrator.get_current_area()
                if current_area and current_area.npcs:
                    print(f"DEBUG: Current area has NPCs: {current_area.npcs}")

                    # Try to match target with NPCs in the area
                    for npc in current_area.npcs:
                        npc_lower = npc.lower()
                        # Check if the NPC name contains the target or vice versa
                        if target_lower in npc_lower or any(
                            word in npc_lower for word in target_lower.split()
                        ):
                            print(f"DEBUG: Found matching NPC in map area: {npc}")
                            map_npc_found = True
                            query = f"talk to {npc} in {current_area.name}"
                            response = self.graph_rag_engine.generate_response(
                                query, self.game_state
                            )
                            return {
                                "success": True,
                                "message": response,
                                "action_type": CommandType.INTERACTION.value,
                                "target": npc,
                                "original_target": target,
                            }

            # Standard NPC handling via game state as fallback
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

            # Try with just the last word, which is likely the actual name
            words = target.split()
            if len(words) > 1:
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

            # Check if the target appears in any NPC names (partial matches)
            partial_match = None
            for npc in game_state_npcs:
                npc_parts = npc.lower().split()
                for part in npc_parts:
                    if part in target_lower or target_lower in part:
                        partial_match = npc
                        break
                if partial_match:
                    break

            # If we found a partial match, use it
            if partial_match:
                print(
                    f"DEBUG: Found partial match with game state NPC: {partial_match}"
                )
                query = f"talk to {partial_match}"
                response = self.graph_rag_engine.generate_response(
                    query, self.game_state
                )
                return {
                    "success": True,
                    "message": response,
                    "action_type": CommandType.INTERACTION.value,
                    "target": partial_match,
                    "original_target": target,
                }

            # Check one last time with generic terms
            if hasattr(self.graph_rag_engine, "map_integrator"):
                current_area = self.graph_rag_engine.map_integrator.get_current_area()
                if current_area and current_area.npcs:
                    generic_terms = ["guide", "hermit", "merchant", "traveler", "guard"]
                    for term in generic_terms:
                        if term in target_lower:
                            for npc in current_area.npcs:
                                if term in npc.lower():
                                    query = f"talk to {npc} in {current_area.name}"
                                    response = self.graph_rag_engine.generate_response(
                                        query, self.game_state
                                    )
                                    return {
                                        "success": True,
                                        "message": response,
                                        "action_type": CommandType.INTERACTION.value,
                                        "target": npc,
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

        elif action == "help" or action == "options":
            # Display help
            help_text = """
Available Commands:
------------------
Movement: go [location], move [location], walk [location]
Look: look, examine [object/person]
Interaction: talk [character], take [item], use [item]
Inventory: inventory, equip [item]
Combat: attack [enemy], stats, block, dodge, flee
System: save [filename], load [filename], help, options, quit

Special Commands:
----------------
options - Show available directions, NPCs, and actions in current area
quit - Exit the game
            """

            # If command is "options", add additional context-specific information
            if action == "options":
                # Get current context information
                context = self.game_state.get_current_context()
                current_location = context.get("current_location", {})
                npcs_present = context.get("npcs_present", {})

                # Check if we have an enhanced GraphRAG engine with map support
                map_info = ""
                print("\n⭐⭐⭐ DEBUGGING MAP OPTIONS ⭐⭐⭐")
                print("Checking for map_integrator...")

                # Explicitly check if enhanced engine is being used
                engine_class = self.graph_rag_engine.__class__.__name__
                print(f"GraphRAG Engine Class: {engine_class}")

                if hasattr(self.graph_rag_engine, "map_integrator"):
                    print("✅ Found map_integrator in graph_rag_engine")
                    current_area = (
                        self.graph_rag_engine.map_integrator.get_current_area()
                    )

                    if current_area:
                        print(
                            f"✅ Found current area: {current_area.name} in {current_area.location}"
                        )
                        print(f"✅ Area exits: {list(current_area.exits.keys())}")

                        # Set map_info content with very visible formatting
                        map_info = (
                            "\n\n============ AVAILABLE MAP DIRECTIONS ============\n"
                        )

                        # Add area information
                        if current_area.sub_location:
                            map_info += f"Current Area: {current_area.name}\n"
                            map_info += f"Sub-Location: {current_area.sub_location}\n\n"
                        else:
                            map_info += f"Current Area: {current_area.name}\n\n"

                        # Add directions with clear formatting
                        if current_area.exits:
                            map_info += "You can go in these directions:\n"
                            for direction, target_id in current_area.exits.items():
                                map_info += f"  > {direction.upper()}\n"
                            map_info += "\n"

                        # Add items
                        if current_area.items:
                            map_info += "Items you can see here:\n"
                            for item in current_area.items:
                                map_info += f"  * {item}\n"
                            map_info += "\n"

                        # Make sure this is very visible
                        map_info += "============================================\n"

                        print(f"✅ Generated map_info:\n{map_info}")
                    else:
                        print("❌ Failed to get current area from map_integrator")
                else:
                    print("❌ No map_integrator found in graph_rag_engine")

                # Standard options for all versions
                options_text = (
                    f"\nCurrent Location: {self.game_state.player_location}\n"
                )

                # Add available exits
                available_exits = current_location.get("connected_locations", [])
                if available_exits:
                    options_text += "\nConnected Locations:\n"
                    for location in available_exits:
                        options_text += f"  {location}\n"

                # Add NPCs
                if npcs_present:
                    options_text += "\nCharacters Present:\n"
                    for npc in npcs_present.keys():
                        options_text += f"  {npc}\n"

                # Add enhanced map info if available - VERY IMPORTANT!
                if map_info:
                    print("📋 Adding map_info to options_text")
                    options_text += map_info
                else:
                    print("⚠️ No map_info to add to options")

                # Add inventory
                if self.game_state.inventory:
                    options_text += "\nInventory:\n"
                    for item in self.game_state.inventory:
                        options_text += f"  {item}\n"

                # Add options_text to help_text
                print(f"📝 Final options_text length: {len(options_text)}")
                print(f"📝 First 100 chars of options_text: {options_text[:100]}")
                print(f"📝 Adding options_text to help_text")
                help_text += options_text

            return {
                "success": True,
                "message": help_text,
                "action_type": CommandType.SYSTEM.value,
                "help_displayed": True,
            }

        # Map command removed - visualization library dependencies were removed

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
            provider_id = int(input("Enter new LLM provider (1-3): "))
            self.setup_llm_provider(provider_id, interactive=True)
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
