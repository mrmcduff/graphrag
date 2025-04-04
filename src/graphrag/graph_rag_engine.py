import os
import networkx as nx
import pandas as pd
from typing import Dict, List, Any, Set, Optional, Tuple
import time
import re


class GraphRAGEngine:
    """Class to handle retrieval-augmented generation using the knowledge graph."""

    def __init__(self, game_data_dir: str, llm_manager):
        """
        Initialize the GraphRAG engine.

        Args:
            game_data_dir: Directory containing game data files
            llm_manager: LLM manager for text generation
        """
        self.game_data_dir = game_data_dir
        self.llm_manager = llm_manager

        # Load the document chunks and knowledge graph
        self._load_data()

    def _load_data(self) -> None:
        """Load document chunks, entities, relations, and knowledge graph."""
        print("Loading GraphRAG data...")

        # Load the document chunks for retrieval
        chunks_path = os.path.join(self.game_data_dir, "document_chunks.csv")
        if os.path.exists(chunks_path):
            self.chunks_df = pd.read_csv(chunks_path)
            print(f"Loaded {len(self.chunks_df)} document chunks")
        else:
            print(f"Warning: Document chunks file not found at {chunks_path}")
            self.chunks_df = pd.DataFrame(
                columns=["filename", "chunk_id", "chunk_text"]
            )

        # Load the knowledge graph
        graph_path = os.path.join(self.game_data_dir, "knowledge_graph.gexf")
        if os.path.exists(graph_path):
            self.graph = nx.read_gexf(graph_path)
            print(
                f"Loaded knowledge graph with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges"
            )
        else:
            print(f"Warning: Knowledge graph file not found at {graph_path}")
            self.graph = nx.Graph()

        # Load entities and relations
        entities_path = os.path.join(self.game_data_dir, "entities.csv")
        if os.path.exists(entities_path):
            self.entities_df = pd.read_csv(entities_path)
            print(f"Loaded {len(self.entities_df)} entities")
        else:
            print(f"Warning: Entities file not found at {entities_path}")
            self.entities_df = pd.DataFrame(
                columns=["id", "text", "label", "source_file", "chunk_id"]
            )

        relations_path = os.path.join(self.game_data_dir, "relations.csv")
        if os.path.exists(relations_path):
            self.relations_df = pd.read_csv(relations_path)
            print(f"Loaded {len(self.relations_df)} relations")
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

    def retrieve_relevant_context(self, query: str, state, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant context from the knowledge graph and document chunks.

        Args:
            query: The user's command/query
            state: The current game state
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant text chunks
        """
        # Extract terms from query (simplified - would use NLP in production)
        query_terms = set(query.lower().split())

        # Get entities related to current location
        location_id = state.player_location.lower().replace(" ", "_")
        location_related_entities = self._get_related_entities(location_id)

        # Get entities related to NPCs in current location
        npc_related_entities = set()
        npcs_here = [
            npc
            for npc, data in state.npc_states.items()
            if data["location"] == state.player_location
        ]

        for npc in npcs_here:
            npc_id = npc.lower().replace(" ", "_")
            npc_related_entities.update(self._get_related_entities(npc_id))

        # Get entities related to world events
        event_related_entities = set()
        for event, event_data in state.world_state["world_events"].items():
            event_related_entities.add(event.lower())
            if isinstance(event_data, dict) and "data" in event_data:
                if isinstance(event_data["data"], str):
                    event_related_entities.add(event_data["data"].lower())

        # Get entities related to player inventory
        inventory_related_entities = set()
        for item in state.inventory:
            item_id = item.lower().replace(" ", "_")
            inventory_related_entities.update(self._get_related_entities(item_id))

        # Combine all search terms
        search_terms = query_terms.union(
            location_related_entities,
            npc_related_entities,
            event_related_entities,
            inventory_related_entities,
        )

        # Simple search functionality - find chunks containing the search terms
        # In a production system, this would use vector similarity or more sophisticated retrieval
        relevant_chunks = []
        scores = []

        if not self.chunks_df.empty:
            for _, row in self.chunks_df.iterrows():
                chunk_text = (
                    row["chunk_text"].lower()
                    if isinstance(row["chunk_text"], str)
                    else ""
                )
                score = sum(1 for term in search_terms if term in chunk_text)

                # Boost score for chunks that match multiple terms
                if score > 1:
                    score = score * 1.5

                # Boost score for chunks that match location or NPCs
                if state.player_location.lower() in chunk_text:
                    score += 2

                for npc in npcs_here:
                    if npc.lower() in chunk_text:
                        score += 1.5

                if score > 0:
                    relevant_chunks.append(row["chunk_text"])
                    scores.append(score)

        # Sort chunks by relevance score and take top-k
        if relevant_chunks:
            sorted_chunks = [
                x for _, x in sorted(zip(scores, relevant_chunks), reverse=True)
            ]
            return sorted_chunks[:top_k]

        # Fallback to current location description if no relevant chunks found
        return [
            f"You are in {state.player_location}. There are {len(npcs_here)} characters here."
        ]

    def _get_related_entities(self, entity_id: str) -> Set[str]:
        """
        Get entities related to a specific entity from the knowledge graph.

        Args:
            entity_id: ID of the entity

        Returns:
            Set of related entity terms
        """
        related_entities = set()

        if entity_id in self.graph.nodes:
            # Get nodes connected to entity
            for neighbor in self.graph.neighbors(entity_id):
                node_data = self.graph.nodes[neighbor]
                if "label" in node_data:
                    related_entities.add(node_data["label"].lower())

                    # Also add ID as a term (useful for matching with underscores)
                    related_entities.add(neighbor.lower())

        return related_entities

    def generate_response(self, query: str, state) -> str:
        """
        Generate a response to the user's query using the GraphRAG system.

        Args:
            query: The user's command/query
            state: The current game state

        Returns:
            Generated response
        """
        start_time = time.time()

        # Get current game context
        context = state.get_current_context()

        # Retrieve relevant text chunks
        relevant_chunks = self.retrieve_relevant_context(query, state)

        # Parse the user command (simplified)
        command_parts = query.lower().split()
        action = command_parts[0] if command_parts else ""
        target = " ".join(command_parts[1:]) if len(command_parts) > 1 else None

        # Update game state based on command - BUT DON'T DO THIS HERE
        # The CommandProcessor should handle this - we're just checking it
        action_success = True  # Assume success for prompt construction

        # Construct the prompt
        prompt = self._construct_prompt(query, context, relevant_chunks, action_success)

        # Generate response using LLM manager
        response = self.llm_manager.generate_text(prompt)

        end_time = time.time()
        print(f"Generated response in {end_time - start_time:.2f} seconds")

        return response

    def _construct_prompt(
        self,
        query: str,
        context: Dict,
        relevant_chunks: List[str],
        action_success: bool,
    ) -> str:
        """
        Construct a prompt for the language model.

        Args:
            query: The user's command/query
            context: The current game context
            relevant_chunks: Relevant document chunks
            action_success: Whether the action was successful

        Returns:
            Constructed prompt string
        """
        current_location = context["current_location"]["name"]
        npcs_present = list(context["npcs_present"].keys())

        # Combine relevant chunks into context text (limit to avoid token issues)
        context_text = "\n\n".join(relevant_chunks)

        # Truncate if too long (simple token estimation)
        if len(context_text) > 2000:
            context_text = context_text[:2000] + "..."

        # Format player inventory
        inventory_text = (
            ", ".join(context["player"]["inventory"])
            if context["player"]["inventory"]
            else "Nothing"
        )

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

        # Format player history (limit to avoid token issues)
        history_text = ""
        if (
            "significant_actions" in context["player"]
            and context["player"]["significant_actions"]
        ):
            actions = context["player"]["significant_actions"][
                -5:
            ]  # Only last 5 actions
            history_text = "\nRecent significant actions:\n- " + "\n- ".join(actions)

        # Format world events
        event_text = ""
        if context["world_events"]:
            events = []
            for event, data in list(context["world_events"].items())[
                :3
            ]:  # Limit to 3 events
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

                met_before = (
                    "you have met before"
                    if info["met_player"]
                    else "you haven't met before"
                )
                npc_details.append(f"{npc} ({feeling}, {met_before})")

            npc_text = f"\nCharacters present: {', '.join(npc_details)}"

        prompt = f"""
# Game World Context
{context_text}

# Current Game State
You are in {current_location}.{npc_text}
Inventory: {inventory_text}{faction_text}{history_text}{event_text}
Game turn: {context["game_turn"]}

# Player Command
{query}

# Task
Generate an immersive, descriptive response to the player's command. Include rich details about the current location, characters, and any relevant story elements. If the command was successful, describe the result of the action. If it failed, explain why in a way that fits the game world.

The response should be in second person perspective and should be 2-3 paragraphs long. Do not include any meta-commentary about the game mechanics or AI. Respond as if you are the game itself, not an AI assistant.
"""
        return prompt
