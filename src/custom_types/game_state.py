from dataclasses import dataclass
from typing import Any, List, Set, Dict, Optional
from pandas import DataFrame
from networkx import Graph


@dataclass
class WorldState:
    faction_relationships: Any  # Relationships between factions
    player_faction_standing: Any  # Player's standing with each faction
    world_events: Any  # Major world events that have occurred


@dataclass
class GameState:
    game_data_dir: str
    player_location: Optional[str]
    inventory: List[str]
    visited_locations: Set[str]
    npc_states: Dict[str, Any]  # For tracking NPC states and relationships with player
    quests: Dict[str, Any]  # For tracking active and completed quests
    game_turn: int  # Track the number of turns
    player_actions: List[str]  # History of significant player act
    # World state for factions and global events
    world_state: WorldState
    characters: List[str]
    items: List[str]
    locations: List[str]
    actions: List[str]
    entities_df: DataFrame
    relations_df: DataFrame
    graph: Graph
