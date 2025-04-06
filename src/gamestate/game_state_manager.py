import os
import json
import networkx as nx
import pandas as pd
import random
from typing import Dict, List, Tuple, Optional, Set, Any
from custom_types import GameState, WorldState
import time


class GameStateManager:
    """Class to maintain the current state of the game."""

    def __init__(self, game_data_dir: str, save_file: str = None):
        """
        Initialize the game state.

        Args:
            game_data_dir: Directory containing game data files
            save_file: Path to save file (optional)
        """
        self.game_state: GameState = GameState(
            game_data_dir=game_data_dir,
            player_location=None,
            inventory=[],
            visited_locations=[],
            npc_states={},
            quests={},
            game_turn=0,
            locations=[],
            player_actions=[],
            world_state=WorldState(),
            characters=[],
            items=[],
            actions=[],
            entities_df=pd.DataFrame(),
            relations_df=pd.DataFrame(),
        )

        # Load the knowledge graph and game elements
        self.load_game_data()

        # Set initial location or load from save file
        if save_file and os.path.exists(save_file):
            self.load_game(save_file)
        else:
            if hasattr(self, "locations") and self.locations:
                self.player_location = self.locations[0]
                self.visited_locations.add(self.player_location)

    def load_game_data(self):
        """Load the knowledge graph and game elements from files."""
        print("Loading game data...")

        try:
            # Load graph
            graph_path = os.path.join(self.game_data_dir, "knowledge_graph.gexf")
            if os.path.exists(graph_path):
                self.game_state.graph = nx.read_gexf(graph_path)
                print(f"Loaded knowledge graph with {len(self.graph.nodes)} nodes")
            else:
                print(f"Warning: Knowledge graph not found at {graph_path}")
                self.game_state.graph = nx.Graph()

            # Load game elements
            self.game_state.locations = self._load_csv_column(
                os.path.join(self.game_data_dir, "game_locations.csv"), "location"
            )
            self.game_state.characters = self._load_csv_column(
                os.path.join(self.game_data_dir, "game_characters.csv"), "character"
            )
            self.game_state.items = self._load_csv_column(
                os.path.join(self.game_data_dir, "game_items.csv"), "item"
            )
            self.game_state.actions = self._load_csv_column(
                os.path.join(self.game_data_dir, "game_actions.csv"), "action"
            )

            # Load entities and relations for context retrieval
            entities_path = os.path.join(self.game_data_dir, "entities.csv")
            if os.path.exists(entities_path):
                self.game_state.entities_df = pd.read_csv(entities_path)
            else:
                print(f"Warning: Entities file not found at {entities_path}")
                self.game_state.entities_df = pd.DataFrame(
                    columns=["id", "text", "label", "source_file", "chunk_id"]
                )

            relations_path = os.path.join(self.game_state.game_data_dir, "relations.csv")
            if os.path.exists(relations_path):
                self.game_state.relations_df = pd.read_csv(relations_path)
            else:
                print(f"Warning: Relations file not found at {relations_path}")
                self.game_state.relations_df = pd.DataFrame(
                    columns=[
                        "subject",
                        "predicate",
                        "object",
                        "sentence",
                        "source_file",
                        "chunk_id",
                    ]
                )

            # Initialize NPC states
            for character in self.characters:
                self.game_state.npc_states[character] = {
                    "location": random.choice(self.locations)
                    if self.game_state.locations
                    else "Unknown",
                    "disposition": random.randint(
                        30, 70
                    ),  # 0-100 scale for NPC opinion of player
                    "state": "neutral",
                    "met_player": False,
                    "conversations": [],
                }

            # Initialize faction relationships if any are defined in files
            faction_file = os.path.join(self.game_state.game_data_dir, "game_factions.csv")
            if os.path.exists(faction_file):
                factions_df = pd.read_csv(faction_file)
                for _, row in factions_df.iterrows():
                    self.game_state.world_state["player_faction_standing"][row["faction"]] = 0

            # Initialize faction relationships
            faction_relation_file = os.path.join(
                self.game_state.game_data_dir, "game_faction_relations.csv"
            )
            if os.path.exists(faction_relation_file):
                relations_df = pd.read_csv(faction_relation_file)
                for _, row in relations_df.iterrows():
                    if (
                        row["faction_1"]
                        not in self.game_state.world_state["faction_relationships"]
                    ):
                        self.game_state.world_state["faction_relationships"][row["faction_1"]] = {}

                    self.game_state.world_state["faction_relationships"][row["faction_1"]][
                        row["faction_2"]
                    ] = row["relation_value"]

            print(
                f"Loaded {len(self.game_state.locations)} locations, {len(self.game_state.characters)} characters, {len(self.game_state.items)} items"
            )

        except Exception as e:
            print(f"Error loading game data: {e}")
            import traceback

            traceback.print_exc()

            self.game_state.locations=["Starting location"]
            # Initialize with empty data to avoid crashes
            # Note: all items were initialized in the constructor
            # self.graph = nx.Graph()
            # self.locations = ["Starting Location"]
            # self.characters = []
            # self.items = []
            # self.actions = []
            # self.entities_df = pd.DataFrame()
            # self.relations_df = pd.DataFrame()

    def _load_csv_column(self, file_path: str, column_name: str) -> List[str]:
        """
        Helper method to load a column from a CSV file.

        Args:
            file_path: Path to CSV file
            column_name: Name of column to load

        Returns:
            List of values from the column
        """
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                return df[column_name].tolist()
            else:
                print(f"Warning: File not found at {file_path}")
                return []
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current game context for the AI.

        Returns:
            Dictionary with all relevant context
        """
        # Get information about current location
        location_info = self._get_location_info(self.game_state.player_location)

        # Get information about NPCs in current location
        npcs_here = [
            npc
            for npc, data in self.game_state.npc_states.items()
            if data["location"] == self.game_state.player_location
        ]

        npc_info = {}
        for npc in npcs_here:
            npc_info[npc] = self._get_character_info(npc)

        # Compile context
        context = {
            "player": {
                "location": self.game_state.player_location,
                "inventory": self.game_state.inventory,
                "visited_locations": list(self.game_state.visited_locations),
                "faction_standings": self.game_state.world_state["player_faction_standing"],
                "significant_actions": self.game_state.player_actions[-10:]
                if self.game_state.player_actions
                else [],
            },
            "current_location": location_info,
            "npcs_present": npc_info,
            "world_events": self.game_state.world_state["world_events"],
            "game_turn": self.game_state.game_turn,
        }

        return context

    def _get_location_info(self, location: str) -> Dict[str, Any]:
        """
        Get information about a location from the knowledge graph.

        Args:
            location: Name of the location

        Returns:
            Dictionary with location information
        """
        # Get information about the location from entities and relations
        location_id = location.lower().replace(" ", "_")

        # Get connected locations
        connected_locations = []
        if hasattr(self, "graph") and location_id in self.game_state.graph.nodes:
            for neighbor in self.game_state.graph.neighbors(location_id):
                node_data = self.game_state.graph.nodes[neighbor]
                if "label" in node_data:
                    connected_locations.append(node_data["label"])

        # Get items at this location
        # In a real game, you'd have a proper item placement system
        # This is a simplified approach where items are placed somewhat randomly
        items_here = []
        if hasattr(self, "graph") and hasattr(self, "items"):
            for item in self.game_state.items:
                item_id = item.lower().replace(" ", "_")
                if item_id in self.game_state.graph.nodes:
                    # Check if item is related to this location in the graph
                    if item_id in self.game_state.graph.neighbors(location_id):
                        items_here.append(item)

        # If no items were found through graph relations, add some random ones
        # (This ensures there are always some items for testing)
        if not items_here and random.random() < 0.7:
            potential_items = [
                item for item in self.game_state.items if item not in self.game_state.inventory
            ]
            if potential_items:
                num_items = random.randint(1, min(3, len(potential_items)))
                items_here = random.sample(potential_items, num_items)

        return {
            "name": location,
            "connected_locations": connected_locations,
            "items": items_here,
        }

    def _get_character_info(self, character: str) -> Dict[str, Any]:
        """
        Get information about a character from the knowledge graph.

        Args:
            character: Name of the character

        Returns:
            Dictionary with character information
        """
        character_id = character.lower().replace(" ", "_")

        # Get relations with other characters
        relations = []
        if hasattr(self.game_state, "graph") and character_id in self.game_state.graph.nodes:
            for neighbor in self.game_state.graph.neighbors(character_id):
                edge_data = self.game_state.graph.get_edge_data(character_id, neighbor)
                if edge_data and "relation" in edge_data:
                    node_data = self.game_state.graph.nodes[neighbor]
                    if "label" in node_data:
                        relations.append(
                            {
                                "other_character": node_data["label"],
                                "relation": edge_data["relation"],
                            }
                        )

        # Get the character's state
        state = self.game_state.npc_states.get(
            character, {"state": "neutral", "disposition": 50, "met_player": False}
        )

        # Get character's faction if any
        faction = None
        if hasattr(self, "relations_df"):
            faction_relations = self.relations_df.loc[
                (self.relations_df["subject"] == character.lower())
                & (self.relations_df["predicate"] == "belongs_to")
            ]

            if not faction_relations.empty:
                faction = faction_relations.iloc[0]["object"]

        return {
            "name": character,
            "relations": relations,
            "state": state["state"],
            "disposition": state["disposition"],
            "met_player": state["met_player"],
            "faction": faction,
            "recent_conversations": state["conversations"][-3:]
            if state["conversations"]
            else [],
        }

    def update_state(self, action: str, target: str = None) -> bool:
        """
        Update the game state based on player action.

        Args:
            action: The action verb
            target: The target of the action (optional)

        Returns:
            Boolean indicating if action was successful
        """
        # Handle movement
        if action in ["go", "move", "travel", "walk"]:
            if target in self.game_state.locations:
                # Check if location is connected to current location
                location_info = self._get_location_info(self.game_state.player_location)
                if target in location_info["connected_locations"]:
                    self.game_state.player_location = target
                    self.game_state.visited_locations.add(target)

                    # Update NPCs who see the player arrive
                    for npc, data in self.game_state.npc_states.items():
                        if data["location"] == target and not data["met_player"]:
                            self.game_state.npc_states[npc]["met_player"] = True

                    return True
                else:
                    return False  # Location not connected
            else:
                return False  # Not a valid location

        # Handle taking items
        elif action in ["take", "get", "pick"]:
            if target in self.game_state.items:
                location_info = self._get_location_info(self.game_state.player_location)
                if target in location_info["items"]:
                    self.game_state.inventory.append(target)
                    # In a full game, you'd remove it from the location
                    # This simplified version doesn't track item locations accurately
                    self.game_state.player_actions.append(
                        f"Took {target} from {self.game_state.player_location}"
                    )
                    return True
                else:
                    return False  # Item not at this location
            else:
                return False  # Not a valid item

        # Handle talking to NPCs
        elif action in ["talk", "speak", "ask"]:
            npcs_here = [
                npc
                for npc, data in self.game_state.npc_states.items()
                if data["location"] == self.game_state.player_location
            ]

            if target in npcs_here:
                # Record that the player has met this NPC
                self.game_state.npc_states[target]["met_player"] = True

                # Add to conversation history (would add actual dialogue in a full game)
                self.game_state.npc_states[target]["conversations"].append(
                    f"Turn {self.game_state.game_turn}"
                )

                # Update disposition based on faction relationships
                # Get NPC's faction
                npc_faction = None
                for faction, standing in self.game_state.world_state[
                    "player_faction_standing"
                ].items():
                    if self._is_character_in_faction(target, faction):
                        npc_faction = faction
                        # NPC's initial reaction is influenced by faction standing
                        faction_modifier = standing / 10
                        self.game_state.npc_states[target]["disposition"] += faction_modifier
                        self.game_state.npc_states[target]["disposition"] = max(
                            0, min(100, self.game_state.npc_states[target]["disposition"])
                        )

                return True
            else:
                return False  # NPC not here

        # Handle using items
        elif action in ["use", "activate", "operate"]:
            if target in self.game_state.inventory:
                # Record the action
                self.game_state.player_actions.append(f"Used {target} in {self.game_state.player_location}")
                return True
            else:
                return False  # Item not in inventory

        # Handle attacking (combat would be more complex in a real game)
        elif action in ["attack", "fight", "kill"]:
            npcs_here = [
                npc
                for npc, data in self.game_state.npc_states.items()
                if data["location"] == self.game_state.player_location
            ]

            if target in npcs_here:
                # Record the action - this is a major action that impacts relationships
                self.game_state.player_actions.append(
                    f"Attacked {target} in {self.game_state.player_location}"
                )

                # Drastically reduce NPC disposition
                self.game_state.npc_states[target]["disposition"] = max(
                    0, self.game_state.npc_states[target]["disposition"] - 50
                )
                self.game_state.npc_states[target]["state"] = "hostile"

                # Update faction standing if NPC belongs to a faction
                for faction, standing in self.game_state.world_state[
                    "player_faction_standing"
                ].items():
                    if self._is_character_in_faction(target, faction):
                        self.game_state.world_state["player_faction_standing"][faction] -= 20

                        # Also affect allied factions
                        if faction in self.game_state.world_state["faction_relationships"]:
                            for other_faction, relation in self.game_state.world_state[
                                "faction_relationships"
                            ][faction].items():
                                if relation > 50:  # Allied faction
                                    if (
                                        other_faction
                                        in self.game_state.world_state["player_faction_standing"]
                                    ):
                                        self.game_state.world_state["player_faction_standing"][
                                            other_faction
                                        ] -= 10

                return True
            else:
                return False  # Target not present

        # Default case - let AI interpret other actions
        return True

    def _is_character_in_faction(self, character: str, faction: str) -> bool:
        """
        Check if a character belongs to a faction.

        Args:
            character: Name of the character
            faction: Name of the faction

        Returns:
            Boolean indicating if character belongs to faction
        """
        character_lower = character.lower()
        faction_lower = faction.lower()

        # Check in relations DataFrame
        if hasattr(self, "relations_df"):
            faction_relations = self.game_state.relations_df.loc[
                (self.game_state.relations_df["subject"] == character_lower)
                & (self.game_state.relations_df["predicate"].isin(["belongs_to", "member_of"]))
                & (self.game_state.relations_df["object"] == faction_lower)
            ]

            return not faction_relations.empty

        return False

    def update_graph_relationship(
        self, subject: str, relation: str, object_: str, add: bool = True
    ) -> bool:
        """
        Add or remove a relationship in the knowledge graph.

        Args:
            subject: The subject entity
            relation: The relationship type
            object_: The object entity
            add: Whether to add (True) or remove (False) the relationship

        Returns:
            Boolean indicating success
        """
        if not hasattr(self, "graph"):
            print("Warning: No graph available for relationship update")
            return False

        subject_id = subject.lower().replace(" ", "_")
        object_id = object_.lower().replace(" ", "_")

        # Ensure nodes exist
        if subject_id not in self.game_state.graph.nodes:
            self.game_state.graph.add_node(subject_id, label=subject)
        if object_id not in self.game_state.graph.nodes:
            self.game_state.graph.add_node(object_id, label=object_)

        if add:
            # Add the relationship
            self.game_state.graph.add_edge(subject_id, object_id, relation=relation)

            # Add to relations dataframe for retrieval
            if hasattr(self, "relations_df"):
                new_relation = {
                    "subject": subject.lower(),
                    "predicate": relation.lower(),
                    "object": object_.lower(),
                    "source_file": "player_actions",
                    "chunk_id": -1,
                    "sentence": f"{subject} {relation} {object_}.",
                }
                self.game_state.relations_df = pd.concat(
                    [self.game_state.relations_df, pd.DataFrame([new_relation])], ignore_index=True
                )
            return True
        else:
            # Remove the relationship if it exists
            if self.game_state.graph.has_edge(subject_id, object_id):
                self.game_state.graph.remove_edge(subject_id, object_id)

                # Remove from relations dataframe
                if hasattr(self, "relations_df"):
                    mask = (
                        (self.game_state.relations_df["subject"] == subject.lower())
                        & (self.game_state.relations_df["predicate"] == relation.lower())
                        & (self.game_state.relations_df["object"] == object_.lower())
                    )
                    self.game_state.relations_df = self.game_state.relations_df[~mask]
                return True

            return False  # Edge didn't exist

    def update_faction_standing(self, faction: str, change: float) -> bool:
        """
        Update the player's standing with a faction.

        Args:
            faction: The faction name
            change: The amount to change (positive or negative)

        Returns:
            Boolean indicating success
        """
        if faction in self.game_state.world_state["player_faction_standing"]:
            current = self.game_state.world_state["player_faction_standing"][faction]
            self.game_state.world_state["player_faction_standing"][faction] = max(
                -100, min(100, current + change)
            )

            # Also update relations with opposing or allied factions
            if faction in self.game_state.world_state["faction_relationships"]:
                for other_faction, relation in self.game_state.world_state[
                    "faction_relationships"
                ][faction].items():
                    if relation < -50:  # Enemy factions
                        if other_faction in self.game_state.world_state["player_faction_standing"]:
                            inverse_change = (
                                -change * 0.5
                            )  # Inverse effect, but not as strong
                            current = self.game_state.world_state["player_faction_standing"][
                                other_faction
                            ]
                            self.game_state.world_state["player_faction_standing"][
                                other_faction
                            ] = max(-100, min(100, current + inverse_change))
                    elif relation > 50:  # Allied factions
                        if other_faction in self.game_state.world_state["player_faction_standing"]:
                            reduced_change = (
                                change * 0.5
                            )  # Same direction, but not as strong
                            current = self.game_state.world_state["player_faction_standing"][
                                other_faction
                            ]
                            self.game_state.world_state["player_faction_standing"][
                                other_faction
                            ] = max(-100, min(100, current + reduced_change))
            return True
        else:
            # Faction doesn't exist
            return False

    def record_world_event(self, event_name: str, event_data: Any = None) -> None:
        """
        Record that a world event has occurred.

        Args:
            event_name: Name of the event
            event_data: Additional data about the event (optional)
        """
        self.game_state.world_state["world_events"][event_name] = {
            "turn": self.game_state.game_turn,
            "data": event_data,
        }

        # Add to player actions
        self.game_state.player_actions.append(
            f"Event: {event_name} occurred on turn {self.game_state.game_turn}"
        )

    def save_game(self, save_file: str) -> bool:
        """
        Save the current game state to a file.

        Args:
            save_file: Path to save file

        Returns:
            Boolean indicating success
        """
        try:
            # Convert sets to lists for JSON serialization
            save_data = {
                "player_location": self.game_state.player_location,
                "inventory": self.game_state.inventory,
                "visited_locations": list(self.game_state.visited_locations),
                "npc_states": self.game_state.npc_states,
                "quests": self.game_state.quests,
                "game_turn": self.game_state.game_turn,
                "player_actions": self.game_state.player_actions,
                "world_state": self.game_state.world_state,
            }

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_file)), exist_ok=True)

            with open(save_file, "w") as f:
                json.dump(save_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, save_file: str) -> bool:
        """
        Load game state from a file.

        Args:
            save_file: Path to save file

        Returns:
            Boolean indicating success
        """
        try:
            with open(save_file, "r") as f:
                save_data = json.load(f)

            self.game_state.player_location = save_data["player_location"]
            self.game_state.inventory = save_data["inventory"]
            self.game_state.visited_locations = set(save_data["visited_locations"])
            self.game_state.npc_states = save_data["npc_states"]
            self.game_state.quests = save_data["quests"]
            self.game_state.game_turn = save_data["game_turn"]
            self.game_state.player_actions = save_data["player_actions"]
            self.game_state.world_state = save_data["world_state"]

            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
