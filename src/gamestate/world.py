# Potential contents:
class WorldState:
    """Manages global world state separate from player state."""

    def __init__(self):
        self.faction_relationships = {}  # Relationships between factions
        self.world_events = {}  # Major world events that have occurred
        self.time_of_day = "day"  # Current time in the game world
        self.weather = "clear"  # Current weather in the game world

    def add_faction_relationship(self, faction1, faction2, relationship_value):
        """Define relationship between two factions."""
        if faction1 not in self.faction_relationships:
            self.faction_relationships[faction1] = {}
        self.faction_relationships[faction1][faction2] = relationship_value

    def record_world_event(self, event_name, event_data=None, turn=0):
        """Record a world event."""
        self.world_events[event_name] = {"turn": turn, "data": event_data}

    def update_time_of_day(self):
        """Update time of day based on game turns."""
        # Logic to cycle through time of day
        if self.time_of_day == "day":
            self.time_of_day = "evening"
        elif self.time_of_day == "evening":
            self.time_of_day = "night"
        else:
            self.time_of_day = "day"
