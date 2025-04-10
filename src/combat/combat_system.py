import random
import math
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import json
import os


class CombatStatus(Enum):
    """Enum for the status of a combat encounter."""

    ACTIVE = "active"
    PLAYER_VICTORY = "player_victory"
    PLAYER_DEFEATED = "player_defeated"
    PLAYER_FLED = "player_fled"
    ENDED = "ended"  # Generic ended state (e.g., through dialogue/surrender)


class AttackType(Enum):
    """Types of attacks available in combat."""

    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"
    SPECIAL = "special"


class StatusEffect(Enum):
    """Status effects that can be applied during combat."""

    NONE = "none"
    POISONED = "poisoned"
    STUNNED = "stunned"
    WEAKENED = "weakened"
    PROTECTED = "protected"
    ENRAGED = "enraged"
    BLESSED = "blessed"
    CURSED = "cursed"


class CombatSystem:
    """Class to handle combat mechanics in the game."""

    def __init__(self, game_state_data, game_state=None, graph=None, relations_df=None):
        """
        Initialize the combat system.

        Args:
            game_state_data: The current game state data
            game_state: The full game state object (for backward compatibility)
            graph: The knowledge graph (optional)
            relations_df: The relations dataframe (optional)
        """
        self.game_state_data = game_state_data
        self.game_state = game_state  # Keep for backward compatibility
        self.graph = graph
        self.relations_df = relations_df

        # If graph is not provided, try to get it from game_state_data or game_state
        if self.graph is None:
            if hasattr(game_state_data, "graph"):
                self.graph = game_state_data.graph
            elif game_state is not None and hasattr(game_state, "graph"):
                self.graph = game_state.graph

        # If relations_df is not provided, try to get it from game_state_data or game_state
        if self.relations_df is None:
            if hasattr(game_state_data, "relations_df"):
                self.relations_df = game_state_data.relations_df
            elif game_state is not None and hasattr(game_state, "relations_df"):
                self.relations_df = game_state.relations_df

        self.active_combat = None
        self.player_stats = self._initialize_player_stats()
        self.enemy_database = self._load_enemy_database()
        self.weapon_database = self._load_weapon_database()
        self.armor_database = self._load_armor_database()

        # Combat-specific knowledge derived from the graph
        self.weakness_map = self._derive_weakness_map()
        self.environment_effects = self._derive_environment_effects()

    def _initialize_player_stats(self) -> Dict[str, Any]:
        """
        Initialize player combat stats based on game_state_data if available,
        otherwise use default values.
        """
        # Default player stats
        default_stats = {
            "health": 100,
            "max_health": 100,
            "stamina": 100,
            "max_stamina": 100,
            "mana": 50,
            "max_mana": 50,
            "strength": 10,
            "dexterity": 10,
            "intelligence": 10,
            "defense": 5,
            "evasion": 10,
            "critical_chance": 5,  # Percentage
            "level": 1,
            "experience": 0,
            "equipped_weapon": None,
            "equipped_armor": None,
            "status_effects": [],
            "abilities": ["strike", "block", "dodge"],
        }

        # Try to get player stats from game_state_data if available
        if hasattr(self.game_state_data, "player_stats"):
            # Update default stats with values from game_state_data
            for key, value in self.game_state_data.player_stats.items():
                if key in default_stats:
                    default_stats[key] = value

        return default_stats

    def _load_enemy_database(self) -> Dict[str, Dict[str, Any]]:
        """
        Load enemy data from files or initialize defaults based on graph entities.

        Returns:
            Dictionary of enemy data
        """
        # Get game_data_dir from game_state_data or game_state
        game_data_dir = None
        if hasattr(self.game_state_data, "game_data_dir"):
            game_data_dir = self.game_state_data.game_data_dir
        elif self.game_state is not None and hasattr(self.game_state, "game_data_dir"):
            game_data_dir = self.game_state.game_data_dir

        # Try to load from file first
        if game_data_dir:
            try:
                enemy_file = os.path.join(game_data_dir, "game_enemies.json")
                if os.path.exists(enemy_file):
                    with open(enemy_file, "r") as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading enemy database: {e}")

        # If file loading fails, derive from entities graph
        enemies = {}

        # Extract PERSON entities that could be combatants
        characters = self.game_state_data.characters
        for character in characters:
            char_lower = character.lower()
            character_id = char_lower.replace(" ", "_")

            # Check character relations to identify potential enemies
            is_potential_enemy = False
            aggressive_relations = ["hates", "hunts", "attacks", "enemy_of"]

            # Check relations in the graph
            if self.graph and character_id in self.graph.nodes:
                for neighbor in self.graph.neighbors(character_id):
                    edge_data = self.graph.get_edge_data(character_id, neighbor)
                    if edge_data and "relation" in edge_data:
                        if edge_data["relation"].lower() in aggressive_relations:
                            is_potential_enemy = True
                            break

            # Set enemy type based on name patterns (simple heuristic)
            enemy_type = "humanoid"
            for type_name, keywords in [
                ("beast", ["wolf", "bear", "lion", "tiger", "beast"]),
                ("undead", ["zombie", "skeleton", "ghost", "undead", "vampire"]),
                ("magical", ["wizard", "mage", "witch", "sorcerer", "warlock"]),
                ("monster", ["troll", "ogre", "goblin", "orc", "monster"]),
                ("elemental", ["elemental", "fire", "water", "earth", "air"]),
            ]:
                if any(keyword in char_lower for keyword in keywords):
                    enemy_type = type_name
                    is_potential_enemy = True
                    break

            # Only add as enemy if they seem like one
            if is_potential_enemy:
                # Scale stats based on character name length (just a simple heuristic)
                name_power = len(character) % 5 + 1

                enemies[character] = {
                    "name": character,
                    "type": enemy_type,
                    "level": random.randint(1, 5),
                    "health": 50 + name_power * 10,
                    "max_health": 50 + name_power * 10,
                    "attack": 5 + name_power,
                    "defense": 3 + name_power // 2,
                    "evasion": 5 + name_power // 3,
                    "abilities": ["strike"],
                    "drops": [],
                    "experience_value": 20 + name_power * 5,
                    "description": f"A hostile {enemy_type}.",
                }

                # Add special abilities based on type
                if enemy_type == "magical":
                    enemies[character]["abilities"].append("fireball")
                    enemies[character]["mana"] = 30
                    enemies[character]["max_mana"] = 30
                elif enemy_type == "beast":
                    enemies[character]["abilities"].append("claw")
                    enemies[character]["abilities"].append("bite")
                elif enemy_type == "undead":
                    enemies[character]["abilities"].append("drain_life")
                    enemies[character]["resistance"] = ["poison"]
                elif enemy_type == "monster":
                    enemies[character]["abilities"].append("smash")
                    enemies[character]["strength"] = 15

        return enemies

    def _load_weapon_database(self) -> Dict[str, Dict[str, Any]]:
        """
        Load weapon data from files or initialize defaults based on graph entities.

        Returns:
            Dictionary of weapon data
        """
        # Get game_data_dir from game_state_data or game_state
        game_data_dir = None
        if hasattr(self.game_state_data, "game_data_dir"):
            game_data_dir = self.game_state_data.game_data_dir
        elif self.game_state is not None and hasattr(self.game_state, "game_data_dir"):
            game_data_dir = self.game_state.game_data_dir

        # Try to load from file first
        if game_data_dir:
            try:
                weapon_file = os.path.join(game_data_dir, "game_weapons.json")
                if os.path.exists(weapon_file):
                    with open(weapon_file, "r") as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading weapon database: {e}")

        # If file loading fails, derive from items in graph
        weapons = {}

        # Find items that could be weapons based on name
        weapon_keywords = [
            "sword",
            "axe",
            "bow",
            "staff",
            "wand",
            "dagger",
            "mace",
            "spear",
            "knife",
            "hammer",
            "blade",
        ]

        # Get items from game_state_data or fall back to game_state
        items = []
        if hasattr(self.game_state_data, "items"):
            items = self.game_state_data.items
        elif self.game_state is not None and hasattr(self.game_state, "items"):
            items = self.game_state.items

        for item in items:
            item_lower = item.lower()

            # Check if item name contains weapon keywords
            is_weapon = any(keyword in item_lower for keyword in weapon_keywords)

            if is_weapon:
                # Determine weapon type
                weapon_type = "sword"  # Default
                attack_type = AttackType.MELEE

                if "bow" in item_lower or "arrow" in item_lower:
                    weapon_type = "bow"
                    attack_type = AttackType.RANGED
                elif "staff" in item_lower or "wand" in item_lower:
                    weapon_type = "staff"
                    attack_type = AttackType.MAGIC
                elif "dagger" in item_lower or "knife" in item_lower:
                    weapon_type = "dagger"
                elif "axe" in item_lower:
                    weapon_type = "axe"
                elif "hammer" in item_lower or "mace" in item_lower:
                    weapon_type = "hammer"
                elif "spear" in item_lower:
                    weapon_type = "spear"

                # Generate weapon properties based on name
                name_power = len(item) % 5 + 1

                # Check for magical qualities
                has_magic = any(
                    word in item_lower
                    for word in [
                        "magic",
                        "enchanted",
                        "ancient",
                        "mystic",
                        "legendary",
                        "cursed",
                        "blessed",
                    ]
                )
                elemental_type = None

                for element, keywords in [
                    ("fire", ["fire", "flame", "burning"]),
                    ("ice", ["ice", "frost", "freezing"]),
                    ("lightning", ["lightning", "thunder", "storm"]),
                    ("poison", ["poison", "venom", "toxic"]),
                    ("holy", ["holy", "sacred", "divine"]),
                    ("dark", ["dark", "shadow", "void"]),
                ]:
                    if any(keyword in item_lower for keyword in keywords):
                        elemental_type = element
                        has_magic = True
                        break

                # Create weapon entry
                weapons[item] = {
                    "name": item,
                    "type": weapon_type,
                    "attack_type": attack_type.value,
                    "damage": 5 + name_power * 2 + (5 if has_magic else 0),
                    "critical_bonus": 5 + (10 if "dagger" in item_lower else 0),
                    "magical": has_magic,
                    "elemental_type": elemental_type,
                    "durability": 100,
                    "abilities": [],
                    "requirements": {"level": 1},
                }

                # Add special abilities based on weapon properties
                if has_magic and elemental_type:
                    weapons[item]["abilities"].append(f"{elemental_type}_damage")

                if "legendary" in item_lower or "ancient" in item_lower:
                    weapons[item]["abilities"].append("special_attack")
                    weapons[item]["requirements"]["level"] = 3

                if weapon_type == "bow":
                    weapons[item]["abilities"].append("aimed_shot")
                elif weapon_type == "staff" and has_magic:
                    weapons[item]["abilities"].append("magic_bolt")
                elif weapon_type == "dagger":
                    weapons[item]["abilities"].append("backstab")

        return weapons

    def _load_armor_database(self) -> Dict[str, Dict[str, Any]]:
        """
        Load armor data from files or initialize defaults based on graph entities.

        Returns:
            Dictionary of armor data
        """
        # Get game_data_dir from game_state_data or game_state
        game_data_dir = None
        if hasattr(self.game_state_data, "game_data_dir"):
            game_data_dir = self.game_state_data.game_data_dir
        elif self.game_state is not None and hasattr(self.game_state, "game_data_dir"):
            game_data_dir = self.game_state.game_data_dir

        # Try to load from file first
        if game_data_dir:
            try:
                armor_file = os.path.join(game_data_dir, "game_armor.json")
                if os.path.exists(armor_file):
                    with open(armor_file, "r") as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading armor database: {e}")

        # If file loading fails, derive from items in graph
        armor = {}

        # Find items that could be armor based on name
        armor_keywords = [
            "armor",
            "shield",
            "helmet",
            "gauntlet",
            "glove",
            "boot",
            "robe",
            "cloak",
            "plate",
            "chain",
            "leather",
        ]

        # Get items from game_state_data or fall back to game_state
        items = []
        if hasattr(self.game_state_data, "items"):
            items = self.game_state_data.items
        elif self.game_state is not None and hasattr(self.game_state, "items"):
            items = self.game_state.items

        for item in items:
            item_lower = item.lower()

            # Check if item name contains armor keywords
            is_armor = any(keyword in item_lower for keyword in armor_keywords)

            if is_armor:
                # Determine armor type
                armor_type = "light"  # Default

                if any(
                    word in item_lower for word in ["plate", "heavy", "steel", "iron"]
                ):
                    armor_type = "heavy"
                elif any(word in item_lower for word in ["robe", "cloth", "silk"]):
                    armor_type = "cloth"
                elif any(word in item_lower for word in ["shield"]):
                    armor_type = "shield"
                elif any(word in item_lower for word in ["leather", "hide"]):
                    armor_type = "light"

                # Generate armor properties based on name
                name_power = len(item) % 5 + 1

                # Check for magical qualities
                has_magic = any(
                    word in item_lower
                    for word in [
                        "magic",
                        "enchanted",
                        "ancient",
                        "mystic",
                        "legendary",
                        "cursed",
                        "blessed",
                    ]
                )
                elemental_resistance = None

                for element, keywords in [
                    ("fire", ["fire", "flame", "heat"]),
                    ("ice", ["ice", "frost", "cold"]),
                    ("lightning", ["lightning", "thunder", "shock"]),
                    ("poison", ["poison", "venom", "toxic"]),
                    ("holy", ["holy", "sacred", "divine"]),
                    ("dark", ["dark", "shadow", "void"]),
                ]:
                    if any(keyword in item_lower for keyword in keywords):
                        elemental_resistance = element
                        has_magic = True
                        break

                # Create armor entry
                armor[item] = {
                    "name": item,
                    "type": armor_type,
                    "defense": 3 + name_power + (3 if has_magic else 0),
                    "magical": has_magic,
                    "elemental_resistance": elemental_resistance,
                    "durability": 100,
                    "effects": [],
                    "requirements": {"level": 1},
                }

                # Add special effects based on armor properties
                if has_magic and elemental_resistance:
                    armor[item]["effects"].append(f"{elemental_resistance}_resistance")

                if "legendary" in item_lower or "ancient" in item_lower:
                    armor[item]["effects"].append("damage_reflection")
                    armor[item]["requirements"]["level"] = 3

                # Type-specific bonuses
                if armor_type == "heavy":
                    armor[item]["defense"] += 5
                    armor[item]["effects"].append("reduced_evasion")
                elif armor_type == "light":
                    armor[item]["defense"] += 2
                    armor[item]["effects"].append("increased_evasion")
                elif armor_type == "cloth":
                    armor[item]["defense"] += 1
                    armor[item]["effects"].append("increased_mana")
                elif armor_type == "shield":
                    armor[item]["defense"] += 3
                    armor[item]["effects"].append("block_chance")

        return armor

    def _derive_weakness_map(self) -> Dict[str, List[str]]:
        """
        Derive entity weaknesses from the knowledge graph.

        Returns:
            Dictionary mapping entity types to their weaknesses
        """
        weakness_map = {
            "beast": ["fire", "poison"],
            "undead": ["holy", "fire"],
            "magical": ["physical", "surprise"],
            "monster": ["silver", "magic"],
            "elemental": [],
            "humanoid": [],
        }

        # Enhance with data from the knowledge graph if available
        if self.relations_df is not None:
            weakness_relations = self.relations_df.loc[
                self.relations_df["predicate"].isin(
                    ["weak_against", "vulnerable_to", "fears"]
                )
            ]
        else:
            # If no relations dataframe is available, return just the default weakness map
            return weakness_map

        for _, relation in weakness_relations.iterrows():
            subject = relation["subject"]
            object_ = relation["object"]

            # Try to map subject to an enemy type
            subject_type = None
            for enemy_data in self.enemy_database.values():
                if enemy_data["name"].lower() == subject:
                    subject_type = enemy_data["type"]
                    break

            # If we found a type, add the weakness
            if subject_type and subject_type in weakness_map:
                if object_ not in weakness_map[subject_type]:
                    weakness_map[subject_type].append(object_)

            # Also add individual enemy weaknesses
            if subject in self.enemy_database:
                if "weaknesses" not in self.enemy_database[subject]:
                    self.enemy_database[subject]["weaknesses"] = []

                if object_ not in self.enemy_database[subject]["weaknesses"]:
                    self.enemy_database[subject]["weaknesses"].append(object_)

        return weakness_map

    def _derive_environment_effects(self) -> Dict[str, Dict[str, Any]]:
        """
        Derive environment effects from location data.

        Returns:
            Dictionary mapping locations to their combat effects
        """
        environment_effects = {}

        # Default effects for generic environment types
        default_effects = {
            "forest": {"evasion_bonus": 10, "effects": ["cover"]},
            "cave": {"evasion_penalty": 5, "effects": ["darkness"]},
            "mountain": {"stamina_cost": 1.2, "effects": ["high_ground"]},
            "swamp": {
                "movement_penalty": 0.7,
                "effects": ["difficult_terrain", "poison_hazard"],
            },
            "castle": {"defense_bonus": 5, "effects": ["defensible_position"]},
            "temple": {"magic_bonus": 10, "effects": ["holy_ground"]},
            "dungeon": {"attack_penalty": 5, "effects": ["confined_space"]},
            "river": {"magic_bonus": 5, "effects": ["flowing_water"]},
        }

        # Get locations from game_state_data or fall back to game_state
        locations = []
        if hasattr(self.game_state_data, "locations"):
            locations = self.game_state_data.locations
        elif self.game_state is not None and hasattr(self.game_state, "locations"):
            locations = self.game_state.locations

        # Apply default effects based on location name patterns
        for location in locations:
            location_lower = location.lower()
            environment_effects[location] = {"effects": [], "bonuses": {}}

            # Check for environment types in the name
            for env_type, effects in default_effects.items():
                if env_type in location_lower:
                    environment_effects[location]["effects"].extend(effects["effects"])

                    # Add numeric bonuses/penalties
                    for key, value in effects.items():
                        if key != "effects":
                            environment_effects[location]["bonuses"][key] = value

        # Enhance with data from the knowledge graph if available
        if self.relations_df is not None:
            environment_relations = self.relations_df.loc[
                self.relations_df["predicate"].isin(
                    ["has_feature", "contains", "provides"]
                )
            ]
        else:
            # If no relations dataframe is available, return just the default environment effects
            return environment_effects

        for _, relation in environment_relations.iterrows():
            subject = relation["subject"]
            object_ = relation["object"]

            # If subject is a location we know
            if subject in environment_effects:
                # Add special effect based on object
                special_effect = None

                for effect_word, effect_name in [
                    (["water", "river", "lake"], "water_terrain"),
                    (["fire", "lava", "flame"], "fire_hazard"),
                    (["dark", "shadow", "night"], "darkness"),
                    (["light", "sunny", "bright"], "bright_light"),
                    (["holy", "blessed", "sacred"], "holy_ground"),
                    (["curse", "evil", "corrupt"], "cursed_ground"),
                    (["narrow", "tight", "confined"], "confined_space"),
                    (["open", "vast", "wide"], "open_ground"),
                    (["elevated", "high", "tall"], "high_ground"),
                ]:
                    if any(word in object_ for word in effect_word):
                        special_effect = effect_name
                        break

                if (
                    special_effect
                    and special_effect not in environment_effects[subject]["effects"]
                ):
                    environment_effects[subject]["effects"].append(special_effect)

        return environment_effects

    def start_combat(self, enemy_name: str) -> bool:
        """
        Start a combat encounter with an enemy.

        Args:
            enemy_name: Name of the enemy to fight

        Returns:
            Boolean indicating if combat started successfully
        """
        # Check if enemy exists and is in the current location
        npcs_here = [
            npc
            for npc, data in self.game_state_data.npc_states.items()
            if data["location"] == self.game_state_data.player_location
        ]

        if enemy_name not in npcs_here:
            return False

        # Check if enemy is in the database
        if enemy_name not in self.enemy_database:
            # Not a combat-capable NPC
            return False

        # Create a copy of the enemy data for this combat
        enemy_data = self.enemy_database[enemy_name].copy()

        # Get environment effects
        environment = self.environment_effects.get(
            self.game_state_data.player_location, {"effects": [], "bonuses": {}}
        )

        # Initialize combat state
        self.active_combat = {
            "enemy": enemy_data,
            "status": CombatStatus.ACTIVE,
            "turn": 0,
            "player_next_action": None,
            "enemy_next_action": None,
            "combat_log": [f"Combat with {enemy_name} has begun!"],
            "environment": environment,
            "player_temp_stats": self.player_stats.copy(),
            "enemy_temp_stats": enemy_data.copy(),
        }

        # Apply environment effects to starting stats
        self._apply_environment_effects()

        # Apply equipped item bonuses
        self._apply_equipment_effects()

        # Record the combat event
        if self.game_state:
            self.game_state.player_actions.append(
                f"Started combat with {enemy_name} in {self.game_state_data.player_location}"
            )
        elif hasattr(self.game_state_data, "player_actions"):
            self.game_state_data.player_actions.append(
                f"Started combat with {enemy_name} in {self.game_state_data.player_location}"
            )

        return True

    def _apply_environment_effects(self):
        """Apply environmental effects to combatants."""
        if not self.active_combat or "environment" not in self.active_combat:
            return

        environment = self.active_combat["environment"]

        # Apply numeric bonuses
        for stat, value in environment.get("bonuses", {}).items():
            if "evasion" in stat:
                if "bonus" in stat:
                    self.active_combat["player_temp_stats"]["evasion"] += value
                elif "penalty" in stat:
                    self.active_combat["player_temp_stats"]["evasion"] -= value

            if "defense" in stat:
                if "bonus" in stat:
                    self.active_combat["player_temp_stats"]["defense"] += value
                elif "penalty" in stat:
                    self.active_combat["player_temp_stats"]["defense"] -= value

        # Record effects in combat log
        if environment.get("effects"):
            effects_str = ", ".join(environment["effects"])
            self.active_combat["combat_log"].append(
                f"The environment provides effects: {effects_str}"
            )

    def _apply_equipment_effects(self):
        """Apply effects from equipped items."""
        if not self.active_combat:
            return

        # Apply weapon effects
        weapon = self.player_stats.get("equipped_weapon")
        if weapon and weapon in self.weapon_database:
            weapon_data = self.weapon_database[weapon]

            # Basic damage bonus
            self.active_combat["player_temp_stats"]["damage_bonus"] = weapon_data[
                "damage"
            ]

            # Critical hit bonus
            if "critical_bonus" in weapon_data:
                self.active_combat["player_temp_stats"]["critical_chance"] += (
                    weapon_data["critical_bonus"]
                )

            # Elemental effects
            if weapon_data.get("elemental_type"):
                self.active_combat["player_temp_stats"]["damage_type"] = weapon_data[
                    "elemental_type"
                ]

            # Log equipment
            self.active_combat["combat_log"].append(f"You are wielding {weapon}")

        # Apply armor effects
        armor = self.player_stats.get("equipped_armor")
        if armor and armor in self.armor_database:
            armor_data = self.armor_database[armor]

            # Basic defense bonus
            self.active_combat["player_temp_stats"]["defense"] += armor_data["defense"]

            # Special effects
            if "effects" in armor_data:
                for effect in armor_data["effects"]:
                    if effect == "increased_evasion":
                        self.active_combat["player_temp_stats"]["evasion"] += 5
                    elif effect == "reduced_evasion":
                        self.active_combat["player_temp_stats"]["evasion"] -= 5
                    elif effect == "block_chance":
                        self.active_combat["player_temp_stats"]["block_chance"] = 20
                    elif effect == "increased_mana":
                        self.active_combat["player_temp_stats"]["max_mana"] += 20
                        self.active_combat["player_temp_stats"]["mana"] += 20

            # Elemental resistance
            if armor_data.get("elemental_resistance"):
                resistance = armor_data["elemental_resistance"]
                if "resistances" not in self.active_combat["player_temp_stats"]:
                    self.active_combat["player_temp_stats"]["resistances"] = []
                self.active_combat["player_temp_stats"]["resistances"].append(
                    resistance
                )

            # Log equipment
            self.active_combat["combat_log"].append(f"You are wearing {armor}")

    def process_combat_action(self, action: str, target: str = None) -> Dict[str, Any]:
        """
        Process a player's combat action.

        Args:
            action: The combat action to perform
            target: The target of the action (optional)

        Returns:
            Dictionary with the results of the action
        """
        if (
            not self.active_combat
            or self.active_combat["status"] != CombatStatus.ACTIVE
        ):
            return {"success": False, "message": "No active combat"}

        # Increment turn counter
        self.active_combat["turn"] += 1

        # Get enemy data
        enemy = self.active_combat["enemy"]

        # Process player action
        player_result = self._process_player_combat_action(action, target)

        # If combat ended after player action, return result
        if self.active_combat["status"] != CombatStatus.ACTIVE:
            return player_result

        # Process enemy action
        enemy_result = self._process_enemy_combat_action()

        # Check for status changes (defeated, victory, etc.)
        self._check_combat_status()

        # Combine results
        result = {
            "success": True,
            "player_action": player_result,
            "enemy_action": enemy_result,
            "combat_status": self.active_combat["status"].value,
            "player_health": self.active_combat["player_temp_stats"]["health"],
            "enemy_health": self.active_combat["enemy"]["health"],
            "combat_log": self.active_combat["combat_log"][-3:],  # Last 3 log entries
        }

        return result

    def _process_player_combat_action(
        self, action: str, target: str = None
    ) -> Dict[str, Any]:
        """Process the player's combat action."""
        # Default result
        result = {"success": False, "message": "Invalid action", "damage": 0}

        # Get player and enemy data
        player = self.active_combat["player_temp_stats"]
        enemy = self.active_combat["enemy"]

        # Handle different action types
        if action == "attack":
            # Basic attack
            hit_chance = 70 + player.get("dexterity", 10) - enemy.get("evasion", 0)
            hit_roll = random.randint(1, 100)

            if hit_roll <= hit_chance:
                # Hit! Calculate damage
                base_damage = 5 + player.get("strength", 10) // 2
                weapon_bonus = player.get("damage_bonus", 0)
                total_damage = base_damage + weapon_bonus

                # Deduct enemy defense
                defense = enemy.get("defense", 0)
                damage = max(1, total_damage - defense)

                # Check for critical hit
                crit_chance = player.get("critical_chance", 5)
                crit_roll = random.randint(1, 100)

                if crit_roll <= crit_chance:
                    damage = damage * 2
                    self.active_combat["combat_log"].append("Critical hit!")

                # Apply damage
                enemy["health"] -= damage

                # Update result
                result = {
                    "success": True,
                    "message": f"You hit {enemy['name']} for {damage} damage.",
                    "damage": damage,
                    "critical": crit_roll <= crit_chance,
                }

                # Add to combat log
                self.active_combat["combat_log"].append(result["message"])
            else:
                # Miss
                result = {
                    "success": False,
                    "message": f"Your attack misses {enemy['name']}.",
                    "damage": 0,
                }

                # Add to combat log
                self.active_combat["combat_log"].append(result["message"])

        elif action == "block":
            # Defensive stance - increases defense for this turn
            defense_bonus = 5 + player.get("strength", 10) // 2
            player["defense"] += defense_bonus
            player["blocking"] = True

            result = {
                "success": True,
                "message": f"You assume a defensive stance, increasing your defense by {defense_bonus}.",
                "defense_bonus": defense_bonus,
            }

            # Add to combat log
            self.active_combat["combat_log"].append(result["message"])

        elif action == "dodge":
            # Evasive maneuver - increases evasion for this turn
            evasion_bonus = 10 + player.get("dexterity", 10) // 2
            player["evasion"] += evasion_bonus
            player["dodging"] = True

            result = {
                "success": True,
                "message": f"You prepare to dodge, increasing your evasion by {evasion_bonus}.",
                "evasion_bonus": evasion_bonus,
            }

            # Add to combat log
            self.active_combat["combat_log"].append(result["message"])

        elif action == "use":
            # Use an item in combat
            # Get inventory from game_state_data or fall back to game_state
            inventory = []
            if hasattr(self.game_state_data, "inventory"):
                inventory = self.game_state_data.inventory
            elif self.game_state is not None and hasattr(self.game_state, "inventory"):
                inventory = self.game_state.inventory

            if not target or target not in inventory:
                result = {
                    "success": False,
                    "message": f"You don't have {target} in your inventory.",
                    "damage": 0,
                }
                self.active_combat["combat_log"].append(result["message"])
                return result

            # Process different item types
            if "potion" in target.lower() or "heal" in target.lower():
                # Healing item
                heal_amount = random.randint(20, 40)
                player["health"] = min(
                    player["max_health"], player["health"] + heal_amount
                )

                result = {
                    "success": True,
                    "message": f"You use {target} and heal for {heal_amount} health.",
                    "heal_amount": heal_amount,
                }
