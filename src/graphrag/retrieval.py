# Potential contents:
import networkx as nx
from typing import List, Dict, Any, Set


def retrieve_by_entity(entity_id: str, graph: nx.Graph, depth: int = 1) -> List[str]:
    """
    Retrieve context related to a specific entity.

    Args:
        entity_id: ID of the entity to retrieve context for
        graph: Knowledge graph
        depth: Depth of traversal in the graph

    Returns:
        List of relevant context strings
    """
    related_entities = set()

    if entity_id in graph.nodes:
        # Direct neighbors (depth 1)
        for neighbor in graph.neighbors(entity_id):
            related_entities.add(neighbor)

        # Additional depth if requested
        if depth > 1:
            for entity in list(
                related_entities
            ):  # Make copy to avoid modification during iteration
                for neighbor in graph.neighbors(entity):
                    related_entities.add(neighbor)

    return list(related_entities)


def retrieve_by_relation(subject: str, relation: str, relations_df) -> List[Dict]:
    """
    Retrieve triples matching a subject and relation.

    Args:
        subject: Subject entity
        relation: Relation type
        relations_df: DataFrame of relations

    Returns:
        List of matching relation dictionaries
    """
    # Filter relations DataFrame
    matches = relations_df[
        (relations_df["subject"] == subject.lower())
        & (relations_df["predicate"] == relation.lower())
    ]

    return matches.to_dict("records")
