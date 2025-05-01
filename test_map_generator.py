#!/usr/bin/env python3
import os
import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional

# Fix imports to work with both direct and relative import paths
try:
    from src.graphrag.map_generator_ai import MapGeneratorAI
    from src.llm.llm_manager import LLMManager
    from src.llm.providers.base import LLMType
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from src.graphrag.map_generator_ai import MapGeneratorAI
    from src.llm.llm_manager import LLMManager
    from src.llm.providers.base import LLMType


def load_knowledge_graph(data_dir: str) -> Optional[nx.Graph]:
    """Load the knowledge graph from a GEXF file in the data directory."""
    graph_path = os.path.join(data_dir, "knowledge_graph.gexf")
    
    if not os.path.exists(graph_path):
        print(f"Error: Knowledge graph not found at {graph_path}")
        return None
    
    try:
        graph = nx.read_gexf(graph_path)
        print(f"Successfully loaded knowledge graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        return graph
    except Exception as e:
        print(f"Error loading knowledge graph: {e}")
        return None


def generate_map(location_name: str, data_dir: str, provider_type: str = "anthropic", model_name: str = None, verbose: bool = False, quiet: bool = True):
    """Generate a map for the specified location."""
    # Load the knowledge graph
    graph = load_knowledge_graph(data_dir)
    if not graph:
        print("Failed to load knowledge graph. Exiting.")
        return
    
    # Set up LLM manager
    llm_manager = LLMManager()
    
    # Patch the LLMManager's generate_text method to make it quieter by default
    if quiet:
        original_generate_text = llm_manager.generate_text
        
        def quieter_generate_text(prompt, max_tokens=500, temperature=0.7, quiet=True):
            return original_generate_text(prompt, max_tokens, temperature, quiet=True)
        
        llm_manager.generate_text = quieter_generate_text
    
    # Convert provider type string to enum
    if provider_type.lower() == "openai":
        provider_enum = llm_manager.LLMType.OPENAI
    elif provider_type.lower() == "anthropic":
        provider_enum = llm_manager.LLMType.ANTHROPIC
    elif provider_type.lower() == "google":
        provider_enum = llm_manager.LLMType.GOOGLE
    else:
        provider_enum = llm_manager.LLMType.RULE_BASED
    
    # Create and add the provider
    provider_kwargs = {}
    if model_name:
        provider_kwargs["model"] = model_name
    
    provider = llm_manager.create_provider(provider_enum, **provider_kwargs)
    llm_manager.add_provider(provider_enum, provider)
    llm_manager.set_active_provider(provider_enum)
    
    # Output directory (same as data_dir by default)
    output_dir = data_dir
    
    # Create the map generator
    map_generator = MapGeneratorAI(
        game_data_dir=data_dir,
        graph=graph,
        llm_manager=llm_manager,
        output_dir=output_dir,
        verbose=verbose
    )
    
    # Try to load existing maps first
    if map_generator.load_maps(verbose=verbose):
        print(f"Loaded existing map data with {len(map_generator.map_manager.areas)} areas")
    
    # Generate the initial area and connected areas
    print(f"Generating map for {location_name}...")
    main_area_id = map_generator.generate_initial_area(
        location_name=location_name,
        generation_depth=2,  # Generate the main area, direct connections, and one more layer
        verbose=verbose
    )
    
    if main_area_id:
        # Get the main area
        main_area = map_generator.map_manager.get_area(main_area_id)
        if main_area:
            print(f"\nSuccessfully generated map for {location_name}")
            print(f"Main area: {main_area.name} (ID: {main_area.location_id})")
            print(f"Description: {main_area.description}")
            print(f"Exits: {list(main_area.exits.keys())}")
            print(f"Total areas created: {len(map_generator.map_manager.areas)}")
            
            # Print all areas in the location
            print(f"\nAreas in {location_name}:")
            for area_id, area in map_generator.map_manager.areas.items():
                if area.location.lower() == location_name.lower():
                    print(f"  - {area.name} ({area_id})")
                    print(f"    Description: {area.description[:60]}...")
                    print(f"    Connected to: {list(area.exits.keys())}")
                    print()
    else:
        print(f"Failed to generate map for {location_name}.")


def main():
    """Main function to parse arguments and run the map generator."""
    parser = argparse.ArgumentParser(description="Generate maps for a game world")
    parser.add_argument("location", help="Name of the location to generate a map for")
    
    parser.add_argument(
        "--data-dir", 
        default="data/output/elyria", 
        help="Directory containing knowledge graph and related data files"
    )
    
    parser.add_argument(
        "--provider", 
        default="anthropic", 
        choices=["anthropic", "openai", "google", "rule_based"],
        help="LLM provider to use"
    )
    
    parser.add_argument(
        "--model", 
        default=None, 
        help="LLM model to use (if not specified, uses the default from the provider)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print detailed progress information"
    )
    
    parser.add_argument(
        "--visualize", 
        action="store_true", 
        help="Visualize the map after generation"
    )
    
    parser.add_argument(
        "--noisy", 
        action="store_true", 
        help="Print LLM response time information"
    )
    
    args = parser.parse_args()
    
    # Run the map generator
    generate_map(
        location_name=args.location,
        data_dir=args.data_dir,
        provider_type=args.provider,
        model_name=args.model,
        verbose=args.verbose,
        quiet=not args.noisy
    )
    
    # Visualize the map if requested
    if args.visualize:
        try:
            from test_map_visualizer import visualize_map
            map_file = os.path.join(args.data_dir, "maps", "map_data.json")
            print(f"\nVisualizing map from {map_file}...")
            visualize_map(map_file)
        except ImportError as e:
            print(f"Could not visualize map: {e}")
        except Exception as e:
            print(f"Error visualizing map: {e}")


if __name__ == "__main__":
    main()