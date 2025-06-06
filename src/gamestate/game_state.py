import os
import json
import networkx as nx
import pandas as pd
import random
import difflib
from typing import Dict, List, Tuple, Optional, Set, Any
import time
from .game_state_data import GameStateData


class GameState:
    """Class to maintain the current state of the game and provide game logic operations."""

    def __init__(self, game_data_dir: str, save_file: str = None):
        """
        Initialize the game state.

        Args:
            game_data_dir: Directory containing game data files
            save_file: Path to save file (optional)
        """
        # Store game_data_dir for backward compatibility
        self.game_data_dir = game_data_dir

        # Initialize the data container
        self.data = GameStateData(game_data_dir=game_data_dir)

        # Graph and dataframes for knowledge representation
        self.graph = None
        self.entities_df = None
        self.relations_df = None

        # Load the knowledge graph and game elements
        self.load_game_data()

        # Set initial location or load from save file
        if save_file and os.path.exists(save_file):
            self.load_game(save_file)
        else:
            if self.data.locations:
                self.data.player_location = self.data.locations[0]

    # Property accessors for backward compatibility
    @property
    def player_location(self):
        return self.data.player_location

    @player_location.setter
    def player_location(self, value):
        self.data.player_location = value

    @property
    def inventory(self):
        return self.data.inventory

    @inventory.setter
    def inventory(self, value):
        self.data.inventory = value

    @property
    def visited_locations(self):
        return self.data.visited_locations

    @visited_locations.setter
    def visited_locations(self, value):
        self.data.visited_locations = value

    @property
    def npc_states(self):
        return self.data.npc_states

    @npc_states.setter
    def npc_states(self, value):
        self.data.npc_states = value

    @property
    def quests(self):
        return self.data.quests

    @quests.setter
    def quests(self, value):
        self.data.quests = value

    @property
    def game_turn(self):
        return self.data.game_turn

    @game_turn.setter
    def game_turn(self, value):
        self.data.game_turn = value

    @property
    def player_actions(self):
        return self.data.player_actions

    @player_actions.setter
    def player_actions(self, value):
        self.data.player_actions = value

    @property
    def world_state(self):
        return self.data.world_state

    @world_state.setter
    def world_state(self, value):
        self.data.world_state = value

    @property
    def characters(self):
        return self.data.characters

    @characters.setter
    def characters(self, value):
        self.data.characters = value

    @property
    def locations(self):
        return self.data.locations

    @locations.setter
    def locations(self, value):
        self.data.locations = value

    @property
    def items(self):
        return self.data.items

    @items.setter
    def items(self, value):
        self.data.items = value

    def add_to_visited_locations(self):
        """Add the current player location to visited locations."""
        self.data.visited_locations.add(self.data.player_location)

    def load_game_data(self):
        """Load the knowledge graph and game elements from files."""
        print("Loading game data...")

        try:
            # Load graph
            graph_path = os.path.join(self.data.game_data_dir, "knowledge_graph.gexf")
            if os.path.exists(graph_path):
                self.graph = nx.read_gexf(graph_path)
                print(f"Loaded knowledge graph with {len(self.graph.nodes)} nodes")
            else:
                print(f"Warning: Knowledge graph not found at {graph_path}")
                self.graph = nx.Graph()

            # Load game elements
            self.data.locations = self._load_csv_column(
                os.path.join(self.data.game_data_dir, "game_locations.csv"), "location"
            )
            self.data.characters = self._load_csv_column(
                os.path.join(self.data.game_data_dir, "game_characters.csv"),
                "character",
            )
            self.data.items = self._load_csv_column(
                os.path.join(self.data.game_data_dir, "game_items.csv"), "item"
            )
            self.data.actions = self._load_csv_column(
                os.path.join(self.data.game_data_dir, "game_actions.csv"), "action"
            )

            # Load entities and relations for context retrieval
            entities_path = os.path.join(self.data.game_data_dir, "entities.csv")
            if os.path.exists(entities_path):
                self.entities_df = pd.read_csv(entities_path)
            else:
                print(f"Warning: Entities file not found at {entities_path}")
                self.entities_df = pd.DataFrame(
                    columns=["id", "text", "label", "source_file", "chunk_id"]
                )

            relations_path = os.path.join(self.data.game_data_dir, "relations.csv")
            if os.path.exists(relations_path):
                self.relations_df = pd.read_csv(relations_path)
            else:
                print(f"Warning: Relations file not found at {relations_path}")
                self.relations_df = pd.DataFrame(
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
            for character in self.data.characters:
                if character not in self.data.npc_states:
                    self.data.npc_states[character] = {
                        "location": random.choice(self.data.locations)
                        if self.data.locations
                        else "Unknown",
                        "disposition": random.randint(
                            30, 70
                        ),  # 0-100 scale for NPC opinion of player
                        "state": "neutral",
                        "met_player": False,
                        "conversations": [],
                    }

            # Initialize faction relationships if any are defined in files
            faction_file = os.path.join(self.data.game_data_dir, "game_factions.csv")
            if os.path.exists(faction_file):
                factions_df = pd.read_csv(faction_file)
                for _, row in factions_df.iterrows():
                    self.data.world_state["player_faction_standing"][row["faction"]] = 0

            # Initialize faction relationships
            faction_relation_file = os.path.join(
                self.data.game_data_dir, "game_faction_relations.csv"
            )
            if os.path.exists(faction_relation_file):
                relations_df = pd.read_csv(faction_relation_file)
                for _, row in relations_df.iterrows():
                    if (
                        row["faction_1"]
                        not in self.data.world_state["faction_relationships"]
                    ):
                        self.data.world_state["faction_relationships"][
                            row["faction_1"]
                        ] = {}

                    self.data.world_state["faction_relationships"][row["faction_1"]][
                        row["faction_2"]
                    ] = row["relation_value"]

            print(
                f"Loaded {len(self.data.locations)} locations, {len(self.data.characters)} characters, {len(self.data.items)} items"
            )

        except Exception as e:
            print(f"Error loading game data: {e}")
            import traceback

            traceback.print_exc()

            # Initialize with empty data to avoid crashes
            self.graph = nx.Graph()
            self.data.locations = ["Starting Location"]
            self.data.characters = []
            self.data.items = []
            self.data.actions = []
            self.entities_df = pd.DataFrame()
            self.relations_df = pd.DataFrame()

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
        location_info = self._get_location_info(self.data.player_location)

        # Get information about NPCs in current location
        npcs_here = [
            npc
            for npc, data in self.data.npc_states.items()
            if data["location"] == self.data.player_location
        ]

        npc_info = {}
        for npc in npcs_here:
            npc_info[npc] = self._get_character_info(npc)

        # Compile context
        context = {
            "player": {
                "location": self.data.player_location,
                "inventory": self.data.inventory,
                "visited_locations": list(self.data.visited_locations),
                "faction_standings": self.data.world_state["player_faction_standing"],
                "significant_actions": self.data.player_actions[-10:]
                if self.data.player_actions
                else [],
            },
            "current_location": location_info,
            "npcs_present": npc_info,
            "world_events": self.data.world_state["world_events"],
            "game_turn": self.data.game_turn,
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
        if hasattr(self, "graph") and location_id in self.graph.nodes:
            for neighbor in self.graph.neighbors(location_id):
                node_data = self.graph.nodes[neighbor]
                if "label" in node_data:
                    connected_locations.append(node_data["label"])

        # Get items at this location
        # In a real game, you'd have a proper item placement system
        # This is a simplified approach where items are placed somewhat randomly
        items_here = []
        if hasattr(self, "graph") and hasattr(self.data, "items"):
            for item in self.data.items:
                item_id = item.lower().replace(" ", "_")
                if item_id in self.graph.nodes:
                    # Check if item is related to this location in the graph
                    if item_id in self.graph.neighbors(location_id):
                        items_here.append(item)

        # If no items were found through graph relations, add some random ones
        # (This ensures there are always some items for testing)
        if not items_here and random.random() < 0.7:
            potential_items = [
                item for item in self.data.items if item not in self.data.inventory
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
        if hasattr(self, "graph") and character_id in self.graph.nodes:
            for neighbor in self.graph.neighbors(character_id):
                edge_data = self.graph.get_edge_data(character_id, neighbor)
                if edge_data and "relation" in edge_data:
                    node_data = self.graph.nodes[neighbor]
                    if "label" in node_data:
                        relations.append(
                            {
                                "other_character": node_data["label"],
                                "relation": edge_data["relation"],
                            }
                        )

        # Get the character's state
        state = self.data.npc_states.get(
            character,
            {
                "state": "neutral",
                "disposition": 50,
                "met_player": False,
                "conversations": [],
            },
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
            # Use fuzzy matching for location names
            matched_location, confidence = (
                self.find_best_match(target, "location") if target else (None, 0.0)
            )

            if matched_location and confidence >= 0.6:
                # Check if location is connected to current location
                location_info = self._get_location_info(self.data.player_location)
                if matched_location in location_info["connected_locations"]:
                    # Store previous location for graph update
                    previous_location = self.data.player_location

                    # Update player location
                    self.data.player_location = matched_location
                    self.data.visited_locations.add(matched_location)

                    # Update graph: player left previous location
                    self.update_graph_relationship(
                        subject="player",
                        relation="located_in",
                        object_=previous_location,
                        add=False,
                    )

                    # Update graph: player entered new location
                    self.update_graph_relationship(
                        subject="player",
                        relation="located_in",
                        object_=matched_location,
                        add=True,
                    )

                    # Update NPCs who see the player arrive
                    for npc, data in self.data.npc_states.items():
                        if (
                            data["location"] == matched_location
                            and not data["met_player"]
                        ):
                            self.data.npc_states[npc]["met_player"] = True

                            # Update graph: player met NPC
                            self.update_graph_relationship(
                                subject="player", relation="met", object_=npc, add=True
                            )

                    return True
                else:
                    return False  # Location not connected
            else:
                return False  # Not a valid location

        # Handle taking items
        elif action in ["take", "get", "pick"]:
            # Use fuzzy matching for item names
            matched_item, confidence = (
                self.find_best_match(target, "item") if target else (None, 0.0)
            )

            if matched_item and confidence >= 0.6:
                location_info = self._get_location_info(self.data.player_location)
                if matched_item in location_info["items"]:
                    # Add item to inventory
                    self.data.inventory.append(matched_item)

                    # Update graph: item is no longer at location
                    self.update_graph_relationship(
                        subject=self.data.player_location,
                        relation="contains",
                        object_=matched_item,
                        add=False,
                    )

                    # Update graph: player now owns item
                    self.update_graph_relationship(
                        subject="player",
                        relation="owns",
                        object_=matched_item,
                        add=True,
                    )

                    # Record the action
                    self.data.player_actions.append(
                        f"Took {matched_item} from {self.data.player_location}"
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
                for npc, data in self.data.npc_states.items()
                if data["location"] == self.data.player_location
            ]

            # Use fuzzy matching for character names
            matched_npc, confidence = None, 0.0
            if target:
                # First try to find a direct match among NPCs in the current location
                for npc in npcs_here:
                    # Check if target matches the first name or full name (case insensitive)
                    npc_parts = npc.lower().split()
                    if npc.lower() == target.lower() or (
                        npc_parts and npc_parts[0] == target.lower()
                    ):
                        matched_npc, confidence = npc, 1.0
                        break

                # If no direct match, try fuzzy matching among NPCs in the current location
                if not matched_npc:
                    for npc in npcs_here:
                        similarity = difflib.SequenceMatcher(
                            None, target.lower(), npc.lower()
                        ).ratio()
                        if similarity > confidence and similarity >= 0.6:
                            matched_npc, confidence = npc, similarity

            if matched_npc:
                # Record that the player has met this NPC
                first_meeting = not self.data.npc_states[matched_npc]["met_player"]
                self.data.npc_states[matched_npc]["met_player"] = True

                # Add to conversation history (would add actual dialogue in a full game)
                self.data.npc_states[matched_npc]["conversations"].append(
                    f"Turn {self.data.game_turn}"
                )

                # Update graph: player talked to NPC
                self.update_graph_relationship(
                    subject="player",
                    relation="talked_to",
                    object_=matched_npc,
                    add=True,
                )

                # If this is the first meeting, add that relationship too
                if first_meeting:
                    self.update_graph_relationship(
                        subject="player", relation="met", object_=matched_npc, add=True
                    )

                # Update disposition based on faction relationships
                # Get NPC's faction
                npc_faction = None
                for faction, standing in self.data.world_state[
                    "player_faction_standing"
                ].items():
                    if self._is_character_in_faction(matched_npc, faction):
                        npc_faction = faction
                        # NPC's initial reaction is influenced by faction standing
                        faction_modifier = standing / 10
                        self.data.npc_states[matched_npc]["disposition"] += (
                            faction_modifier
                        )
                        self.data.npc_states[matched_npc]["disposition"] = max(
                            0,
                            min(100, self.data.npc_states[matched_npc]["disposition"]),
                        )

                        # Update graph with faction relationship if it exists
                        if npc_faction:
                            self.update_graph_relationship(
                                subject=matched_npc,
                                relation="belongs_to",
                                object_=npc_faction,
                                add=True,
                            )

                return True
            else:
                return False  # NPC not here

        # Handle using items
        elif action in ["use", "activate", "operate"]:
            # Use fuzzy matching for inventory items
            matched_item, confidence = None, 0.0
            if target:
                for item in self.data.inventory:
                    similarity = difflib.SequenceMatcher(
                        None, target.lower(), item.lower()
                    ).ratio()
                    if similarity > confidence and similarity >= 0.6:
                        matched_item, confidence = item, similarity

            if matched_item:
                # Update graph: player used item
                self.update_graph_relationship(
                    subject="player", relation="used", object_=matched_item, add=True
                )

                # Update graph: item was used at location
                self.update_graph_relationship(
                    subject=matched_item,
                    relation="used_at",
                    object_=self.data.player_location,
                    add=True,
                )

                # Record the action
                self.data.player_actions.append(
                    f"Used {matched_item} in {self.data.player_location}"
                )
                return True
            else:
                return False  # Item not in inventory

        # Handle attacking (combat would be more complex in a real game)
        elif action in ["attack", "fight", "kill"]:
            npcs_here = [
                npc
                for npc, data in self.data.npc_states.items()
                if data["location"] == self.data.player_location
            ]

            # Use fuzzy matching for character names
            matched_npc, confidence = (
                self.find_best_match(target, "character") if target else (None, 0.0)
            )
            if matched_npc and matched_npc in npcs_here:
                # Update graph: player attacked NPC
                self.update_graph_relationship(
                    subject="player", relation="attacked", object_=matched_npc, add=True
                )

                # Update graph: NPC is hostile to player
                self.update_graph_relationship(
                    subject=matched_npc,
                    relation="hostile_to",
                    object_="player",
                    add=True,
                )

                # Record the action - this is a major action that impacts relationships
                self.data.player_actions.append(
                    f"Attacked {matched_npc} in {self.data.player_location}"
                )

                # Drastically reduce NPC disposition
                self.data.npc_states[matched_npc]["disposition"] = max(
                    0, self.data.npc_states[matched_npc]["disposition"] - 50
                )
                self.data.npc_states[matched_npc]["state"] = "hostile"

                # Update faction standing if NPC belongs to a faction
                for faction, standing in self.data.world_state[
                    "player_faction_standing"
                ].items():
                    if self._is_character_in_faction(matched_npc, faction):
                        self.data.world_state["player_faction_standing"][faction] -= 20

                        # Update graph: faction relationship worsened
                        self.update_graph_relationship(
                            subject="player",
                            relation="antagonized",
                            object_=faction,
                            add=True,
                        )

                        # Also affect allied factions
                        if faction in self.data.world_state["faction_relationships"]:
                            for other_faction, relation in self.data.world_state[
                                "faction_relationships"
                            ][faction].items():
                                if relation > 50:  # Allied faction
                                    if (
                                        other_faction
                                        in self.data.world_state[
                                            "player_faction_standing"
                                        ]
                                    ):
                                        self.data.world_state[
                                            "player_faction_standing"
                                        ][other_faction] -= 10

                                        # Update graph: allied faction relationship also worsened
                                        self.update_graph_relationship(
                                            subject="player",
                                            relation="antagonized",
                                            object_=other_faction,
                                            add=True,
                                        )

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
            faction_relations = self.relations_df.loc[
                (self.relations_df["subject"] == character_lower)
                & (self.relations_df["predicate"].isin(["belongs_to", "member_of"]))
                & (self.relations_df["object"] == faction_lower)
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
        if subject_id not in self.graph.nodes:
            self.graph.add_node(subject_id, label=subject)
        if object_id not in self.graph.nodes:
            self.graph.add_node(object_id, label=object_)

        if add:
            # Add the relationship
            self.graph.add_edge(subject_id, object_id, relation=relation)

            # Add to relations dataframe for retrieval - more efficient approach
            if hasattr(self, "relations_df"):
                new_relation = {
                    "subject": subject.lower(),
                    "predicate": relation.lower(),
                    "object": object_.lower(),
                    "source_file": "player_actions",
                    "chunk_id": -1,
                    "sentence": f"{subject} {relation} {object_}.",
                }
                # More efficient than pd.concat - avoids creating a new DataFrame
                self.relations_df.loc[len(self.relations_df)] = new_relation
            return True
        else:
            # Remove the relationship if it exists
            if self.graph.has_edge(subject_id, object_id):
                self.graph.remove_edge(subject_id, object_id)

                # Remove from relations dataframe
                if hasattr(self, "relations_df"):
                    mask = (
                        (self.relations_df["subject"] == subject.lower())
                        & (self.relations_df["predicate"] == relation.lower())
                        & (self.relations_df["object"] == object_.lower())
                    )
                    self.relations_df = self.relations_df[~mask]
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
        if faction in self.data.world_state["player_faction_standing"]:
            current = self.data.world_state["player_faction_standing"][faction]
            self.data.world_state["player_faction_standing"][faction] = max(
                -100, min(100, current + change)
            )

            # Also update relations with opposing or allied factions
            if faction in self.data.world_state["faction_relationships"]:
                for other_faction, relation in self.data.world_state[
                    "faction_relationships"
                ][faction].items():
                    if relation < -50:  # Enemy factions
                        if (
                            other_faction
                            in self.data.world_state["player_faction_standing"]
                        ):
                            inverse_change = (
                                -change * 0.5
                            )  # Inverse effect, but not as strong
                            current = self.data.world_state["player_faction_standing"][
                                other_faction
                            ]
                            self.data.world_state["player_faction_standing"][
                                other_faction
                            ] = max(-100, min(100, current + inverse_change))
                    elif relation > 50:  # Allied factions
                        if (
                            other_faction
                            in self.data.world_state["player_faction_standing"]
                        ):
                            reduced_change = (
                                change * 0.5
                            )  # Same direction, but not as strong
                            current = self.data.world_state["player_faction_standing"][
                                other_faction
                            ]
                            self.data.world_state["player_faction_standing"][
                                other_faction
                            ] = max(-100, min(100, current + reduced_change))
            return True
        else:
            # Faction doesn't exist
            return False

    def find_best_match(self, name: str, category: str = None) -> Tuple[str, float]:
        """
        Find the best match for a name using fuzzy matching.

        Args:
            name: The name to match
            category: Optional category to limit search ("character", "location", "item")

        Returns:
            Tuple of (best_match, confidence_score)
        """
        import difflib

        # Normalize the input name
        name = name.lower().strip()

        # Determine which list to search
        if category == "character":
            search_list = self.data.characters
        elif category == "location":
            search_list = self.data.locations
        elif category == "item":
            search_list = self.data.items
        else:
            # Search all entities if no category specified
            search_list = self.data.characters + self.data.locations + self.data.items

        # If the name is empty, return no match
        if not name:
            return (None, 0.0)

        # First check for exact matches (case-insensitive)
        for item in search_list:
            if name.lower() == item.lower():
                return (item, 1.0)

        # Check for first name matches for characters with multi-word names
        if category == "character" or category is None:
            for character in self.data.characters:
                parts = character.lower().split()
                if parts and name == parts[0]:
                    return (character, 0.9)

        # Use difflib to find the closest match
        matches = difflib.get_close_matches(
            name, [item.lower() for item in search_list], n=1, cutoff=0.6
        )

        if matches:
            # Find the original case version
            for item in search_list:
                if item.lower() == matches[0]:
                    # Calculate similarity score
                    similarity = difflib.SequenceMatcher(
                        None, name, item.lower()
                    ).ratio()
                    return (item, similarity)

        # No good match found
        return (None, 0.0)

    def record_world_event(self, event_name: str, event_data: Any = None) -> None:
        """
        Record that a world event has occurred.

        Args:
            event_name: Name of the event
            event_data: Additional data about the event (optional)
        """
        self.data.world_state["world_events"][event_name] = {
            "turn": self.data.game_turn,
            "data": event_data,
        }

        # Add to player actions
        self.player_actions.append(
            f"Event: {event_name} occurred on turn {self.game_turn}"
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
                "player_location": self.player_location,
                "inventory": self.inventory,
                "visited_locations": list(self.visited_locations),
                "npc_states": self.npc_states,
                "quests": self.quests,
                "game_turn": self.game_turn,
                "player_actions": self.player_actions,
                "world_state": self.world_state,
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

            self.player_location = save_data["player_location"]
            self.inventory = save_data["inventory"]
            self.visited_locations = set(save_data["visited_locations"])
            self.npc_states = save_data["npc_states"]
            self.quests = save_data["quests"]
            self.game_turn = save_data["game_turn"]
            self.player_actions = save_data["player_actions"]
            self.world_state = save_data["world_state"]

            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
