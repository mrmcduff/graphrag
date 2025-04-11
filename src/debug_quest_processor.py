"""
Debug script for quest processing in GraphRAG.

This script helps diagnose issues with the quest processing module.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    """Run the debug script."""
    print("Debugging quest processor imports...")

    # Try to import the document quest processor
    try:
        print("Trying direct import...")
        from document_quest_processor import DocumentQuestProcessor

        print("✅ Direct import successful")
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")

    try:
        print("\nTrying package import...")
        from src.document_quest_processor import DocumentQuestProcessor

        print("✅ Package import successful")
    except ImportError as e:
        print(f"❌ Package import failed: {e}")

    # Try to import the quest parser
    try:
        print("\nTrying to import quest parser...")
        from quest_parser import QuestParser

        print("✅ Quest parser import successful")
    except ImportError as e:
        print(f"❌ Quest parser import failed: {e}")

    # Check if the document_quest_processor.py file exists
    quest_processor_path = os.path.join(
        os.path.dirname(__file__), "document_quest_processor.py"
    )
    print(
        f"\nChecking if document_quest_processor.py exists at: {quest_processor_path}"
    )
    if os.path.exists(quest_processor_path):
        print(f"✅ File exists")
    else:
        print(f"❌ File does not exist")

    # Check for quest documents
    documents_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "documents", "elyria"
    )
    print(f"\nChecking for quest documents in: {documents_dir}")
    if os.path.exists(documents_dir):
        quest_docs = []
        for filename in os.listdir(documents_dir):
            if filename.lower().endswith("quest.docx"):
                quest_docs.append(filename)

        if quest_docs:
            print(
                f"✅ Found {len(quest_docs)} quest documents: {', '.join(quest_docs)}"
            )
        else:
            print("❌ No quest documents found")
    else:
        print(f"❌ Documents directory does not exist")

    # Try to import the LLM client selection function
    try:
        print("\nTrying to import LLM client selection...")
        from llm_clients import select_llm_client

        print("✅ LLM client selection import successful")

        print("\nTrying to select an LLM client (non-interactive)...")
        client = select_llm_client(interactive=False)
        if client:
            print(f"✅ Selected LLM client: {client.name}")
        else:
            print("❌ No LLM client selected")
    except ImportError as e:
        print(f"❌ LLM client selection import failed: {e}")
    except Exception as e:
        print(f"❌ Error selecting LLM client: {e}")


if __name__ == "__main__":
    main()
