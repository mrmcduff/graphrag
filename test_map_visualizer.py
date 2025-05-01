#!/usr/bin/env python3
import os
import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict

# Fix imports to work with both direct and relative import paths
try:
    from src.gamestate.map_manager import MapManager
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from src.gamestate.map_manager import MapManager


def visualize_map(map_file: str, output_file: str = None, show_plot: bool = True):
    """
    Visualize a game map by reading the map data and creating a network graph.
    
    Args:
        map_file: Path to the map data file
        output_file: Path to save the visualization image (optional)
        show_plot: Whether to display the plot interactively
    """
    # Load the map
    map_manager = MapManager()
    
    if not map_manager.load_map(map_file):
        print(f"Error: Could not load map from {map_file}")
        return
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes and edges based on map areas and connections
    for area_id, area in map_manager.areas.items():
        # Add a node for each area
        node_color = "lightgreen" if area.is_region_entrance else "lightblue"
        node_size = 1000 if area.is_region_entrance else 700
        
        G.add_node(
            area_id, 
            label=area.name, 
            location=area.location,
            sub_location=area.sub_location or "",
            color=node_color,
            size=node_size
        )
        
        # Add edges for exits
        for direction, target_id in area.exits.items():
            if target_id and target_id in map_manager.areas:
                G.add_edge(area_id, target_id, direction=direction)
    
    # Setup plot
    plt.figure(figsize=(16, 12))
    
    # Get node attributes for visualization
    node_colors = [data.get("color", "lightblue") for node, data in G.nodes(data=True)]
    node_sizes = [data.get("size", 700) for node, data in G.nodes(data=True)]
    
    # Use different layout algorithms based on graph size
    if len(G.nodes) < 10:
        pos = nx.spring_layout(G, seed=42, k=0.5)
    elif len(G.nodes) < 20:
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42, k=0.8, iterations=100)
    
    # Draw the network
    nx.draw(
        G, 
        pos, 
        with_labels=False,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
        edge_color="gray",
        arrows=True
    )
    
    # Add labels
    labels = {}
    for node, data in G.nodes(data=True):
        labels[node] = f"{data['label']}\n({data['sub_location']})" if data['sub_location'] else data['label']
    
    nx.draw_networkx_labels(
        G, 
        pos, 
        labels=labels,
        font_size=8,
        font_weight="bold"
    )
    
    # Add edge labels (directions)
    edge_labels = {(u, v): data["direction"] for u, v, data in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, 
        pos, 
        edge_labels=edge_labels,
        font_size=7
    )
    
    # Add title
    areas = list(map_manager.areas.values())
    if areas:
        location_name = areas[0].location
        plt.title(f"Map of {location_name} - {len(G.nodes)} Areas")
    else:
        plt.title("Game World Map")
    
    plt.tight_layout()
    
    # Save the plot if requested
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Map visualization saved to {output_file}")
    
    # Show the plot if requested
    if show_plot:
        plt.show()
    
    return G


def main():
    """Main function to parse arguments and visualize a map."""
    parser = argparse.ArgumentParser(description="Visualize a game map")
    
    parser.add_argument(
        "--map-file", 
        default="data/output/elyria/maps/map_data.json", 
        help="Path to the map data file"
    )
    
    parser.add_argument(
        "--output", 
        default=None, 
        help="Path to save the visualization image (optional)"
    )
    
    parser.add_argument(
        "--no-show", 
        action="store_true", 
        help="Don't display the plot interactively"
    )
    
    args = parser.parse_args()
    
    # Visualize the map
    visualize_map(
        map_file=args.map_file,
        output_file=args.output,
        show_plot=not args.no_show
    )


if __name__ == "__main__":
    main()