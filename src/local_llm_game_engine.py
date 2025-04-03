import os
import json
import networkx as nx
import pandas as pd
import random
import re
from typing import Dict, List, Tuple, Any, Optional
import requests
from enum import Enum

class CombatStatus(Enum):
    """Enum for the status of a combat encounter."""
    ACTIVE = "active"
    PLAYER_VICTORY = "player_victory"
    PLAYER_DEFEATED = "player_defeated"
    PLAYER_FLED = "player_fled"
    ENDED = "ended"  # Generic ended state (e.g., through dialogue/surrender)

class GameState:
    """Class to maintain the current state of the game."""

    def __init__(self, game_data_dir: str, save_file: str = None):
        """
        Initialize the game state.

        Args:
            game_data_dir: Directory containing game data files
            save_file: Path to save file (optional)
        """
        self.game_data_dir = game_data_dir
        self.player_location = None
        self.inventory = []
        self.visited_locations = set()
        self.npc_states = {}    # For tracking NPC states and relationships with player
        self.quests = {}        # For tracking active and completed quests
        self.game_turn = 0      # Track the number of turns
        self.player_actions = []  # History of significant player actions

        # World state for factions and global events
        self.world_state = {
            "faction_relationships": {},  # Relationships between factions
            "player_faction_standing": {},  # Player's standing with each faction
            "world_events": {}  # Major world events that have occurred
        }

        # Load the knowledge graph and game elements
        self.load_game_data()

        # Set initial location or load from save file
        if save_file and os.path.exists(save_file):
            self.load_game(save_file)
        else:
            if self.locations:
                self.player_location = self.locations[0]
                self.visited_locations.add(self.player_location)

    def load_game_data(self):
        """Load the knowledge graph and game elements from files."""
        # Load graph
        graph_path = os.path.join(self.game_data_dir, "knowledge_graph.gexf")
        self.graph = nx.read_gexf(graph_path)

        # Load game elements
        self.locations = self._load_csv_column(os.path.join(self.game_data_dir, "game_locations.csv"), "location")
        self.characters = self._load_csv_column(os.path.join(self.game_data_dir, "game_characters.csv"), "character")
        self.items = self._load_csv_column(os.path.join(self.game_data_dir, "game_items.csv"), "item")
        self.actions = self._load_csv_column(os.path.join(self.game_data_dir, "game_actions.csv"), "action")

        # Load entities and relations for context retrieval
        self.entities_df = pd.read_csv(os.path.join(self.game_data_dir, "entities.csv"))
        self.relations_df = pd.read_csv(os.path.join(self.game_data_dir, "relations.csv"))

        # Initialize NPC states
        for character in self.characters:
            self.npc_states[character] = {
                "location": random.choice(self.locations),
                "disposition": random.randint(30, 70),  # 0-100 scale for NPC opinion of player
                "state": "neutral",
                "met_player": False,
                "conversations": []
            }

        # Initialize faction relationships if any are defined in files
        faction_file = os.path.join(self.game_data_dir, "game_factions.csv")
        if os.path.exists(faction_file):
            factions_df = pd.read_csv(faction_file)
            for _, row in factions_df.iterrows():
                self.world_state["player_faction_standing"][row["faction"]] = 0

        # Initialize faction relationships
        faction_relation_file = os.path.join(self.game_data_dir, "game_faction_relations.csv")
        if os.path.exists(faction_relation_file):
            relations_df = pd.read_csv(faction_relation_file)
            for _, row in relations_df.iterrows():
                if row["faction_1"] not in self.world_state["faction_relationships"]:
                    self.world_state["faction_relationships"][row["faction_1"]] = {}

                self.world_state["faction_relationships"][row["faction_1"]][row["faction_2"]] = row["relation_value"]

    def _load_csv_column(self, file_path: str, column_name: str) -> List[str]:
        """Helper method to load a column from a CSV file."""
        try:
            df = pd.read_csv(file_path)
            return df[column_name].tolist()
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
        location_info = self._get_location_info(self.player_location)

        # Get information about NPCs in current location
        npcs_here = [npc for npc, data in self.npc_states.items()
                    if data["location"] == self.player_location]

        npc_info = {}
        for npc in npcs_here:
            npc_info[npc] = self._get_character_info(npc)

        # Compile context
        context = {
            "player": {
                "location": self.player_location,
                "inventory": self.inventory,
                "visited_locations": list(self.visited_locations),
                "faction_standings": self.world_state["player_faction_standing"],
                "significant_actions": self.player_actions[-10:] if self.player_actions else []
            },
            "current_location": location_info,
            "npcs_present": npc_info,
            "world_events": self.world_state["world_events"],
            "game_turn": self.game_turn
        }

        return context

    def _get_location_info(self, location: str) -> Dict[str, Any]:
        """Get information about a location from the knowledge graph."""
        # Get information about the location from entities and relations
        location_id = location.lower().replace(' ', '_')

        # Get connected locations
        connected_locations = []
        if location_id in self.graph.nodes:
            for neighbor in self.graph.neighbors(location_id):
                node_data = self.graph.nodes[neighbor]
                if 'label' in node_data:
                    connected_locations.append(node_data['label'])

        # Get items at this location
        # In a real game, you'd have a proper item placement system
        # This is a simplified approach where items are placed somewhat randomly
        items_here = []
        for item in self.items:
            item_id = item.lower().replace(' ', '_')
            if item_id in self.graph.nodes:
                # Check if item is related to this location in the graph
                if item_id in self.graph.neighbors(location_id):
                    items_here.append(item)

        # If no items were found through graph relations, add some random ones
        # (This ensures there are always some items for testing)
        if not items_here and random.random() < 0.7:
            potential_items = [item for item in self.items if item not in self.inventory]
            if potential_items:
                num_items = random.randint(1, min(3, len(potential_items)))
                items_here = random.sample(potential_items, num_items)

        return {
            "name": location,
            "connected_locations": connected_locations,
            "items": items_here
        }

    def _get_character_info(self, character: str) -> Dict[str, Any]:
        """Get information about a character from the knowledge graph."""
        character_id = character.lower().replace(' ', '_')

        # Get relations with other characters
        relations = []
        if character_id in self.graph.nodes:
            for neighbor in self.graph.neighbors(character_id):
                edge_data = self.graph.get_edge_data(character_id, neighbor)
                if edge_data and 'relation' in edge_data:
                    node_data = self.graph.nodes[neighbor]
                    if 'label' in node_data:
                        relations.append({
                            "other_character": node_data['label'],
                            "relation": edge_data['relation']
                        })

        # Get the character's state
        state = self.npc_states.get(character, {"state": "neutral", "disposition": 50, "met_player": False})

        # Get character's faction if any
        faction = None
        for faction_relation in self.relations_df.loc[
            (self.relations_df['subject'] == character.lower()) &
            (self.relations_df['predicate'] == 'belongs_to')
        ].itertuples():
            faction = faction_relation.object

        return {
            "name": character,
            "relations": relations,
            "state": state["state"],
            "disposition": state["disposition"],
            "met_player": state["met_player"],
            "faction": faction,
            "recent_conversations": state["conversations"][-3:] if state["conversations"] else []
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
        self.game_turn += 1

        # Handle movement
        if action in ["go", "move", "travel", "walk"]:
            if target in self.locations:
                # Check if location is connected to current location
                location_info = self._get_location_info(self.player_location)
                if target in location_info["connected_locations"]:
                    self.player_location = target
                    self.visited_locations.add(target)

                    # Update NPCs who see the player arrive
                    for npc, data in self.npc_states.items():
                        if data["location"] == target and not data["met_player"]:
                            self.npc_states[npc]["met_player"] = True

                    return True
                else:
                    return False  # Location not connected
            else:
                return False  # Not a valid location

        # Handle taking items
        elif action in ["take", "get", "pick"]:
            if target in self.items:
                location_info = self._get_location_info(self.player_location)
                if target in location_info["items"]:
                    self.inventory.append(target)
                    # In a full game, you'd remove it from the location
                    # This simplified version doesn't track item locations accurately
                    self.player_actions.append(f"Took {target} from {self.player_location}")
                    return True
                else:
                    return False  # Item not at this location
            else:
                return False  # Not a valid item

        # Handle talking to NPCs
        elif action in ["talk", "speak", "ask"]:
            npcs_here = [npc for npc, data in self.npc_states.items()
                        if data["location"] == self.player_location]

            if target in npcs_here:
                # Record that the player has met this NPC
                self.npc_states[target]["met_player"] = True

                # Add to conversation history (would add actual dialogue in a full game)
                self.npc_states[target]["conversations"].append(f"Turn {self.game_turn}")

                # Update disposition based on faction relationships
                # Get NPC's faction
                npc_faction = None
                for faction, standing in self.world_state["player_faction_standing"].items():
                    if self._is_character_in_faction(target, faction):
                        npc_faction = faction
                        # NPC's initial reaction is influenced by faction standing
                        faction_modifier = standing / 10
                        self.npc_states[target]["disposition"] += faction_modifier
                        self.npc_states[target]["disposition"] = max(0, min(100, self.npc_states[target]["disposition"]))

                return True
            else:
                return False  # NPC not here

        # Handle using items
        elif action in ["use", "activate", "operate"]:
            if target in self.inventory:
                # Record the action
                self.player_actions.append(f"Used {target} in {self.player_location}")
                return True
            else:
                return False  # Item not in inventory

        # Handle attacking (combat would be more complex in a real game)
        elif action in ["attack", "fight", "kill"]:
            npcs_here = [npc for npc, data in self.npc_states.items()
                        if data["location"] == self.player_location]

            if target in npcs_here:
                # Record the action - this is a major action that impacts relationships
                self.player_actions.append(f"Attacked {target} in {self.player_location}")

                # Drastically reduce NPC disposition
                self.npc_states[target]["disposition"] = max(0, self.npc_states[target]["disposition"] - 50)
                self.npc_states[target]["state"] = "hostile"

                # Update faction standing if NPC belongs to a faction
                for faction, standing in self.world_state["player_faction_standing"].items():
                    if self._is_character_in_faction(target, faction):
                        self.world_state["player_faction_standing"][faction] -= 20

                        # Also affect allied factions
                        if faction in self.world_state["faction_relationships"]:
                            for other_faction, relation in self.world_state["faction_relationships"][faction].items():
                                if relation > 50:  # Allied faction
                                    if other_faction in self.world_state["player_faction_standing"]:
                                        self.world_state["player_faction_standing"][other_faction] -= 10

                return True
            else:
                return False  # Target not present

        # Default case - let AI interpret other actions
        return True

    def _is_character_in_faction(self, character: str, faction: str) -> bool:
        """Check if a character belongs to a faction."""
        character_lower = character.lower()
        faction_lower = faction.lower()

        # Check in relations DataFrame
        faction_relations = self.relations_df.loc[
            (self.relations_df['subject'] == character_lower) &
            (self.relations_df['predicate'].isin(['belongs_to', 'member_of'])) &
            (self.relations_df['object'] == faction_lower)
        ]

        return not faction_relations.empty

    def update_graph_relationship(self, subject: str, relation: str, object_: str, add: bool = True) -> bool:
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
        subject_id = subject.lower().replace(' ', '_')
        object_id = object_.lower().replace(' ', '_')

        # Ensure nodes exist
        if subject_id not in self.graph.nodes:
            self.graph.add_node(subject_id, label=subject)
        if object_id not in self.graph.nodes:
            self.graph.add_node(object_id, label=object_)

        if add:
            # Add the relationship
            self.graph.add_edge(subject_id, object_id, relation=relation)

            # Add to relations dataframe for retrieval
            new_relation = {
                'subject': subject.lower(),
                'predicate': relation.lower(),
                'object': object_.lower(),
                'source_file': 'player_actions',
                'chunk_id': -1,
                'sentence': f"{subject} {relation} {object_}."
            }
            self.relations_df = pd.concat([self.relations_df, pd.DataFrame([new_relation])], ignore_index=True)
            return True
        else:
            # Remove the relationship if it exists
            if self.graph.has_edge(subject_id, object_id):
                self.graph.remove_edge(subject_id, object_id)

                # Remove from relations dataframe
                mask = ((self.relations_df['subject'] == subject.lower()) &
                       (self.relations_df['predicate'] == relation.lower()) &
                       (self.relations_df['object'] == object_.lower()))
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
        if faction in self.world_state["player_faction_standing"]:
            current = self.world_state["player_faction_standing"][faction]
            self.world_state["player_faction_standing"][faction] = max(-100, min(100, current + change))

            # Also update relations with opposing or allied factions
            if faction in self.world_state["faction_relationships"]:
                for other_faction, relation in self.world_state["faction_relationships"][faction].items():
                    if relation < -50:  # Enemy factions
                        if other_faction in self.world_state["player_faction_standing"]:
                            inverse_change = -change * 0.5  # Inverse effect, but not as strong
                            current = self.world_state["player_faction_standing"][other_faction]
                            self.world_state["player_faction_standing"][other_faction] = max(-100, min(100, current + inverse_change))

                    elif relation > 50:  # Allied factions
                        if other_faction in self.world_state["player_faction_standing"]:
                            reduced_change = change * 0.5  # Same direction, but not as strong
                            current = self.world_state["player_faction_standing"][other_faction]
                            self.world_state["player_faction_standing"][other_faction] = max(-100, min(100, current + reduced_change))

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
        self.world_state["world_events"][event_name] = {
            "turn": self.game_turn,
            "data": event_data
        }

        # Add to player actions
        self.player_actions.append(f"Event: {event_name} occurred on turn {self.game_turn}")

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
                "world_state": self.world_state
            }

            with open(save_file, 'w') as f:
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
            with open(save_file, 'r') as f:
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


