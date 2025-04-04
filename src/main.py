#!/usr/bin/env python3
"""
GraphRAG Text Adventure Game
Main entry point for the game engine
"""

import os
import sys
import argparse
from typing import Dict, Any


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="GraphRAG Text Adventure Game")
    parser.add_argument(
        "--game_data_dir",
        default="data/output",
        help="Directory containing game data files",
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
        "--width", type=int, default=80, help="Width of the text display"
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
        },
        "save_file": args.load_save,
    }


def main():
    """Main entry point for the game."""
    # Parse command line arguments
    args = parse_arguments()

    # Load environment variables from .env file
    from util.config import load_environment_variables

    load_environment_variables()

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
