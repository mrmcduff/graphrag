import os
import json
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GameStateData:
    """Class to store the game state data."""
    
    # Basic game data
    game_data_dir: str
    player_location: Optional[str] = None
    inventory: List[str] = field(default_factory=list)
    visited_locations: Set[str] = field(default_factory=set)
    npc_states: Dict[str, Dict] = field(default_factory=dict)
    quests: Dict[str, Dict] = field(default_factory=dict)
    game_turn: int = 0
    player_actions: List[str] = field(default_factory=list)
    
    # Game elements loaded from files
    locations: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    
    # World state
    world_state: Dict[str, Dict] = field(default_factory=lambda: {
        "faction_relationships": {},  # Relationships between factions
        "player_faction_standing": {},  # Player's standing with each faction
        "world_events": {},  # Major world events that have occurred
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the state data to a dictionary for saving."""
        return {
            "player_location": self.player_location,
            "inventory": self.inventory,
            "visited_locations": list(self.visited_locations),
            "npc_states": self.npc_states,
            "quests": self.quests,
            "game_turn": self.game_turn,
            "player_actions": self.player_actions,
            "world_state": self.world_state,
        }
    
    def from_dict(self, save_data: Dict[str, Any]) -> None:
        """Load state data from a dictionary."""
        self.player_location = save_data["player_location"]
        self.inventory = save_data["inventory"]
        self.visited_locations = set(save_data["visited_locations"])
        self.npc_states = save_data["npc_states"]
        self.quests = save_data["quests"]
        self.game_turn = save_data["game_turn"]
        self.player_actions = save_data["player_actions"]
        self.world_state = save_data["world_state"]