class LocalLLMEngine:
    """Class to handle interaction with a local LLM for text generation."""

    def __init__(self, model_path: str = None, host: str = "localhost", port: int = 8000):
        """
        Initialize the Local LLM engine.

        Args:
            model_path: Path to local model (if loading directly)
            host: Host where LLM server is running
            port: Port where LLM server is running
        """
        self.model_path = model_path
        self.host = host
        self.port = port
        self.api_url = f"http://{host}:{port}/api/generate"

        # Placeholder for directly loaded model (if using libraries like llama-cpp-python)
        self.model = None

        # Load model directly if path is provided and not using API
        if model_path and model_path.endswith(('.bin', '.gguf')):
            self._load_local_model()

    def _load_local_model(self):
        """Load a local model directly using llama-cpp-python or similar."""
        try:
            # This is just an example - you'd use the appropriate library for your model
            from llama_cpp import Llama

            print(f"Loading local model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,          # Context window size
                n_threads=4          # Number of CPU threads to use
            )
            print("Local model loaded successfully")

        except ImportError:
            print("llama-cpp-python not found. Please install it or use API mode.")
            self.model = None
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generate text using the local LLM.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (higher = more random)

        Returns:
            Generated text
        """
        # If model is loaded directly, use it
        if self.model:
            try:
                output = self.model(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return output["choices"][0]["text"]
            except Exception as e:
                print(f"Error generating with local model: {e}")
                return "[Error generating response with local model]"

        # Otherwise use API
        try:
            response = requests.post(
                self.api_url,
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return f"[Network error: {str(e)}]"
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "[Error generating response]"


class GraphRAGEngine:
    """Class to handle retrieval-augmented generation using the knowledge graph."""

    def __init__(self, game_data_dir: str, llm_engine: LocalLLMEngine = None):
        """
        Initialize the GraphRAG engine.

        Args:
            game_data_dir: Directory containing game data files
            llm_engine: Local LLM engine instance
        """
        self.game_data_dir = game_data_dir
        self.llm_engine = llm_engine

        # Load the document chunks for retrieval
        chunks_path = os.path.join(game_data_dir, "document_chunks.csv")
        self.chunks_df = pd.read_csv(chunks_path)

        # Load the knowledge graph
        graph_path = os.path.join(game_data_dir, "knowledge_graph.gexf")
        self.graph = nx.read_gexf(graph_path)

    def retrieve_relevant_context(self, query: str, state: GameState, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant context from the knowledge graph and document chunks.

        Args:
            query: The user's command/query
            state: The current game state
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant text chunks
        """
        # Extract entities from query (simplified - would use NLP in production)
        query_terms = set(query.lower().split())

        # Get entities related to current location
        location_id = state.player_location.lower().replace(' ', '_')
        location_related_entities = set()

        if location_id in self.graph.nodes:
            # Get nodes connected to location
            for neighbor in self.graph.neighbors(location_id):
                node_data = self.graph.nodes[neighbor]
                if 'label' in node_data:
                    location_related_entities.add(node_data['label'].lower())

        # Get entities related to NPCs in current location
        npc_related_entities = set()
        npcs_here = [npc for npc, data in state.npc_states.items()
                    if data["location"] == state.player_location]

        for npc in npcs_here:
            npc_id = npc.lower().replace(' ', '_')
            if npc_id in self.graph.nodes:
                for neighbor in self.graph.neighbors(npc_id):
                    node_data = self.graph.nodes[neighbor]
                    if 'label' in node_data:
                        npc_related_entities.add(node_data['label'].lower())

        # Combine all search terms
        search_terms = query_terms.union(location_related_entities).union(npc_related_entities)

        # Simple search functionality - find chunks containing the search terms
        # In a production system, this would use vector similarity or more sophisticated retrieval
        relevant_chunks = []
        scores = []

        for _, row in self.chunks_df.iterrows():
            chunk_text = row['chunk_text'].lower()
            score = sum(1 for term in search_terms if term in chunk_text)
            if score > 0:
                relevant_chunks.append(row['chunk_text'])
                scores.append(score)

        # Sort chunks by relevance score and take top-k
        if relevant_chunks:
            sorted_chunks = [x for _, x in sorted(zip(scores, relevant_chunks), reverse=True)]
            return sorted_chunks[:top_k]

        # Fallback to current location description if no relevant chunks found
        return [f"You are in {state.player_location}. There are {len(npcs_here)} characters here."]

    def generate_response(self, query: str, state: GameState) -> str:
        """
        Generate a response to the user's query using the GraphRAG system.

        Args:
            query: The user's command/query
            state: The current game state

        Returns:
            Generated response
        """
        # Get current game context
        context = state.get_current_context()

        # Retrieve relevant text chunks
        relevant_chunks = self.retrieve_relevant_context(query, state)

        # Parse the user command (simplified)
        command_parts = query.lower().split()
        action = command_parts[0] if command_parts else ""
        target = " ".join(command_parts[1:]) if len(command_parts) > 1 else None

        # Update game state based on command
        action_success = state.update_state(action, target)

        # If using LLM
        if self.llm_engine:
            return self._generate_with_llm(query, context, relevant_chunks, action_success)
        else:
            # Fallback to rule-based response generation
            return self._generate_rule_based(query, context, relevant_chunks, action_success)

    def _generate_with_llm(self, query: str, context: Dict, relevant_chunks: List[str], action_success: bool) -> str:
        """Generate a response using the local LLM."""
        try:
            # Construct the prompt
            prompt = self._construct_prompt(query, context, relevant_chunks, action_success)

            # Call the LLM
            response = self.llm_engine.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            return response

        except Exception as e:
            print(f"Error calling local LLM: {e}")
            return self._generate_rule_based(query, context, relevant_chunks, action_success)

    def _construct_prompt(self, query: str, context: Dict, relevant_chunks: List[str], action_success: bool) -> str:
        """Construct a prompt for the language model."""
        current_location = context["current_location"]["name"]
        npcs_present = list(context["npcs_present"].keys())

        # Combine relevant chunks into context text
        context_text = "\n\n".join(relevant_chunks)

        # Format player inventory
        inventory_text = ", ".join(context['player']['inventory']) if context['player']['inventory'] else "Nothing"

        # Format player faction standings
        faction_text = ""
        if "faction_standings" in context["player"]:
            standings = []
            for faction, value in context["player"]["faction_standings"].items():
                if value < -50:
                    relation = "hated by"
                elif value < -20:
                    relation = "disliked by"
                elif value < 20:
                    relation = "neutral with"
                elif value < 50:
                    relation = "liked by"
                else:
                    relation = "revered by"

                standings.append(f"{relation} the {faction}")

            if standings:
                faction_text = f"\nFaction relations: You are {'; '.join(standings)}."

        # Format player history
        history_text = ""
        if "significant_actions" in context["player"] and context["player"]["significant_actions"]:
            history_text = "\nRecent significant actions:\n- " + "\n- ".join(context["player"]["significant_actions"])

        # Format world events
        event_text = ""
        if context["world_events"]:
            events = []
            for event, data in context["world_events"].items():
                events.append(f"{event} (turn {data['turn']})")

            if events:
                event_text = f"\nWorld events: {', '.join(events)}"

        # Format NPC information
        npc_text = ""
        if npcs_present:
            npc_details = []
            for npc, info in context["npcs_present"].items():
                disposition = info["disposition"]
                if disposition < 20:
                    feeling = "hostile"
                elif disposition < 40:
                    feeling = "suspicious"
                elif disposition < 60:
                    feeling = "neutral"
                elif disposition < 80:
                    feeling = "friendly"
                else:
                    feeling = "very friendly"

                met_before = "you have met before" if info["met_player"] else "you haven't met before"
                npc_details.append(f"{npc} ({feeling}, {met_before})")

            npc_text = f"\nCharacters present: {', '.join(npc_details)}"

        prompt = f"""
# Game World Context
{context_text}

# Current Game State
You are in {current_location}.{npc_text}
Inventory: {inventory_text}{faction_text}{history_text}{event_text}
Game turn: {context['game_turn']}

# Player Command
{query}

# Command Success
The action {'was successful' if action_success else 'failed'}

# Task
Generate an immersive, descriptive response to the player's command. Include rich details about the current location, characters, and any relevant story elements. If the command was successful, describe the result of the action. If it failed, explain why in a way that fits the game world.

The response should be in second person perspective and should be 2-3 paragraphs long. Do not include any meta-commentary about the game mechanics or AI. Respond as if you are the game itself, not an AI assistant.
"""
        return prompt

    def _generate_rule_based(self, query: str, context: Dict, relevant_chunks: List[str], action_success: bool) -> str:
        """Generate a rule-based response (fallback when no LLM is available)."""
        current_location = context["current_location"]["name"]
        npcs_present = list(context["npcs_present"].keys())

        # Parse the query to understand command
        command_parts = query.lower().split()
        action = command_parts[0] if command_parts else ""

        # Basic response templates
        if not action_success:
            return f"You cannot do that. You are currently in {current_location}."

        # Look command
        if action in ["look", "examine", "inspect"]:
            response = f"You are in {current_location}. "

            if npcs_present:
                response += f"You can see {', '.join(npcs_present)}. "

            if context["current_location"]["items"]:
                response += f"There are some items here: {', '.join(context['current_location']['items'])}. "

            if context["current_location"]["connected_locations"]:
                response += f"You can go to: {', '.join(context['current_location']['connected_locations'])}."

            return response

        # Move command
        elif action in ["go", "move", "travel", "walk"]:
            return f"You have moved to {context['player']['location']}."

        # Talk command
        elif action in ["talk", "speak", "ask"] and len(command_parts) > 1:
            target = " ".join(command_parts[1:])
            if target in npcs_present:
                npc_info = context["npcs_present"][target]
                disposition = npc_info["disposition"]

                if disposition > 75:
                    return f"{target} greets you warmly and seems very friendly."
                elif disposition > 50:
                    return f"{target} smiles at you and seems willing to help."
                elif disposition > 25:
                    return f"{target} acknowledges you with a neutral expression."
                else:
                    return f"{target} looks at you suspiciously and seems reluctant to talk."
            else:
                return f"There's no one named {target} here."

        # Take command
        elif action in ["take", "get", "pick"] and len(command_parts) > 1:
            target = " ".join(command_parts[1:])
            return f"You have taken the {target} and added it to your inventory."

        # Default response
        else:
            # Use the first relevant chunk as context if available
            if relevant_chunks:
                return f"You {action} in {current_location}. {relevant_chunks[0][:100]}..."
            else:
                return f"You {action} in {current_location}."


