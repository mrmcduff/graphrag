#!/usr/bin/env python3
"""
GraphRAG Text Adventure Game
Main entry point for the game engine
"""

import os
import sys
import argparse
import time
from typing import Dict, Any, List, Optional


def list_available_worlds(base_dir: str = "data/output") -> List[Dict[str, any]]:
    """
    List all available worlds in the output directory.
    
    Args:
        base_dir: Base directory containing world data
        
    Returns:
        List of world information dictionaries
    """
    worlds = []
    base_path = os.path.abspath(base_dir)
    
    # Check if the base directory exists
    if not os.path.isdir(base_path):
        print(f"Warning: Output directory '{base_dir}' does not exist.")
        return worlds
    
    # Check if the root output directory has a knowledge graph
    if os.path.exists(os.path.join(base_path, "knowledge_graph.gexf")):
        worlds.append({
            "name": "default",
            "path": base_dir,
            "created": time.ctime(os.path.getmtime(os.path.join(base_path, "knowledge_graph.gexf"))),
        })
    
    # Check subdirectories
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "knowledge_graph.gexf")):
            worlds.append({
                "name": item,
                "path": os.path.join(base_dir, item),
                "created": time.ctime(os.path.getmtime(os.path.join(item_path, "knowledge_graph.gexf"))),
            })
    
    return worlds


def find_world_by_name(world_name: str, base_dir: str = "data/output") -> Optional[str]:
    """
    Find a world by name and return its path.
    
    Args:
        world_name: Name of the world to find
        base_dir: Base directory containing world data
        
    Returns:
        Path to the world directory if found, None otherwise
    """
    worlds = list_available_worlds(base_dir)
    
    for world in worlds:
        if world["name"].lower() == world_name.lower():
            return world["path"]
    
    return None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="GraphRAG Text Adventure Game")
    
    world_group = parser.add_argument_group("World Selection")
    world_group.add_argument(
        "--game_data_dir",
        default="data/output",
        help="Directory containing game data files",
    )
    world_group.add_argument(
        "--world",
        help="Name of the world to load (will be looked up in data/output)",
    )
    world_group.add_argument(
        "--list_worlds",
        action="store_true",
        help="List all available worlds",
    )
    
    parser.add_argument(
        "--load_save", default=None, help="Load a previously saved game file"
    )
    parser.add_argument(
        "--no_color", action="store_true", help="Disable colored output"
    )
    parser.add_argument(
        "--no_typing_effect",
        action="store_true",
        help="Disable typing effect for text display",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: disables text animation for faster debugging",
    )
    parser.add_argument(
        "--width", type=int, default=80, help="Width of the text display"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose logging"
    )

    return parser.parse_args()


def validate_data_directory(game_data_dir: str) -> bool:
    """
    Validate that the game data directory exists and contains necessary files.

    Args:
        game_data_dir: Directory containing game data files

    Returns:
        Boolean indicating if directory is valid
    """
    if not os.path.isdir(game_data_dir):
        print(f"Error: Game data directory '{game_data_dir}' does not exist.")
        return False

    # Check for essential files
    required_files = ["game_locations.csv", "game_characters.csv", "game_items.csv"]

    missing_files = [
        f for f in required_files if not os.path.exists(os.path.join(game_data_dir, f))
    ]

    if missing_files:
        print(
            f"Warning: The following required files are missing from '{game_data_dir}':"
        )
        for file in missing_files:
            print(f"  - {file}")

        print("\nYou might need to run the document processor first:")
        print(
            "  python src/document_processor.py --documents_dir data/documents --output_dir data/output"
        )

        # If missing critical files, suggest creating them with sample data
        return False

    return True


def create_config(args) -> Dict[str, Any]:
    """
    Create configuration dictionary from command line arguments.

    Args:
        args: Command line arguments

    Returns:
        Configuration dictionary
    """
    return {
        "output_config": {
            "use_color": not args.no_color,
            "delay": 0 if args.no_typing_effect else 0.02,
            "width": args.width,
            "quick_mode": args.quick,
        },
        "save_file": args.load_save,
    }


def main():
    """Main entry point for the game."""
    # Parse command line arguments
    args = parse_arguments()

    # Set debug mode based on command line flag
    from util.debug import set_debug_mode

    set_debug_mode(args.debug)

    # Load environment variables from .env file
    from util.config import load_environment_variables

    # Apply Pillow patch for textsize method
    from util import pillow_patch

    load_environment_variables()
    
    # Handle listing worlds if requested
    if args.list_worlds:
        worlds = list_available_worlds()
        if not worlds:
            print("No worlds found. Run the document processor to create a world.")
            sys.exit(0)
            
        print("\nAvailable worlds:")
        print("-" * 80)
        for world in worlds:
            print(f"Name: {world['name']}")
            print(f"Path: {world['path']}")
            print(f"Created: {world['created']}")
            print("-" * 80)
        sys.exit(0)
    
    # Handle world selection if specified
    if args.world:
        world_path = find_world_by_name(args.world)
        if world_path:
            print(f"Using world: {args.world} ({world_path})")
            args.game_data_dir = world_path
        else:
            print(f"Error: World '{args.world}' not found. Use --list_worlds to see available worlds.")
            sys.exit(1)

    # Validate game data directory
    if not validate_data_directory(args.game_data_dir):
        proceed = input("Continue anyway? (y/n): ").lower() == "y"
        if not proceed:
            print("Exiting.")
            sys.exit(1)

    # Create configuration
    config = create_config(args)

    # Import components here to avoid circular imports
    from engine.game_loop import GameLoop

    # Create and start the game loop
    game = GameLoop(args.game_data_dir, config)
    game.start()


if __name__ == "__main__":
    main()
