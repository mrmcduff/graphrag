import sys
import os
import networkx as nx
from src.map_generator import MapGenerator

# Create a simple graph for testing
g = nx.Graph()
g.add_edges_from(
    [
        ("riverdale", "forest_edge"),
        ("riverdale", "mountain_path"),
        ("forest_edge", "deep_forest"),
        ("mountain_path", "mountain_peak"),
        ("riverdale", "castle_road"),
        ("castle_road", "castle_entrance"),
    ]
)

# Set node labels
for node in g.nodes():
    g.nodes[node]["label"] = node.replace("_", " ").title()


# Create a game state data class to mimic the expected structure
class GameStateData:
    def __init__(self):
        self.visited_locations = ["Riverdale", "Forest Edge", "Mountain Path"]
        # Locations should be strings, not dictionaries
        self.locations = [
            "Riverdale",
            "Forest Edge",
            "Deep Forest",
            "Mountain Path",
            "Mountain Peak",
            "Castle Road",
            "Castle Entrance",
        ]
        self.graph = g


# Initialize the map generator with our mock game state data
game_state_data = GameStateData()
# Set debug=True if you want to see debug output
m = MapGenerator(game_state_data, g, debug=False)

# Generate the map
output_path = "test_map.png"
m.generate_map("Riverdale", output_path=output_path)

print(f"Map generated at {os.path.abspath(output_path)}")
