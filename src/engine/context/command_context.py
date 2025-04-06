from typing import TYPE_CHECKING
from engine.intent_recognition import IntentType

if TYPE_CHECKING:
    from game_engine import GameState  # Only imported for type checking


class CommandContext:
    """Represents the context in which a command is executed."""

    def __init__(self, game_state: "GameState"):
        """
        Initialize the command context.

        Args:
            game_state: The current game state
        """
        self.game_state = game_state
        self.recent_interactions = []  # List of recent interactions
        self.current_focus = None  # Currently focused entity
        self.last_referenced_entities = {}  # Track references by pronoun

    def add_interaction(self, interaction_type: IntentType, target_info: tuple):
        """
        Add a recent interaction to the context.

        Args:
            interaction_type: Type of interaction
            target_info: Tuple of (entity_type, entity_id)
        """
        self.recent_interactions.append((interaction_type, target_info))
        if len(self.recent_interactions) > 5:  # Keep only 5 most recent
            self.recent_interactions.pop(0)

        self.current_focus = target_info

        # Update referenced entities
        entity_type, entity_id = target_info
        if entity_type:
            # Update pronouns based on entity type (simplified)
            pronoun = "it"  # Default

            # Get entity data to determine appropriate pronoun
            entity_data = self._get_entity_data(entity_type, entity_id)

            if entity_data:
                if entity_type == "npcs" and entity_data.get("gender") == "female":
                    pronoun = "her"
                elif entity_type == "npcs" and entity_data.get("gender") == "male":
                    pronoun = "him"

            self.last_referenced_entities[pronoun] = target_info

    def _get_entity_data(self, entity_type, entity_id):
        """Get entity data from game state."""
        if entity_type == "items":
            return self.game_state.get_item_data(entity_id)
        elif entity_type == "npcs":
            return self.game_state.get_npc_data(entity_id)
        elif entity_type == "features":
            return self.game_state.get_feature_data(entity_id)
        return None

    def get_visible_entities(self):
        """Get all entities visible in the current location."""
        current_location = self.game_state.player_location
        visible_entities = {
            "items": self.game_state.get_items_at_location(current_location),
            "npcs": self.game_state.get_npcs_at_location(current_location),
            "features": self.game_state.get_features_at_location(current_location),
            "exits": self.game_state.get_exits_from_location(current_location),
        }
        return visible_entities

    def resolve_reference(self, reference):
        """
        Resolve an ambiguous reference like "it", "them", "the door".

        Args:
            reference: The reference text

        Returns:
            Tuple of (entity_type, entity_id) if resolved, None otherwise
        """
        if not reference:
            return None

        reference = reference.lower()

        # Check for pronouns referencing entities
        pronouns = ["it", "him", "her", "them", "this", "that"]
        if reference in pronouns and reference in self.last_referenced_entities:
            return self.last_referenced_entities[reference]

        # Check for "the X" format
        if reference.startswith("the "):
            reference = reference[4:]  # Remove "the "

        # Check visible entities
        visible = self.get_visible_entities()

        # First, try exact matches
        for entity_type, entities in visible.items():
            for entity_id, entity_data in entities.items():
                if entity_data.get("name", "").lower() == reference:
                    return (entity_type, entity_id)

        # Then, try partial matches
        for entity_type, entities in visible.items():
            for entity_id, entity_data in entities.items():
                if reference in entity_data.get("name", "").lower():
                    return (entity_type, entity_id)

        # Check inventory for items
        inventory = self.game_state.get_inventory()
        if inventory:
            for item_id, item_data in inventory.items():
                if item_data.get("name", "").lower() == reference:
                    return ("inventory", item_id)
                if reference in item_data.get("name", "").lower():
                    return ("inventory", item_id)

        return None
