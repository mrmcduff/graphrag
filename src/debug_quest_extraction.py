#!/usr/bin/env python3
"""
Debug script for testing quest extraction from documents.

This script allows testing the quest extraction functionality without running the full game.
It processes quest documents and outputs the extracted quests in JSON format for debugging.
"""

import os
import sys
import json
import logging
import argparse
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_paths():
    """Add the current directory to sys.path to ensure imports work correctly."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Also add the parent directory
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)


def process_quest_document(
    document_path: str, output_dir: str, use_llm: bool = True
) -> None:
    """
    Process a single quest document for debugging.

    Args:
        document_path: Path to the quest document
        output_dir: Directory to save output files
        use_llm: Whether to use an LLM for quest parsing
    """
    try:
        # Import the document processor
        from document_processor import process_quest_documents

        # Create a temporary directory with just this document
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the document to the temp directory
            document_name = os.path.basename(document_path)
            temp_path = os.path.join(temp_dir, document_name)
            shutil.copy2(document_path, temp_path)

            # Process the document
            world_name = "debug"
            process_quest_documents(
                temp_dir, output_dir, world_name, use_llm, debug_mode=True
            )

            # Check if quests were extracted
            debug_file = os.path.join(
                output_dir, "debug", f"{world_name}_quests_debug.json"
            )
            if os.path.exists(debug_file):
                with open(debug_file, "r") as f:
                    quests = json.load(f)

                print("\nExtracted quests:")
                print(json.dumps(quests, indent=2))
                print(f"\nQuest data saved to {debug_file}")
            else:
                print("No quests were extracted or debug file was not created.")

    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error processing quest document: {e}")


def test_rule_based_extraction(document_path: str) -> None:
    """
    Test the rule-based extraction directly without going through the document processor.

    Args:
        document_path: Path to the quest document
    """
    try:
        # Import the necessary modules
        from docx import Document
        from llm_clients import RuleBasedClient
        from quest_parser import QuestParser

        # Read the document
        doc = Document(document_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])

        print(f"\nDocument text:\n{'-' * 40}\n{text}\n{'-' * 40}\n")

        # Create a rule-based client with debug mode
        client = RuleBasedClient(debug_mode=True)

        # Create a quest parser
        parser = QuestParser(client)

        # Extract quests
        quests = parser.extract_quests_from_text(text)

        print("\nExtracted quests:")
        print(json.dumps(quests, indent=2))

    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error testing rule-based extraction: {e}")


def main():
    """Main function to run the debug script."""
    parser = argparse.ArgumentParser(
        description="Debug quest extraction from documents"
    )
    parser.add_argument("--document", "-d", type=str, help="Path to the quest document")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Directory to save output files",
    )
    parser.add_argument(
        "--no-llm", action="store_true", help="Disable LLM for quest parsing"
    )
    parser.add_argument(
        "--rule-based-only",
        action="store_true",
        help="Test only the rule-based extraction",
    )

    args = parser.parse_args()

    # Set up paths for imports
    setup_paths()

    # Check if document exists
    if not args.document or not os.path.exists(args.document):
        print("Please provide a valid document path")
        parser.print_help()
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # Process the document
    if args.rule_based_only:
        test_rule_based_extraction(args.document)
    else:
        process_quest_document(args.document, args.output, not args.no_llm)


if __name__ == "__main__":
    main()
