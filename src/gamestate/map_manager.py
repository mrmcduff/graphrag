import os
import json
from typing import Dict, List, Optional, Set, Any
from .map_area import MapArea


class MapManager:
    """
    Manages the game world's map areas and navigation.

    This class is responsible for loading, saving, and managing MapArea objects
    that represent the game world. It provides methods for finding areas,
    creating connections between areas, and handling player movement.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the map manager.

        Args:
            data_dir: Directory for loading/saving map data
        """
        self.areas: Dict[str, MapArea] = {}
        self.data_dir = data_dir
        self.current_area_id: Optional[str] = None

    def add_area(self, area: MapArea) -> None:
        """
        Add a new area to the map.

        Args:
            area: The MapArea to add
        """
        self.areas[area.location_id] = area

    def get_area(self, area_id: str) -> Optional[MapArea]:
        """
        Retrieve an area by its ID.

        Args:
            area_id: The ID of the area to retrieve

        Returns:
            The MapArea if found, None otherwise
        """
        return self.areas.get(area_id)

    def create_bidirectional_exit(
        self, from_id: str, to_id: str, from_direction: str, to_direction: str
    ) -> bool:
        """
        Create exits connecting two areas in both directions.

        Args:
            from_id: ID of the first area
            to_id: ID of the second area
            from_direction: Direction from first area to second (e.g., "north")
            to_direction: Direction from second area to first (e.g., "south")

        Returns:
            True if successful, False if either area doesn't exist
        """
        from_area = self.get_area(from_id)
        to_area = self.get_area(to_id)

        if not from_area or not to_area:
            return False

        from_area.add_exit(from_direction, to_id)
        to_area.add_exit(to_direction, from_id)
        return True

    def move_player(self, direction: str) -> Optional[MapArea]:
        """
        Move the player in the specified direction if possible.

        Args:
            direction: Direction to move (north, south, east, west, etc.)

        Returns:
            The new MapArea if move was successful, None otherwise
        """
        if not self.current_area_id:
            return None

        current_area = self.areas[self.current_area_id]

        if direction not in current_area.exits:
            return None

        # Get the target area ID
        target_id = current_area.exits[direction]
        target_area = self.areas.get(target_id)

        if not target_area:
            return None

        # Check if the area requires an item
        # Note: Actual item validation would be handled by the game state

        # Update current area and mark as visited
        self.current_area_id = target_id
        target_area.mark_visited()

        return target_area

    def get_current_area(self) -> Optional[MapArea]:
        """
        Get the player's current area.

        Returns:
            The current MapArea if set, None otherwise
        """
        if self.current_area_id:
            return self.areas.get(self.current_area_id)
        return None

    def set_current_area(self, area_id: str) -> bool:
        """
        Set the player's current area.

        Args:
            area_id: ID of the area to set as current

        Returns:
            True if successful, False if area doesn't exist
        """
        if area_id in self.areas:
            self.current_area_id = area_id
            self.areas[area_id].mark_visited()
            return True
        return False

    def get_areas_by_location(self, location: str) -> List[MapArea]:
        """
        Get all map areas in a specific location.

        Args:
            location: The location to filter by (e.g., "Mountain", "Castle")

        Returns:
            List of MapAreas in the specified location
        """
        return [area for area in self.areas.values() if area.location == location]

    def get_areas_with_attribute(self, attribute: str) -> List[MapArea]:
        """
        Get all map areas with a specific attribute.

        Args:
            attribute: The attribute to filter by (e.g., "underwater")

        Returns:
            List of MapAreas with the specified attribute
        """
        return [area for area in self.areas.values() if attribute in area.attributes]

    def save_map(self, filename: str = "map_data.json") -> bool:
        """
        Save the map data to a file.

        Args:
            filename: Name of the file to save to

        Returns:
            True if successful, False otherwise
        """
        if not self.data_dir:
            return False

        try:
            path = os.path.join(self.data_dir, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Create a serializable dictionary of all areas
            map_data = {
                "areas": {
                    area_id: area.to_dict() for area_id, area in self.areas.items()
                },
                "current_area_id": self.current_area_id,
            }

            with open(path, "w") as f:
                json.dump(map_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving map: {e}")
            return False

    def load_map(self, filename: str = "map_data.json") -> bool:
        """
        Load map data from a file.

        Args:
            filename: Name of the file to load from

        Returns:
            True if successful, False otherwise
        """
        if not self.data_dir:
            return False

        try:
            path = os.path.join(self.data_dir, filename)

            if not os.path.exists(path):
                return False

            with open(path, "r") as f:
                map_data = json.load(f)

            # Clear existing areas
            self.areas = {}

            # Load areas from data
            for area_id, area_data in map_data["areas"].items():
                self.areas[area_id] = MapArea.from_dict(area_data)

            # Restore current area
            self.current_area_id = map_data.get("current_area_id")

            return True
        except Exception as e:
            print(f"Error loading map: {e}")
            return False
