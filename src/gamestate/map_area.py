from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple


@dataclass
class MapArea:
    """
    Represents a specific point or area within the game world.

    This class models an individual location in the game world that players can visit,
    interact with, and move between. It includes geographic information, special
    attributes, and connections to other areas.

    Attributes:
        location_id: Unique identifier for this map area
        name: Display name for this area
        location: The broader geographic location (city, mountain, castle, etc.)
        sub_location: Optional sub-location within the broader location (neighborhood, district, floor)
        coordinates: Position coordinates as (x, y, level) where level can indicate elevation
        description: Textual description of the area
        attributes: Set of special properties (underground, elevated, underwater, etc.)
        exits: Dictionary mapping direction names to connected MapArea IDs
        items: List of items found in this area
        npcs: List of NPCs present in this area
        visited: Whether the player has visited this area
        danger_level: Numeric indicator of how dangerous this area is (0-10)
        requires_item: Optional item required to access this area
        parent_area_id: Optional ID of a parent area if this is a sub-area
        is_region_entrance: Whether this area serves as the main entrance to a region
    """

    # Core identification
    location_id: str
    name: str
    location: str

    # Hierarchical organization
    sub_location: Optional[str] = None
    parent_area_id: Optional[str] = None
    is_region_entrance: bool = False

    # Geographic information
    coordinates: Tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))

    # Descriptive elements
    description: str = ""
    attributes: Set[str] = field(default_factory=set)

    # Connections and contents
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> location_id
    items: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)

    # State and properties
    visited: bool = False
    danger_level: int = 0
    requires_item: Optional[str] = None

    def add_exit(self, direction: str, target_id: str) -> None:
        """
        Add an exit from this area to another.

        Args:
            direction: The direction name (north, south, up, etc.)
            target_id: The location_id of the destination MapArea
        """
        self.exits[direction] = target_id

    def remove_exit(self, direction: str) -> bool:
        """
        Remove an exit from this area.

        Args:
            direction: The direction to remove

        Returns:
            True if the exit was removed, False if it didn't exist
        """
        if direction in self.exits:
            del self.exits[direction]
            return True
        return False

    def add_attribute(self, attribute: str) -> None:
        """
        Add an environmental or special attribute to this area.

        Args:
            attribute: The attribute to add (e.g., "underwater", "dark", "magical")
        """
        self.attributes.add(attribute)

    def has_attribute(self, attribute: str) -> bool:
        """
        Check if this area has a specific attribute.

        Args:
            attribute: The attribute to check for

        Returns:
            True if the area has this attribute, False otherwise
        """
        return attribute in self.attributes

    def add_item(self, item: str) -> None:
        """
        Add an item to this area.

        Args:
            item: The item to add
        """
        if item not in self.items:
            self.items.append(item)

    def remove_item(self, item: str) -> bool:
        """
        Remove an item from this area.

        Args:
            item: The item to remove

        Returns:
            True if the item was removed, False if it wasn't present
        """
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def add_npc(self, npc: str) -> None:
        """
        Add an NPC to this area.

        Args:
            npc: The NPC to add
        """
        if npc not in self.npcs:
            self.npcs.append(npc)

    def remove_npc(self, npc: str) -> bool:
        """
        Remove an NPC from this area.

        Args:
            npc: The NPC to remove

        Returns:
            True if the NPC was removed, False if they weren't present
        """
        if npc in self.npcs:
            self.npcs.remove(npc)
            return True
        return False

    def mark_visited(self) -> None:
        """Mark this area as visited by the player."""
        self.visited = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this MapArea to a dictionary for serialization.

        Returns:
            Dictionary representation of this MapArea
        """
        return {
            "location_id": self.location_id,
            "name": self.name,
            "location": self.location,
            "sub_location": self.sub_location,
            "parent_area_id": self.parent_area_id,
            "is_region_entrance": self.is_region_entrance,
            "coordinates": self.coordinates,
            "description": self.description,
            "attributes": list(self.attributes),
            "exits": self.exits,
            "items": self.items,
            "npcs": self.npcs,
            "visited": self.visited,
            "danger_level": self.danger_level,
            "requires_item": self.requires_item,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapArea":
        """
        Create a MapArea instance from a dictionary.

        Args:
            data: Dictionary containing MapArea data

        Returns:
            New MapArea instance
        """
        # Copy the dictionary to avoid modifying the original
        data_copy = data.copy()

        # Convert attributes list back to a set
        if "attributes" in data_copy:
            data_copy["attributes"] = set(data_copy["attributes"])

        # Create and return the MapArea instance
        return cls(**data_copy)