class TextAdventureGame:
    """Main class for running the text adventure game."""

    def __init__(self, game_data_dir: str, model_path: str = None, llm_host: str = "localhost", llm_port: int = 8000):
        """
        Initialize the game.

        Args:
            game_data_dir: Directory containing game data files
            model_path: Path to local model file
            llm_host: Host where LLM server is running
            llm_port: Port where LLM server is running
        """
        self.game_data_dir = game_data_dir

        # Initialize LLM engine
        self.llm_engine = None
        if model_path or (llm_host and llm_port):
            self.llm_engine = LocalLLMEngine(model_path, llm_host, llm_port)

        # Initialize game state
        self.game_state = GameState(game_data_dir)

        # Initialize RAG engine
        self.rag_engine = GraphRAGEngine(game_data_dir, self.llm_engine)

        self.running = False

    def start(self):
        """Start the game."""
        self.running = True

        # Display welcome message
        print("\n" + "="*60)
        print("Welcome to the Text Adventure Game!")
        print("Type 'help' for commands or 'quit' to exit.")
        print("="*60 + "\n")

        # Show initial location
        initial_context = self.game_state.get_current_context()
        print(f"You find yourself in {initial_context['player']['location']}.")

        if initial_context['npcs_present']:
            npcs = list(initial_context['npcs_present'].keys())
            print(f"You can see: {', '.join(npcs)}.")

        print("\nWhat would you like to do?")

        # Main game loop
        while self.running:
            # Get player input
            command = input("\n> ").strip()

            # Handle special commands
            if command.lower() in ["quit", "exit"]:
                self.running = False
                print("Thanks for playing!")
                break

            elif command.lower() == "help":
                self._show_help()
                continue

            elif command.lower() == "save":
                save_path = os.path.join(self.game_data_dir, "savegame.json")
                if self.game_state.save_game(save_path):
                    print(f"Game saved to {save_path}")
                else:
                    print("Failed to save game")
                continue

            elif command.lower() == "load":
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
                continue

            elif command.lower() == "inventory":
                if self.game_state.inventory:
                    print("You are carrying:")
                    for item in self.game_state.inventory:
                        print(f"- {item}")
                else:
                    print("Your inventory is empty.")
                continue

            # Process command through the RAG engine
            response = self.rag_engine.generate_response(command, self.game_state)
            print("\n" + response)

    def _show_help(self):
        """Display help information."""
        print("\n--- COMMAND HELP ---")
        print("look: Examine your surroundings")
        print("go [location]: Move to a connected location")
        print("talk [character]: Talk to a character in your location")
        print("take [item]: Pick up an item")
        print("use [item]: Use an item in your inventory")
        print("inventory: Check your inventory")
        print("save: Save your game")
        print("load: Load a saved game")
        print("quit: Exit the game")
        print("-------------------")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a GraphRAG-based text adventure game with local LLM")
    parser.add_argument("--game_data_dir", required=True, help="Directory containing game data files")
    parser.add_argument("--model_path", help="Path to local LLM model file (optional)")
    parser.add_argument("--llm_host", default="localhost", help="Host where LLM API is running")
    parser.add_argument("--llm_port", type=int, default=8000, help="Port where LLM API is running")

    args = parser.parse_args()

    game = TextAdventureGame(args.game_data_dir, args.model_path, args.llm_host, args.llm_port)
    game.start()
