"""
Document quest processor for GraphRAG text adventure game.

This module extends the document processor to extract quest information from documents
and create quest objects based on the extracted information.
"""

import os
import json
import pandas as pd
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
import logging

# Import the document processor
from document_processor import (
    process_documents,
    chunk_text,
    extract_entities_and_relations,
    initialize_nlp,
)
from quest_parser import QuestParser
from gamestate.quest_system import Quest, QuestManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentQuestProcessor:
    """Class to extract quest information from documents and create quest objects."""

    def __init__(self, llm_client=None):
        """
        Initialize the document quest processor.

        Args:
            llm_client: Client for the LLM API (optional)
        """
        self.quest_parser = QuestParser(llm_client)

    def set_llm_client(self, llm_client):
        """
        Set the LLM client.

        Args:
            llm_client: Client for the LLM API
        """
        self.quest_parser.set_llm_client(llm_client)

    def process_documents_for_quests(
        self, directory: str, output_dir: str = None, world_name: str = None
    ) -> Tuple[List[Quest], pd.DataFrame]:
        """
        Process documents in a directory to extract quest information.

        Args:
            directory: Directory containing documents
            output_dir: Directory to save extracted quest data (optional)

        Returns:
            Tuple containing:
            - List of extracted quests
            - DataFrame with columns: filename, quest_id, quest_data
        """
        logger.info(f"Processing documents in {directory} for quests")

        # Process documents
        df_documents = process_documents(directory)

        if df_documents.empty:
            logger.warning("No documents found")
            return [], pd.DataFrame()

        # Extract quests from each document
        quests = []
        quest_data_list = []

        for _, row in df_documents.iterrows():
            filename = row["filename"]
            content = row["content"]

            logger.info(f"Extracting quests from {filename}")

            # Extract quest data
            extracted_quests = self.quest_parser.extract_quests_from_text(content)

            # Create quest objects
            for quest_data in extracted_quests:
                quest = self.quest_parser.create_quest_from_data(quest_data)

                if quest:
                    quests.append(quest)

                    # Add to quest data list for DataFrame
                    quest_data_list.append(
                        {
                            "filename": filename,
                            "quest_id": quest.quest_id,
                            "quest_data": quest_data,
                        }
                    )

        # Create DataFrame
        df_quests = pd.DataFrame(quest_data_list)

        # Save to file if output_dir is provided
        if output_dir and not df_quests.empty:
            # If world_name is provided, create a world-specific output directory
            if world_name:
                world_output_dir = os.path.join(output_dir, world_name)
            else:
                # Try to find the most recent world directory
                world_dirs = [
                    d
                    for d in os.listdir(output_dir)
                    if os.path.isdir(os.path.join(output_dir, d))
                ]
                if world_dirs:
                    # Sort by modification time (newest first)
                    world_dirs.sort(
                        key=lambda d: os.path.getmtime(os.path.join(output_dir, d)),
                        reverse=True,
                    )
                    world_output_dir = os.path.join(output_dir, world_dirs[0])
                else:
                    # Create a new world directory with timestamp
                    from datetime import datetime

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    world_output_dir = os.path.join(output_dir, f"world_{timestamp}")

            os.makedirs(world_output_dir, exist_ok=True)

            # Save quest data
            df_quests.to_csv(os.path.join(world_output_dir, "quests.csv"), index=False)

            # Save quest objects as JSON
            quest_json = {}
            for quest in quests:
                quest_json[quest.quest_id] = quest.to_dict()

            with open(os.path.join(world_output_dir, "quests.json"), "w") as f:
                json.dump(quest_json, f, indent=2)

            logger.info(f"Saved {len(quests)} quests to {world_output_dir}")

            # Add quests to the knowledge graph if it exists
            graph_path = os.path.join(world_output_dir, "knowledge_graph.gexf")
            if os.path.exists(graph_path):
                self._add_quests_to_knowledge_graph(
                    quests, graph_path, world_output_dir
                )

        return quests, df_quests

    def _add_quests_to_knowledge_graph(
        self, quests: List[Quest], graph_path: str, output_dir: str
    ) -> None:
        """
        Add quests to the knowledge graph.

        Args:
            quests: List of quests
            graph_path: Path to the knowledge graph file
            output_dir: Directory to save the updated graph
        """
        try:
            # Load the knowledge graph
            G = nx.read_gexf(graph_path)

            # Add quest nodes and edges
            for quest in quests:
                # Add quest node
                node_id = f"quest_{quest.quest_id}"
                G.add_node(
                    node_id,
                    label=quest.title,
                    type="quest",
                    quest_type=quest.quest_type.value,
                    description=quest.description,
                )

                # Add edges to related entities
                if quest.giver:
                    # Find character node
                    for node, attrs in G.nodes(data=True):
                        if (
                            attrs.get("type") == "character"
                            and attrs.get("label", "").lower() == quest.giver.lower()
                        ):
                            G.add_edge(node_id, node, relation="given_by")
                            break

                # Add edges based on quest type
                if hasattr(quest, "item_to_fetch") and quest.item_to_fetch:
                    # Find item node
                    for node, attrs in G.nodes(data=True):
                        if (
                            attrs.get("type") == "item"
                            and attrs.get("label", "").lower()
                            == quest.item_to_fetch.lower()
                        ):
                            G.add_edge(node_id, node, relation="requires_item")
                            break

                if hasattr(quest, "target_location") and quest.target_location:
                    # Find location node
                    for node, attrs in G.nodes(data=True):
                        if (
                            attrs.get("type") == "location"
                            and attrs.get("label", "").lower()
                            == quest.target_location.lower()
                        ):
                            G.add_edge(node_id, node, relation="target_location")
                            break

                if hasattr(quest, "target_enemy") and quest.target_enemy:
                    # Find character node
                    for node, attrs in G.nodes(data=True):
                        if (
                            attrs.get("type") == "character"
                            and attrs.get("label", "").lower()
                            == quest.target_enemy.lower()
                        ):
                            G.add_edge(node_id, node, relation="target_enemy")
                            break

            # Save the updated graph
            nx.write_gexf(G, graph_path)
            logger.info(f"Added {len(quests)} quests to knowledge graph")

            # Update the entities CSV file with quests
            entities_path = os.path.join(output_dir, "entities.csv")
            if os.path.exists(entities_path):
                df_entities = pd.read_csv(entities_path)

                # Add quest entities
                quest_entities = []
                for quest in quests:
                    quest_entities.append(
                        {
                            "entity": quest.title,
                            "type": "quest",
                            "subtype": quest.quest_type.value,
                            "description": quest.description,
                        }
                    )

                # Append to existing entities
                df_quest_entities = pd.DataFrame(quest_entities)
                df_entities = pd.concat(
                    [df_entities, df_quest_entities], ignore_index=True
                )

                # Save updated entities
                df_entities.to_csv(entities_path, index=False)
                logger.info(f"Updated entities CSV with {len(quests)} quests")

        except Exception as e:
            logger.error(f"Error adding quests to knowledge graph: {e}")

    def create_quest_manager(self, quests: List[Quest]) -> QuestManager:
        """
        Create a quest manager from a list of quests.

        Args:
            quests: List of quests

        Returns:
            QuestManager object
        """
        quest_manager = QuestManager()

        for quest in quests:
            quest_manager.add_quest(quest)

        return quest_manager


def main(
    documents_dir: str,
    output_dir: str = "output",
    world_name: str = None,
    llm_client=None,
) -> QuestManager:
    """
    Process documents and extract quests.

    Args:
        documents_dir: Directory containing documents
        output_dir: Directory to save output files
        llm_client: Client for the LLM API (optional)

    Returns:
        QuestManager object containing all extracted quests
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create document quest processor
    processor = DocumentQuestProcessor(llm_client)

    # Process documents
    quests, _ = processor.process_documents_for_quests(
        documents_dir, output_dir, world_name
    )

    # Create quest manager
    quest_manager = processor.create_quest_manager(quests)

    logger.info(f"Extracted {len(quests)} quests from documents")

    return quest_manager


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract quests from documents for a GraphRAG-based text adventure game"
    )

    parser.add_argument(
        "--documents_dir", required=True, help="Directory containing documents"
    )
    parser.add_argument(
        "--output_dir", default="data/output", help="Directory to save output files"
    )
    parser.add_argument("--world_name", help="Name of the world to save quests to")

    args = parser.parse_args()

    # Process documents
    quest_manager = main(args.documents_dir, args.output_dir, args.world_name)

    print(f"Extracted {len(quest_manager.quests)} quests from documents")
