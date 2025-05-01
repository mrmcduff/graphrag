from typing import Dict, List, Optional, Set, Any, Tuple
import os
import json
import sys

# Fix imports to work with both direct and relative import paths
try:
    # Try relative imports first
    from ..gamestate.map_area import MapArea
    from ..gamestate.map_manager import MapManager
    from .map_generator_ai import MapGeneratorAI
except (ImportError, ValueError):
    # Fall back to absolute imports
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )
    from src.gamestate.map_area import MapArea
    from src.gamestate.map_manager import MapManager
    from src.graphrag.map_generator_ai import MapGeneratorAI


class GraphRAGMapIntegrator:
    """
    Integrates the MapArea system with the GraphRAG engine.

    This class acts as a bridge between the existing GraphRAG engine and the
    new MapArea system, allowing for dynamic generation and management of
    map areas while maintaining compatibility with the existing codebase.
    """

    def __init__(self, graph_rag_engine, game_state, llm_manager):
        """
        Initialize the map integrator.

        Args:
            graph_rag_engine: The GraphRAG engine instance
            game_state: The game state instance
            llm_manager: The LLM manager for text generation
        """
        self.graph_rag_engine = graph_rag_engine
        self.game_state = game_state
        self.llm_manager = llm_manager
        
        # Set default values first
        self.verbose = False
        self.generation_depth = 2
        self.current_area_id = None
        self.area_cache = {}

        # Create the map generator
        self.map_generator = MapGeneratorAI(
            game_data_dir=self.game_state.game_data_dir,
            graph=self.game_state.graph,
            llm_manager=self.llm_manager,
            output_dir=self.game_state.game_data_dir,
            verbose=self.verbose
        )

        # Get the map manager from the generator
        self.map_manager = self.map_generator.map_manager
        
        # Try to load existing map data
        self._load_or_initialize_maps()

    def _load_or_initialize_maps(self) -> None:
        """Load existing map data or initialize if none exists."""
        # Try to load existing map data
        if not self.map_generator.load_maps(self.verbose):
            if self.verbose:
                print("No existing map data found. Maps will be generated on demand.")

    def get_or_generate_area(self, location_name: str) -> Optional[MapArea]:
        """
        Get an existing area or generate a new one for a location.

        Args:
            location_name: Name of the location

        Returns:
            A MapArea object if available or creatable, None otherwise
        """
        # Check if we already have areas for this location
        existing_areas = self.map_manager.get_areas_by_location(location_name)

        if existing_areas:
            # If we have areas for this location, return the first one
            area_id = existing_areas[0].location_id
            self.current_area_id = area_id
            self.map_manager.set_current_area(area_id)
            return existing_areas[0]

        # Generate an initial area for this location along with connected areas
        area_id = self.map_generator.generate_initial_area(
            location_name, generation_depth=self.generation_depth, verbose=self.verbose
        )

        if area_id:
            self.current_area_id = area_id
            self.map_manager.set_current_area(area_id)
            return self.map_manager.get_area(area_id)

        return None

    def move_player(self, direction: str) -> Tuple[bool, Optional[MapArea]]:
        """
        Move the player in a specified direction, generating new areas if needed.

        Args:
            direction: Direction to move (north, south, east, etc.)

        Returns:
            Tuple of (success, new_area)
        """
        if not self.current_area_id:
            # If no current area, we need to generate one based on player location
            current_area = self.get_or_generate_area(self.game_state.player_location)
            if not current_area:
                return False, None

        current_area = self.map_manager.get_area(self.current_area_id)

        # Debug information
        if self.verbose:
            print(
                f"DEBUG: Current area: {current_area.name} ({current_area.location_id})"
            )
            print(f"DEBUG: Attempting to move {direction}")
            print(f"DEBUG: Available exits: {current_area.exits}")

        # Check if there's an exit in this direction
        if direction in current_area.exits and current_area.exits[direction]:
            # If there's an existing exit, move there
            target_id = current_area.exits[direction]
            target_area = self.map_manager.get_area(target_id)

            if target_area:
                if self.verbose:
                    print(
                        f"DEBUG: Found existing exit to {target_area.name} ({target_id})"
                    )
                self.map_manager.set_current_area(target_id)
                self.current_area_id = target_id
                target_area.mark_visited()
                return True, target_area
            else:
                if self.verbose:
                    print(f"DEBUG: Exit leads to unknown area ID: {target_id}")

        # Either no exit in this direction or target area not found
        # Generate a new area or fix the connection
        if self.verbose:
            print(f"Generating new area in direction {direction}...")
        new_area_id = self.map_generator.generate_connected_area(
            self.current_area_id, direction, self.verbose
        )

        if new_area_id:
            self.map_manager.set_current_area(new_area_id)
            self.current_area_id = new_area_id
            new_area = self.map_manager.get_area(new_area_id)

            # Ensure bidirectional connections are set up correctly
            reverse_direction = self.map_generator._get_reverse_direction(direction)
            if reverse_direction != "unknown":
                if self.verbose:
                    print(
                        f"DEBUG: Setting up bidirectional connection: {direction} <-> {reverse_direction}"
                    )
                self.map_manager.create_bidirectional_exit(
                    current_area.location_id, new_area_id, direction, reverse_direction
                )

            return True, new_area

        return False, None

    def get_current_area(self) -> Optional[MapArea]:
        """Get the current MapArea if any."""
        if self.verbose:
            print(
                f"DEBUG: get_current_area called, current_area_id: {self.current_area_id}"
            )

        if self.current_area_id:
            area = self.map_manager.get_area(self.current_area_id)
            if area:
                if self.verbose:
                    print(f"DEBUG: Found current area: {area.name} in {area.location}")
                    print(f"DEBUG: Area exits: {list(area.exits.keys())}")
                return area
            else:
                if self.verbose:
                    print(f"DEBUG: Couldn't find area with ID {self.current_area_id}")

        # Try to generate an area based on player location
        if self.verbose:
            print(
                f"DEBUG: Trying to generate area for {self.game_state.player_location}"
            )

        # Use current verbose setting for area generation
        area = self.get_or_generate_area(self.game_state.player_location)

        if area:
            if self.verbose:
                print(
                    f"DEBUG: Generated area: {area.name} with exits: {list(area.exits.keys())}"
                )
        else:
            if self.verbose:
                print("⚠️ WARNING: Failed to generate map area")

        return area

    def get_surroundings(self) -> Dict[str, Optional[MapArea]]:
        """
        Get the current area and all adjacent areas.

        Returns:
            Dictionary mapping directions to areas
        """
        surroundings = {}
        current_area = self.get_current_area()

        if not current_area:
            return surroundings

        # Add current area
        surroundings["here"] = current_area

        # Add connected areas
        for direction, area_id in current_area.exits.items():
            if area_id:
                surroundings[direction] = self.map_manager.get_area(area_id)
            else:
                surroundings[direction] = None

        return surroundings

    def enhance_prompt_with_map_info(self, prompt: str) -> str:
        """
        Enhance a standard GraphRAG prompt with map area information.

        Args:
            prompt: Original prompt

        Returns:
            Enhanced prompt with map information
        """
        current_area = self.get_current_area()
        if not current_area:
            return prompt

        surroundings = self.get_surroundings()

        # Build map information section
        map_info = f"""
# Map Area Information
You are currently in {current_area.name}, a specific area within {current_area.location}.

## Current Area Details
- Description: {current_area.description}
- Coordinates: {current_area.coordinates}
- Special Attributes: {", ".join(current_area.attributes) if current_area.attributes else "None"}
- Items Present: {", ".join(current_area.items) if current_area.items else "None"}
- NPCs Present: {", ".join(current_area.npcs) if current_area.npcs else "None"}
- Danger Level: {current_area.danger_level} (0-10 scale)

## Exits and Connected Areas
"""

        # Add connected areas information
        for direction, area in surroundings.items():
            if direction != "here" and area:
                map_info += f"- {direction.capitalize()}: {area.name} ({area.description[:50]}...)\n"
            elif direction != "here":
                map_info += (
                    f"- {direction.capitalize()}: Unknown area (not yet explored)\n"
                )

        # Insert map information before the task section
        if "# Task" in prompt:
            parts = prompt.split("# Task")
            enhanced_prompt = parts[0] + map_info + "\n# Task" + parts[1]
            return enhanced_prompt
        else:
            return prompt + "\n" + map_info

    def save_game_state(self, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate map data into game save data.

        Args:
            save_data: The original save data

        Returns:
            Enhanced save data with map information
        """
        # Save the map data
        self.map_generator._save_maps()

        # Add current area ID to save data
        save_data["current_map_area_id"] = self.current_area_id

        return save_data

    def load_game_state(self, save_data: Dict[str, Any]) -> None:
        """
        Load map data from game save data.

        Args:
            save_data: The save data
        """
        # Load the map data
        self.map_generator.load_maps()

        # Restore current area
        if "current_map_area_id" in save_data:
            self.current_area_id = save_data["current_map_area_id"]
            if self.current_area_id:
                self.map_manager.set_current_area(self.current_area_id)
