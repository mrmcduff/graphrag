import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# Set output directory
output_dir = "data/output"

# Load entities and relations
entities_df = pd.read_csv(os.path.join(output_dir, "entities.csv"))
relations_df = pd.read_csv(os.path.join(output_dir, "relations.csv"))

# Load game elements
locations_df = pd.read_csv(os.path.join(output_dir, "game_locations.csv"))
characters_df = pd.read_csv(os.path.join(output_dir, "game_characters.csv"))
items_df = pd.read_csv(os.path.join(output_dir, "game_items.csv"))

# Print summary statistics
print(f"Extracted {len(entities_df)} entities")
print(f"Extracted {len(relations_df)} relationships")
print(f"Identified {len(locations_df)} locations")
print(f"Identified {len(characters_df)} characters")
print(f"Identified {len(items_df)} items")

# Show most common entity types
entity_types = entities_df["label"].value_counts()
print("\nEntity types:")
print(entity_types)

# Load and visualize a small portion of the graph
G = nx.read_gexf(os.path.join(output_dir, "knowledge_graph.gexf"))
print(f"\nGraph has {len(G.nodes)} nodes and {len(G.edges)} edges")

# Take a small subgraph for visualization
if len(G.nodes) > 0:
    plt.figure(figsize=(10, 8))

    # Take first 20 nodes for visualization
    nodes = list(G.nodes)[: min(20, len(G.nodes))]
    subgraph = G.subgraph(nodes)

    pos = nx.spring_layout(subgraph)
    labels = {node: G.nodes[node].get("label", node) for node in subgraph.nodes}

    nx.draw(
        subgraph,
        pos,
        with_labels=True,
        labels=labels,
        node_color="lightblue",
        node_size=1500,
        font_size=8,
    )

    plt.title("Sample of Knowledge Graph")
    plt.savefig("data/output/graph_sample.png")
    print("Saved graph visualization to data/output/graph_sample.png")
