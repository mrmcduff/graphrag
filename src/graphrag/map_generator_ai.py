import os
import sys
import json
from typing import Dict, List, Optional, Set, Any
import networkx as nx
import pandas as pd

# Fix imports to work with both direct and relative import paths
try:
    # Try relative imports first
    from ..gamestate.map_area import MapArea
    from ..gamestate.map_manager import MapManager
except (ImportError, ValueError):
    # Fall back to absolute imports
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )
    from src.gamestate.map_area import MapArea
    from src.gamestate.map_manager import MapManager


class MapGeneratorAI:
    """
    Generates MapArea objects from the knowledge graph using the LLM.

    This class is responsible for creating MapArea objects that represent
    specific points in the game world. It uses the knowledge graph and LLM
    to generate rich, detailed areas with appropriate attributes and connections.
    """

    def __init__(
        self, game_data_dir: str, graph: nx.Graph, llm_manager, output_dir: str = None
    ):
        """
        Initialize the map generator.

        Args:
            game_data_dir: Directory containing game data files
            graph: Knowledge graph of the game world
            llm_manager: LLM manager for text generation
            output_dir: Directory to save generated map data (defaults to game_data_dir)
        """
        self.game_data_dir = game_data_dir
        self.graph = graph
        self.llm_manager = llm_manager
        self.output_dir = output_dir or game_data_dir

        # Create map manager to store generated areas
        self.map_manager = MapManager(self.output_dir)

        # Load entity and relation information if available
        self.entities_df = self._load_entities()
        self.relations_df = self._load_relations()

        # Track which locations have been generated
        self.generated_locations = set()

        # Ensure output directory exists
        self.maps_dir = os.path.join(self.output_dir, "maps")
        os.makedirs(self.maps_dir, exist_ok=True)
        print(f"Map data will be stored in: {self.maps_dir}")

    def _load_entities(self) -> pd.DataFrame:
        """Load entities from CSV file."""
        entities_path = os.path.join(self.game_data_dir, "entities.csv")
        if os.path.exists(entities_path):
            return pd.read_csv(entities_path)
        return pd.DataFrame(columns=["id", "text", "label", "source_file", "chunk_id"])

    def _load_relations(self) -> pd.DataFrame:
        """Load relations from CSV file."""
        relations_path = os.path.join(self.game_data_dir, "relations.csv")
        if os.path.exists(relations_path):
            return pd.read_csv(relations_path)
        return pd.DataFrame(
            columns=[
                "subject",
                "predicate",
                "object",
                "sentence",
                "source_file",
                "chunk_id",
            ]
        )

    def generate_initial_area(
        self, location_name: str, generation_depth: int = 2, verbose: bool = False
    ) -> Optional[str]:
        """
        Generate the initial MapArea for a location and its connected areas.

        Args:
            location_name: Name of the location to generate the initial area for
            generation_depth: How many layers of connected areas to generate (default=2)
                              0 = just the starting area
                              1 = starting area + directly connected areas
                              2 = starting area + direct connections + one more layer
            verbose: Whether to print detailed progress messages

        Returns:
            The location_id of the generated area if successful, None otherwise
        """
        # If we've already generated this location, just return its main area
        if location_name.lower() in self.generated_locations:
            # Find the main area for this location
            for area_id, area in self.map_manager.areas.items():
                if (
                    area.location.lower() == location_name.lower()
                    and area.is_region_entrance
                ):
                    return area_id

            # If no entrance is found, just return the first area in this location
            for area_id, area in self.map_manager.areas.items():
                if area.location.lower() == location_name.lower():
                    return area_id

            return None

        # Mark this location as generated
        self.generated_locations.add(location_name.lower())

        # Show simple progress indicator
        if not verbose:
            print(f"🌍 Generating map for {location_name}...")
        else:
            print(
                f"Starting map generation for {location_name} with depth {generation_depth}"
            )

        # Get information about the location from the knowledge graph
        location_info = self._get_location_info(location_name)

        # Generate a prompt for the LLM to create the initial area
        prompt = self._create_initial_area_prompt(location_name, location_info)

        try:
            # Generate the area description using the LLM
            ai_response = self.llm_manager.generate_text(prompt)

            # Parse the AI response to create a MapArea
            main_area = self._parse_area_from_ai_response(ai_response, location_name)

            if main_area:
                # Mark this as the region entrance
                main_area.is_region_entrance = True

                # Add the area to the map manager
                self.map_manager.add_area(main_area)

                # Generate connected areas recursively up to the specified depth
                if generation_depth > 0:
                    self._generate_connected_areas(
                        main_area.location_id, generation_depth, verbose
                    )

                # Save the generated areas
                self._save_maps(verbose)

                if not verbose:
                    print("✅ Map generation complete!")

                return main_area.location_id
        except Exception as e:
            print(f"Error generating initial area for {location_name}: {e}")

        return None

    def _generate_connected_areas(
        self, area_id: str, depth: int, verbose: bool = False
    ) -> None:
        """
        Recursively generate connected areas up to the specified depth.

        Args:
            area_id: ID of the area to generate connections for
            depth: Remaining depth to generate (decrements with each recursion)
            verbose: Whether to print detailed progress messages
        """
        if depth <= 0:
            return

        # Get the area
        area = self.map_manager.get_area(area_id)
        if not area:
            print(
                f"⚠️ Cannot generate connected areas: area with ID {area_id} not found"
            )
            return

        if verbose:
            print(
                f"Generating connected areas for {area.name} in {area.location} (depth {depth})"
            )
        else:
            # Simple progress indicator
            print(f"🗺️ Creating map network... {depth * 25}%")

        # Use standard directions to ensure consistency
        standard_directions = ["north", "south", "east", "west", "up", "down"]

        # Make a copy of exits to avoid modification during iteration
        exit_directions = list(area.exits.keys())
        if not exit_directions:
            if verbose:
                print(f"⚠️ No exits defined for {area.name}, using standard directions")
            exit_directions = standard_directions

        # Generate areas for each exit direction
        for direction in exit_directions:
            # Check if the exit already points to a valid area
            has_valid_exit = False
            if direction in area.exits and area.exits[direction]:
                target_id = area.exits[direction]
                target_area = self.map_manager.get_area(target_id)
                if target_area:
                    if verbose:
                        print(
                            f"  ✓ Exit {direction} already points to {target_area.name} ({target_id})"
                        )
                    has_valid_exit = True

                    # Ensure the reverse connection is also set up
                    reverse_direction = self._get_reverse_direction(direction)
                    if reverse_direction != "unknown":
                        if (
                            reverse_direction not in target_area.exits
                            or not target_area.exits[reverse_direction]
                        ):
                            if verbose:
                                print(
                                    f"  ⚠️ Fixing missing reverse connection from {target_area.name} back to {area.name}"
                                )
                            target_area.add_exit(reverse_direction, area_id)

                    # If we have a valid exit and we're still at depth > 1, recursively generate for the target
                    if depth > 1:
                        self._generate_connected_areas(target_id, depth - 1, verbose)

            # If no valid exit exists in this direction, generate a new area
            if not has_valid_exit:
                if verbose:
                    print(f"  Generating new area to the {direction} of {area.name}...")
                new_area_id = self.generate_connected_area(area_id, direction, verbose)

                if new_area_id and depth > 1:
                    # Recursively generate connections from the new area with one less depth
                    self._generate_connected_areas(new_area_id, depth - 1, verbose)

        if verbose:
            print(f"✅ Finished generating connected areas for {area.name}")

        # Always save after generating a set of areas
        self._save_maps(verbose)

    def generate_connected_area(
        self, from_area_id: str, direction: str, verbose: bool = False
    ) -> Optional[str]:
        """
        Generate a new area connected to an existing one.

        Args:
            from_area_id: ID of the existing area
            direction: Direction from the existing area to the new one
            verbose: Whether to print detailed progress messages

        Returns:
            The location_id of the generated area if successful, None otherwise
        """
        # Get the existing area
        from_area = self.map_manager.get_area(from_area_id)
        if not from_area:
            if verbose:
                print(f"Error: Cannot find source area with ID {from_area_id}")
            return None

        # Check if there's already an exit in this direction
        if direction in from_area.exits and from_area.exits[direction]:
            # Return the existing exit's target if it exists
            target_id = from_area.exits[direction]
            if verbose:
                print(
                    f"⚙️ Using existing exit from {from_area.name} {direction} to {target_id}"
                )
            return target_id

        # Generate a prompt for the LLM to create the connected area
        location_info = self._get_location_info(from_area.location)
        prompt = self._create_connected_area_prompt(from_area, direction, location_info)

        try:
            # Generate the area description using the LLM
            if verbose:
                print(f"⚙️ Generating new area {direction} of {from_area.name}...")
            ai_response = self.llm_manager.generate_text(prompt)

            # Parse the AI response to create a MapArea
            new_area = self._parse_area_from_ai_response(
                ai_response, from_area.location
            )

            if new_area:
                # Add the area to the map manager
                self.map_manager.add_area(new_area)

                # Connect the areas (figure out reverse direction)
                reverse_direction = self._get_reverse_direction(direction)

                # Make sure the new area's exits include the reverse direction back to the origin
                if reverse_direction != "unknown":
                    if verbose:
                        print(
                            f"⚙️ Setting bidirectional connection between {from_area.name} and {new_area.name}"
                        )
                        print(f"⚙️ From {from_area.name} {direction} → {new_area.name}")
                        print(
                            f"⚙️ From {new_area.name} {reverse_direction} → {from_area.name}"
                        )

                    # Manually set up the exits in both areas
                    from_area.add_exit(direction, new_area.location_id)
                    new_area.add_exit(reverse_direction, from_area.location_id)

                    # Also use the map manager for extra safety
                    self.map_manager.create_bidirectional_exit(
                        from_area_id, new_area.location_id, direction, reverse_direction
                    )

                # Save the generated areas
                self._save_maps(verbose)

                return new_area.location_id
        except Exception as e:
            if verbose:
                print(
                    f"Error generating connected area from {from_area_id} in direction {direction}: {e}"
                )

        return None

    def _get_location_info(self, location_name: str) -> Dict[str, Any]:
        """
        Get information about a location from the knowledge graph.

        Args:
            location_name: Name of the location

        Returns:
            Dictionary with location information
        """
        location_id = location_name.lower().replace(" ", "_")

        # Information to collect
        info = {
            "name": location_name,
            "description": "",
            "connected_locations": [],
            "characters": [],
            "items": [],
            "attributes": [],
        }

        # Get node attributes if present
        if location_id in self.graph.nodes:
            node_data = self.graph.nodes[location_id]
            if "description" in node_data:
                info["description"] = node_data["description"]

        # Get connected locations
        if location_id in self.graph.nodes:
            for neighbor in self.graph.neighbors(location_id):
                if "label" in self.graph.nodes[neighbor]:
                    neighbor_label = self.graph.nodes[neighbor]["label"]
                    # Only add if it's a location, not a character or item
                    location_labels = [
                        "location",
                        "place",
                        "area",
                        "region",
                        "dungeon",
                        "city",
                        "town",
                    ]
                    if any(
                        label
                        in self.graph.nodes[neighbor].get("entity_type", "").lower()
                        for label in location_labels
                    ):
                        info["connected_locations"].append(neighbor_label)

        # Get characters associated with this location
        if not self.relations_df.empty:
            character_relations = self.relations_df.loc[
                (self.relations_df["object"] == location_name.lower())
                & (
                    self.relations_df["predicate"].isin(
                        ["located_in", "lives_in", "found_in"]
                    )
                )
            ]
            info["characters"] = character_relations["subject"].tolist()

        # Get items associated with this location
        item_relations = self.relations_df.loc[
            (self.relations_df["object"] == location_name.lower())
            & (
                self.relations_df["predicate"].isin(
                    ["located_in", "found_in", "stored_in"]
                )
            )
        ]
        info["items"] = item_relations["subject"].tolist()

        # Get attributes (look for specific relations or properties)
        attribute_relations = self.relations_df.loc[
            (self.relations_df["subject"] == location_name.lower())
            & (
                self.relations_df["predicate"].isin(
                    ["has_attribute", "is", "has_property"]
                )
            )
        ]
        if not attribute_relations.empty:
            info["attributes"] = attribute_relations["object"].tolist()

        return info

    def _create_initial_area_prompt(
        self, location_name: str, location_info: Dict[str, Any]
    ) -> str:
        """
        Create a prompt for generating the initial area of a location.

        Args:
            location_name: Name of the location
            location_info: Information about the location

        Returns:
            Prompt for the LLM
        """
        description = location_info.get("description", "")
        connected_locations = location_info.get("connected_locations", [])
        characters = location_info.get("characters", [])
        items = location_info.get("items", [])
        attributes = location_info.get("attributes", [])

        connected_str = (
            ", ".join(connected_locations) if connected_locations else "none known"
        )
        characters_str = ", ".join(characters) if characters else "none known"
        items_str = ", ".join(items) if items else "none known"
        attributes_str = ", ".join(attributes) if attributes else "none known"

        prompt = f"""
# Task: Generate a Detailed Map Area

You are creating a detailed 'MapArea' object that represents the entrance or main area of {location_name} for a text adventure game.

## Background Information
- Location Name: {location_name}
- Description: {description}
- Connected Locations: {connected_str}
- Characters: {characters_str}
- Items: {items_str}
- Known Attributes: {attributes_str}

## Requirements
Create a detailed MapArea object with the following information:
1. A unique location_id (use lowercase with underscores)
2. A name for this specific area (e.g., "Entrance", "Main Hall", "Central Square")
3. A sub-location name that represents a distinct area within {location_name} (e.g., "Market District", "Northern Woods", "Ground Floor")
4. Coordinates as (x, y, level) where level can indicate elevation (use 0,0,0 for this initial area)
5. A rich description of what the player sees in this area
6. Special attributes of this area (e.g., "dark", "underwater", "elevated", "magical", "dangerous")
7. Important items that can be found here (3-5 items)
8. NPCs present in this area (1-3 characters)
9. A danger level from 0-10 (0 being completely safe, 10 being extremely dangerous)

## Output Format
Return your answer in a JSON format with the following structure:
```json
{{
  "location_id": "unique_id_here",
  "name": "Name of this specific area",
  "location": "{location_name}",
  "sub_location": "Distinct area within the location",
  "coordinates": [0, 0, 0],
  "description": "Detailed description of what the player sees...",
  "attributes": ["attribute1", "attribute2"],
  "items": ["item1", "item2", "item3"],
  "npcs": ["character1", "character2"],
  "danger_level": 3,
  "exits": {{"direction1": null, "direction2": null}}
}}
```

- The "exits" field should include at least 4-6 potential directions (north, south, east, west, up, down), with null values since we haven't generated those areas yet.
- Make the description vivid and atmospheric, about 3-4 sentences long.
- Be creative but consistent with the world information provided.
- Create objects and details that make sense for this location.
- Include environmental details and sensory information.
- The sub_location should represent a distinct, logically consistent area within the broader location that could contain multiple connected areas.

Return ONLY the JSON without any additional explanation.
"""
        return prompt

    def _create_connected_area_prompt(
        self, from_area: MapArea, direction: str, location_info: Dict[str, Any]
    ) -> str:
        """
        Create a prompt for generating an area connected to an existing one.

        Args:
            from_area: The existing area
            direction: Direction from the existing area to the new one
            location_info: Information about the location

        Returns:
            Prompt for the LLM
        """
        # Calculate new coordinates based on direction
        new_coords = list(from_area.coordinates)
        if direction == "north":
            new_coords[1] += 1
        elif direction == "south":
            new_coords[1] -= 1
        elif direction == "east":
            new_coords[0] += 1
        elif direction == "west":
            new_coords[0] -= 1
        elif direction == "up":
            new_coords[2] += 1
        elif direction == "down":
            new_coords[2] -= 1

        reverse_direction = self._get_reverse_direction(direction)

        prompt = f"""
# Task: Generate a Connected Map Area

You are creating a detailed 'MapArea' object for a text adventure game. This area is connected to an existing area.

## Current Area Information
- Location: {from_area.location}
- Area Name: {from_area.name}
- Sub-location: {from_area.sub_location or "None"}
- Description: {from_area.description}
- Coordinates: {from_area.coordinates}
- Attributes: {list(from_area.attributes)}

## Connection Information
- Direction from current area: {direction}
- This new area is {direction} of the current area.
- New coordinates: {new_coords}

## Requirements
Create a detailed MapArea object with the following information:
1. A unique location_id (use lowercase with underscores)
2. A name for this specific area that makes sense given its direction from the current area
3. A sub-location that is either the same as the current area's sub-location (if they're part of the same district/region) or a new one if appropriate
4. Coordinates as provided above
5. A rich description of what the player sees in this area
6. Special attributes of this area (which may be similar or different from the original area)
7. Important items that can be found here (2-4 items)
8. NPCs present in this area (0-2 characters)
9. A danger level from 0-10 (0 being completely safe, 10 being extremely dangerous)

## Output Format
Return your answer in a JSON format with the following structure:
```json
{{
  "location_id": "unique_id_here",
  "name": "Name of this specific area",
  "location": "{from_area.location}",
  "sub_location": "District or section name (often the same as the connected area)",
  "coordinates": {new_coords},
  "description": "Detailed description of what the player sees...",
  "attributes": ["attribute1", "attribute2"],
  "items": ["item1", "item2", "item3"],
  "npcs": ["character1", "character2"],
  "danger_level": 3,
  "exits": {{"{reverse_direction}": "{from_area.location_id}"}}
}}
```

- The "exits" field must include the reverse direction ({reverse_direction}) pointing back to the original area.
- Add 3-4 additional exits in different directions with null values.
- Make the description vivid and atmospheric, about 3-4 sentences long.
- Be creative but consistent with the world and the existing area.
- The new area should make logical sense given its direction from the current area.
- Include environmental details and sensory information.
- If this area is in the same sub-location as the original area, keep that consistent. If it's a transition to a new sub-location, reflect that in the name and description.

Return ONLY the JSON without any additional explanation.
"""
        return prompt

    def _parse_area_from_ai_response(
        self, ai_response: str, location_name: str
    ) -> Optional[MapArea]:
        """
        Parse the AI response to create a MapArea object.

        Args:
            ai_response: The response from the LLM
            location_name: The name of the location

        Returns:
            A MapArea object if parsing is successful, None otherwise
        """
        try:
            # Extract the JSON object from the response
            # First, try to find a JSON block
            json_match = None
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                if json_end > json_start:
                    json_match = ai_response[json_start:json_end].strip()

            # If no JSON block, try to parse the whole response
            if not json_match:
                json_match = ai_response.strip()

            # Parse the JSON
            area_data = json.loads(json_match)

            # Ensure the location matches
            area_data["location"] = location_name

            # Convert coordinates to tuple if needed
            if isinstance(area_data["coordinates"], list):
                area_data["coordinates"] = tuple(area_data["coordinates"])

            # Convert attributes to set if needed
            if isinstance(area_data["attributes"], list):
                area_data["attributes"] = set(area_data["attributes"])

            # Extract NPCs from the description if they're mentioned but not in the npcs list
            if "description" in area_data and "npcs" in area_data:
                description = area_data["description"].lower()
                keywords = [
                    "guide",
                    "hermit",
                    "merchant",
                    "traveler",
                    "warrior",
                    "mage",
                    "wizard",
                    "keeper",
                    "guard",
                    "soldier",
                    "villager",
                    "hunter",
                    "gatherer",
                    "shaman",
                    "priest",
                    "elder",
                ]

                for keyword in keywords:
                    if keyword in description and keyword not in [
                        npc.lower() for npc in area_data["npcs"]
                    ]:
                        # Add the NPC with proper capitalization based on how it appears in description
                        idx = description.find(keyword)
                        if idx >= 0:
                            # Extract the full name using surrounding context
                            start = max(0, idx - 20)
                            end = min(len(description), idx + 20)
                            context = description[start:end]

                            # Try to extract the name with an adjective
                            import re

                            npc_match = re.search(
                                r"(?:\ba\s+|\bthe\s+)?(\w+\s+" + keyword + ")", context
                            )
                            if npc_match:
                                npc_name = npc_match.group(1)
                                # Capitalize properly
                                npc_name = " ".join(
                                    word.capitalize() for word in npc_name.split()
                                )
                                area_data["npcs"].append(npc_name)
                            else:
                                # Just add the keyword with capitalization
                                area_data["npcs"].append(keyword.capitalize())

            # Create the MapArea object
            return MapArea.from_dict(area_data)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            print(f"Response: {ai_response}")
            return None

    def _get_reverse_direction(self, direction: str) -> str:
        """
        Get the reverse of a direction.

        Args:
            direction: The direction to reverse

        Returns:
            The reverse direction
        """
        direction_pairs = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
            "up": "down",
            "down": "up",
            "northeast": "southwest",
            "northwest": "southeast",
            "southeast": "northwest",
            "southwest": "northeast",
            "in": "out",
            "out": "in",
        }

        return direction_pairs.get(direction.lower(), "unknown")

    def _save_maps(self, verbose: bool = False) -> bool:
        """
        Save all generated map areas to a file.

        Args:
            verbose: Whether to print detailed progress messages

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create maps path
            map_file = os.path.join(self.maps_dir, "map_data.json")
            if verbose:
                print(f"Saving map data to {map_file}")

            # Save the map data
            return self.map_manager.save_map(map_file)
        except Exception as e:
            print(f"Error saving map areas: {e}")
            return False

    def load_maps(self) -> bool:
        """
        Load generated map areas from a file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Look for map data in the maps directory
            map_file = os.path.join(self.maps_dir, "map_data.json")
            print(f"Looking for map data at {map_file}")

            if not os.path.exists(map_file):
                print(f"No map data found at {map_file}")
                return False

            success = self.map_manager.load_map(map_file)

            # Update the set of generated locations
            if success:
                self.generated_locations = set()
                for area in self.map_manager.areas.values():
                    self.generated_locations.add(area.location.lower())
                print(f"Successfully loaded {len(self.map_manager.areas)} map areas")

            return success
        except Exception as e:
            print(f"Error loading map areas: {e}")
            return False
