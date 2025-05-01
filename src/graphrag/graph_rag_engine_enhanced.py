import os
import networkx as nx
import pandas as pd
from typing import Dict, List, Any, Set, Optional, Tuple
import time
import re
from .graph_rag_engine import GraphRAGEngine
from .graph_rag_map_integrator import GraphRAGMapIntegrator


class GraphRAGEngineEnhanced(GraphRAGEngine):
    """Enhanced GraphRAG engine with MapArea integration."""

    def __init__(self, game_data_dir: str, llm_manager, game_state):
        """
        Initialize the enhanced GraphRAG engine.

        Args:
            game_data_dir: Directory containing game data files
            llm_manager: LLM manager for text generation
            game_state: Game state manager
        """
        # Initialize the base GraphRAG engine
        super().__init__(game_data_dir, llm_manager)

        # Store the game state reference
        self.game_state = game_state

        # Initialize the map integrator
        self.map_integrator = GraphRAGMapIntegrator(
            graph_rag_engine=self, game_state=game_state, llm_manager=llm_manager
        )

        # Generate the initial area
        print("Generating initial map area for the player's starting location...")
        initial_area = self.map_integrator.get_current_area()
        if initial_area:
            print(
                f"Initial area generated: {initial_area.name} in {initial_area.location}"
            )
            print(f"Available exits: {list(initial_area.exits.keys())}")

            # Try to add any game state NPCs to the current area if they exist
            try:
                context = self.game_state.get_current_context()
                if "npcs_present" in context:
                    print("Adding game state NPCs to the current area...")
                    for npc_name in context["npcs_present"].keys():
                        if npc_name and npc_name not in initial_area.npcs:
                            print(f"Adding NPC from game state: {npc_name}")
                            initial_area.add_npc(npc_name)
            except Exception as e:
                print(f"Error adding game state NPCs to current area: {e}")
        else:
            print("WARNING: Failed to generate initial map area")

        print("Enhanced GraphRAG engine initialized with MapArea integration")

    def retrieve_relevant_context(self, query: str, state, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant context with additional MapArea information.

        Args:
            query: The user's command/query
            state: The current game state
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant text chunks
        """
        # Get the base context from the parent class
        context_chunks = super().retrieve_relevant_context(query, state, top_k)

        # Get current area information
        current_area = self.map_integrator.get_current_area()
        if not current_area:
            return context_chunks

        # Add the current area description to the context
        area_description = f"""
You are in {current_area.name}, a specific area within {current_area.location}.
{current_area.description}

This area has the following attributes: {", ".join(current_area.attributes) if current_area.attributes else "None"}.
Items present: {", ".join(current_area.items) if current_area.items else "None"}.
Characters present: {", ".join(current_area.npcs) if current_area.npcs else "None"}.
"""

        # Add available exits information
        exits_info = "Available exits:\n"
        for direction, area_id in current_area.exits.items():
            if area_id:
                connected_area = self.map_integrator.map_manager.get_area(area_id)
                if connected_area:
                    exits_info += f"- {direction}: leads to {connected_area.name}\n"
            else:
                exits_info += f"- {direction}: unexplored area\n"

        area_description += exits_info

        # Add the area description to the context (at the beginning for emphasis)
        enhanced_context = [area_description] + context_chunks

        return enhanced_context

    def generate_response(self, query: str, state) -> str:
        """
        Generate a response with MapArea awareness.

        Args:
            query: The user's command/query
            state: The current game state

        Returns:
            Generated response
        """
        start_time = time.time()

        # Process movement commands specially to handle map generation
        command_parts = query.lower().split()
        action = command_parts[0] if command_parts else ""
        target = " ".join(command_parts[1:]) if len(command_parts) > 1 else None

        # Check if this is a movement command
        movement_verbs = ["go", "move", "travel", "walk", "run", "climb", "swim"]
        directions = [
            "north",
            "south",
            "east",
            "west",
            "up",
            "down",
            "northeast",
            "northwest",
            "southeast",
            "southwest",
            "in",
            "out",
        ]

        if action in movement_verbs and target and target.lower() in directions:
            direction = target.lower()
            success, new_area = self.map_integrator.move_player(direction)

            if success and new_area:
                # Update the game state's player location if needed
                if state.player_location != new_area.location:
                    state.player_location = new_area.location

                # Create a special response for the new area
                return self._generate_area_arrival_response(new_area)

        # Get current game context
        context = state.get_current_context()

        # Retrieve relevant text chunks
        relevant_chunks = self.retrieve_relevant_context(query, state)

        # Update game state based on command - BUT DON'T DO THIS HERE
        # The CommandProcessor should handle this - we're just checking it
        action_success = True  # Assume success for prompt construction

        # Construct the prompt
        prompt = self._construct_prompt(query, context, relevant_chunks, action_success)

        # Enhance the prompt with map information
        enhanced_prompt = self.map_integrator.enhance_prompt_with_map_info(prompt)

        # Generate response using LLM manager
        response = self.llm_manager.generate_text(enhanced_prompt)

        end_time = time.time()
        print(f"Generated response in {end_time - start_time:.2f} seconds")

        return response

    def _generate_area_arrival_response(self, area: Any) -> str:
        """
        Generate a special response for arriving at a new area.

        Args:
            area: The MapArea object for the new location

        Returns:
            A descriptive response for arriving at the area
        """
        # Create a prompt specifically for describing arrival
        prompt = f"""
# Map Area Arrival
You have just arrived at a new area in the game world. Create a detailed, atmospheric description of what the player experiences upon arrival.

## Area Details
- Area Name: {area.name}
- Location: {area.location}
- Description: {area.description}
- Special Attributes: {", ".join(area.attributes) if area.attributes else "None"}
- Items Present: {", ".join(area.items) if area.items else "None"}
- NPCs Present: {", ".join(area.npcs) if area.npcs else "None"}
- Danger Level: {area.danger_level} (0-10 scale)

## Available Exits
"""
        # Add exits information
        for direction, area_id in area.exits.items():
            if area_id:
                connected_area = self.map_integrator.map_manager.get_area(area_id)
                if connected_area:
                    prompt += f"- {direction}: leads to {connected_area.name}\n"
            else:
                prompt += f"- {direction}: unexplored path\n"

        prompt += """
## Task
Write a vivid, immersive description of the player's arrival at this area. Include:
1. Visual details of the surroundings
2. Ambient sounds, smells, and atmosphere
3. Notable features, landmarks, or objects
4. Brief mention of exits or pathways
5. Subtle hints about potential dangers or points of interest

Write in second person perspective ("You see...") and make the description 2-3 paragraphs long. Focus on creating a sense of place and atmosphere.
"""

        # Generate the arrival description
        arrival_description = self.llm_manager.generate_text(prompt)
        return arrival_description

    def save_game(self, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance save data with map information.

        Args:
            save_data: Original save data

        Returns:
            Enhanced save data
        """
        return self.map_integrator.save_game_state(save_data)

    def load_game(self, save_data: Dict[str, Any]) -> None:
        """
        Load map information from save data.

        Args:
            save_data: Save data
        """
        self.map_integrator.load_game_state(save_data)
