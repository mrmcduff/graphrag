"""
Quest system for GraphRAG text adventure game.

This module defines the quest class hierarchy and related functionality for
managing quests in the game.
"""

from enum import Enum
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, field
import uuid


class QuestStatus(Enum):
    """Enum representing the possible states of a quest."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestType(Enum):
    """Enum representing the different types of quests."""

    FETCH = "fetch"
    LOCATION = "location"
    COMBAT = "combat"
    INFORMATION = "information"
    COMPOSITE = "composite"  # A quest that combines multiple quest types


@dataclass
class QuestCondition:
    """
    Class representing a condition for a quest.

    This can be used for trigger conditions, completion criteria, or failure conditions.
    """

    condition_type: (
        str  # e.g., "has_item", "at_location", "defeated_enemy", "talked_to_npc"
    )
    target: str  # The target of the condition (item name, location name, character name, etc.)
    parameters: Dict[str, Any] = field(default_factory=dict)  # Additional parameters

    def check(self, game_state) -> bool:
        """
        Check if the condition is met based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            Boolean indicating if the condition is met
        """
        if self.condition_type == "has_item":
            return self.target in game_state.inventory

        elif self.condition_type == "at_location":
            return game_state.player_location == self.target

        elif self.condition_type == "defeated_enemy":
            # Check if the enemy has been defeated in the NPC states
            if self.target in game_state.npc_states:
                return game_state.npc_states[self.target].get("defeated", False)
            return False

        elif self.condition_type == "talked_to_npc":
            # Check if the player has talked to the NPC
            if self.target in game_state.npc_states:
                return game_state.npc_states[self.target].get("talked_to", False)
            return False

        elif self.condition_type == "has_information":
            # Check if the player has acquired specific information
            return game_state.world_state.get("player_knowledge", {}).get(
                self.target, False
            )

        elif self.condition_type == "custom":
            # For custom conditions, we use a lambda function stored in parameters
            if "check_function" in self.parameters:
                return self.parameters["check_function"](game_state)
            return False

        return False


@dataclass
class QuestConsequence:
    """
    Class representing a consequence of completing or failing a quest.

    This can include rewards, penalties, or world state changes.
    """

    consequence_type: (
        str  # e.g., "add_item", "remove_item", "change_npc_state", "change_world_state"
    )
    target: str  # The target of the consequence (item name, NPC name, world state key, etc.)
    parameters: Dict[str, Any] = field(default_factory=dict)  # Additional parameters

    def apply(self, game_state) -> None:
        """
        Apply the consequence to the game state.

        Args:
            game_state: The current game state
        """
        if self.consequence_type == "add_item":
            if self.target not in game_state.inventory:
                game_state.inventory.append(self.target)

        elif self.consequence_type == "remove_item":
            if self.target in game_state.inventory:
                game_state.inventory.remove(self.target)

        elif self.consequence_type == "change_npc_state":
            if self.target in game_state.npc_states:
                for key, value in self.parameters.items():
                    game_state.npc_states[self.target][key] = value
            else:
                game_state.npc_states[self.target] = self.parameters

        elif self.consequence_type == "change_world_state":
            # Update a specific key in the world state
            path = self.target.split(".")
            current = game_state.world_state
            for part in path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path[-1]] = self.parameters.get("value")

        elif self.consequence_type == "custom":
            # For custom consequences, we use a lambda function stored in parameters
            if "apply_function" in self.parameters:
                self.parameters["apply_function"](game_state)


class Quest:
    """Base class for all quests in the game."""

    def __init__(
        self,
        quest_id: str = None,
        title: str = "",
        description: str = "",
        quest_type: QuestType = QuestType.FETCH,
        giver: str = None,  # NPC who gives the quest
        status: QuestStatus = QuestStatus.NOT_STARTED,
        trigger_conditions: List[QuestCondition] = None,
        completion_conditions: List[QuestCondition] = None,
        failure_conditions: List[QuestCondition] = None,
        success_consequences: List[QuestConsequence] = None,
        failure_consequences: List[QuestConsequence] = None,
        parent_quest_id: str = None,  # For sub-quests
        sub_quest_ids: List[str] = None,  # For parent quests
        expiration_turn: int = None,  # Game turn when the quest expires
        hidden: bool = False,  # If True, quest is not shown in quest log until triggered
        achievements: List[
            str
        ] = None,  # Achievements unlocked by completing this quest
    ):
        """
        Initialize a quest.

        Args:
            quest_id: Unique identifier for the quest
            title: Title of the quest
            description: Description of the quest
            quest_type: Type of quest
            giver: NPC who gives the quest
            status: Current status of the quest
            trigger_conditions: Conditions that trigger the quest
            completion_conditions: Conditions that must be met to complete the quest
            failure_conditions: Conditions that cause the quest to fail
            success_consequences: Consequences of completing the quest
            failure_consequences: Consequences of failing the quest
            parent_quest_id: ID of the parent quest (if this is a sub-quest)
            sub_quest_ids: IDs of sub-quests (if this is a parent quest)
            expiration_turn: Game turn when the quest expires
            hidden: If True, quest is not shown in quest log until triggered
        """
        self.quest_id = quest_id if quest_id else str(uuid.uuid4())
        self.title = title
        self.description = description
        self.quest_type = quest_type
        self.giver = giver
        self.status = status
        self.trigger_conditions = trigger_conditions or []
        self.completion_conditions = completion_conditions or []
        self.failure_conditions = failure_conditions or []
        self.success_consequences = success_consequences or []
        self.failure_consequences = failure_consequences or []
        self.parent_quest_id = parent_quest_id
        self.sub_quest_ids = sub_quest_ids or []
        self.expiration_turn = expiration_turn
        self.hidden = hidden
        self.achievements = (
            achievements or []
        )  # Achievements unlocked by completing this quest

        # Additional tracking data
        self.turn_started = None
        self.turn_completed = None
        self.turn_failed = None
        self.notes = []  # For tracking quest progress or hints

    def check_trigger(self, game_state) -> bool:
        """
        Check if the quest should be triggered based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            Boolean indicating if the quest should be triggered
        """
        # If there are no trigger conditions, the quest is always triggered
        if not self.trigger_conditions:
            return True

        # All trigger conditions must be met
        return all(condition.check(game_state) for condition in self.trigger_conditions)

    def check_completion(self, game_state) -> bool:
        """
        Check if the quest has been completed based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            Boolean indicating if the quest has been completed
        """
        # All completion conditions must be met
        return all(
            condition.check(game_state) for condition in self.completion_conditions
        )

    def check_failure(self, game_state) -> bool:
        """
        Check if the quest has failed based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            Boolean indicating if the quest has failed
        """
        # If there are no failure conditions, the quest cannot fail
        if not self.failure_conditions:
            return False

        # Any failure condition being met causes the quest to fail
        return any(condition.check(game_state) for condition in self.failure_conditions)

    def apply_success_consequences(self, game_state) -> None:
        """
        Apply the consequences of completing the quest.

        Args:
            game_state: The current game state
        """
        for consequence in self.success_consequences:
            consequence.apply(game_state)

        # Apply achievements if any
        if self.achievements and hasattr(game_state, "player_achievements"):
            for achievement in self.achievements:
                if achievement not in game_state.player_achievements:
                    game_state.player_achievements.append(achievement)
                    # Log the achievement
                    if hasattr(game_state, "player_actions"):
                        game_state.player_actions.append(
                            f"Achievement unlocked: {achievement}"
                        )

    def apply_failure_consequences(self, game_state) -> None:
        """
        Apply the consequences of failing the quest.

        Args:
            game_state: The current game state
        """
        for consequence in self.failure_consequences:
            consequence.apply(game_state)

    def update(self, game_state) -> bool:
        """
        Update the quest status based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            Boolean indicating if the quest status changed
        """
        # If the quest is not started, check if it should be triggered
        if self.status == QuestStatus.NOT_STARTED and self.check_trigger(game_state):
            self.status = QuestStatus.IN_PROGRESS
            self.turn_started = game_state.game_turn
            return True

        # If the quest is in progress, check if it has been completed or failed
        if self.status == QuestStatus.IN_PROGRESS:
            # Check for failure first
            if self.check_failure(game_state):
                self.status = QuestStatus.FAILED
                self.turn_failed = game_state.game_turn
                self.apply_failure_consequences(game_state)
                return True

            # Then check for completion
            if self.check_completion(game_state):
                self.status = QuestStatus.COMPLETED
                self.turn_completed = game_state.game_turn
                self.apply_success_consequences(game_state)
                return True

            # Check for expiration
            if (
                self.expiration_turn is not None
                and game_state.game_turn >= self.expiration_turn
            ):
                self.status = QuestStatus.FAILED
                self.turn_failed = game_state.game_turn
                self.apply_failure_consequences(game_state)
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the quest to a dictionary for saving.

        Returns:
            Dictionary representation of the quest
        """
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "quest_type": self.quest_type.value,
            "giver": self.giver,
            "status": self.status.value,
            "parent_quest_id": self.parent_quest_id,
            "sub_quest_ids": self.sub_quest_ids,
            "expiration_turn": self.expiration_turn,
            "hidden": self.hidden,
            "achievements": self.achievements,
            "turn_started": self.turn_started,
            "turn_completed": self.turn_completed,
            "turn_failed": self.turn_failed,
            "notes": self.notes,
            # We don't save conditions and consequences as they contain functions
            # Instead, these would be reconstructed when loading quests
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quest":
        """
        Create a quest from a dictionary.

        Args:
            data: Dictionary representation of the quest

        Returns:
            Quest object
        """
        quest = cls(
            quest_id=data["quest_id"],
            title=data["title"],
            description=data["description"],
            quest_type=QuestType(data["quest_type"]),
            giver=data["giver"],
            status=QuestStatus(data["status"]),
            parent_quest_id=data.get("parent_quest_id"),
            sub_quest_ids=data.get("sub_quest_ids", []),
            expiration_turn=data.get("expiration_turn"),
            hidden=data.get("hidden", False),
            achievements=data.get("achievements", []),
        )

        quest.turn_started = data.get("turn_started")
        quest.turn_completed = data.get("turn_completed")
        quest.turn_failed = data.get("turn_failed")
        quest.notes = data.get("notes", [])

        return quest


class FetchQuest(Quest):
    """Quest to retrieve an item and bring it to an NPC."""

    def __init__(self, item_to_fetch: str, recipient: str, **kwargs):
        """
        Initialize a fetch quest.

        Args:
            item_to_fetch: Name of the item to fetch
            recipient: NPC to bring the item to
            **kwargs: Additional arguments for the base Quest class
        """
        # Set default quest type
        kwargs["quest_type"] = QuestType.FETCH

        # Create default completion conditions if not provided
        if "completion_conditions" not in kwargs:
            kwargs["completion_conditions"] = [
                QuestCondition("has_item", item_to_fetch),
                QuestCondition("at_location", recipient),
            ]

        super().__init__(**kwargs)

        self.item_to_fetch = item_to_fetch
        self.recipient = recipient


class LocationQuest(Quest):
    """Quest to travel to a specific location."""

    def __init__(self, target_location: str, **kwargs):
        """
        Initialize a location quest.

        Args:
            target_location: Location to travel to
            **kwargs: Additional arguments for the base Quest class
        """
        # Set default quest type
        kwargs["quest_type"] = QuestType.LOCATION

        # Create default completion conditions if not provided
        if "completion_conditions" not in kwargs:
            kwargs["completion_conditions"] = [
                QuestCondition("at_location", target_location)
            ]

        super().__init__(**kwargs)

        self.target_location = target_location


class CombatQuest(Quest):
    """Quest to defeat a specific enemy."""

    def __init__(self, target_enemy: str, **kwargs):
        """
        Initialize a combat quest.

        Args:
            target_enemy: Enemy to defeat
            **kwargs: Additional arguments for the base Quest class
        """
        # Set default quest type
        kwargs["quest_type"] = QuestType.COMBAT

        # Create default completion conditions if not provided
        if "completion_conditions" not in kwargs:
            kwargs["completion_conditions"] = [
                QuestCondition("defeated_enemy", target_enemy)
            ]

        super().__init__(**kwargs)

        self.target_enemy = target_enemy


class InformationQuest(Quest):
    """Quest to deliver information between NPCs."""

    def __init__(self, information: str, source: str, target: str, **kwargs):
        """
        Initialize an information quest.

        Args:
            information: The information to deliver
            source: NPC who provides the information
            target: NPC to deliver the information to
            **kwargs: Additional arguments for the base Quest class
        """
        # Set default quest type
        kwargs["quest_type"] = QuestType.INFORMATION

        # Create default completion conditions if not provided
        if "completion_conditions" not in kwargs:
            kwargs["completion_conditions"] = [
                QuestCondition("talked_to_npc", source),
                QuestCondition("has_information", information),
                QuestCondition("talked_to_npc", target),
            ]

        super().__init__(**kwargs)

        self.information = information
        self.source = source
        self.target = target


class QuestManager:
    """Class to manage all quests in the game."""

    def __init__(self):
        """Initialize the quest manager."""
        self.quests = {}  # Dict of quest_id -> Quest

    def add_quest(self, quest: Quest) -> None:
        """
        Add a quest to the manager.

        Args:
            quest: Quest to add
        """
        self.quests[quest.quest_id] = quest

        # If this is a sub-quest, add it to the parent's sub_quest_ids
        if quest.parent_quest_id and quest.parent_quest_id in self.quests:
            parent = self.quests[quest.parent_quest_id]
            if quest.quest_id not in parent.sub_quest_ids:
                parent.sub_quest_ids.append(quest.quest_id)

    def remove_quest(self, quest_id: str) -> None:
        """
        Remove a quest from the manager.

        Args:
            quest_id: ID of the quest to remove
        """
        if quest_id in self.quests:
            quest = self.quests[quest_id]

            # Remove from parent's sub_quest_ids
            if quest.parent_quest_id and quest.parent_quest_id in self.quests:
                parent = self.quests[quest.parent_quest_id]
                if quest_id in parent.sub_quest_ids:
                    parent.sub_quest_ids.remove(quest_id)

            # Remove all sub-quests
            for sub_quest_id in quest.sub_quest_ids[
                :
            ]:  # Copy to avoid modification during iteration
                self.remove_quest(sub_quest_id)

            # Remove the quest itself
            del self.quests[quest_id]

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """
        Get a quest by ID.

        Args:
            quest_id: ID of the quest to get

        Returns:
            Quest object or None if not found
        """
        return self.quests.get(quest_id)

    def get_active_quests(self) -> List[Quest]:
        """
        Get all active quests.

        Returns:
            List of active quests
        """
        return [
            q
            for q in self.quests.values()
            if q.status == QuestStatus.IN_PROGRESS and not q.hidden
        ]

    def get_completed_quests(self) -> List[Quest]:
        """
        Get all completed quests.

        Returns:
            List of completed quests
        """
        return [
            q
            for q in self.quests.values()
            if q.status == QuestStatus.COMPLETED and not q.hidden
        ]

    def get_failed_quests(self) -> List[Quest]:
        """
        Get all failed quests.

        Returns:
            List of failed quests
        """
        return [
            q
            for q in self.quests.values()
            if q.status == QuestStatus.FAILED and not q.hidden
        ]

    def update_quests(self, game_state) -> List[Quest]:
        """
        Update all quests based on the current game state.

        Args:
            game_state: The current game state

        Returns:
            List of quests whose status changed
        """
        changed_quests = []

        for quest in self.quests.values():
            if quest.update(game_state):
                changed_quests.append(quest)

                # If this is a parent quest that completed or failed,
                # update the status of all sub-quests
                if quest.sub_quest_ids and quest.status in [
                    QuestStatus.COMPLETED,
                    QuestStatus.FAILED,
                ]:
                    for sub_quest_id in quest.sub_quest_ids:
                        sub_quest = self.get_quest(sub_quest_id)
                        if sub_quest and sub_quest.status == QuestStatus.IN_PROGRESS:
                            # Fail or complete sub-quests based on parent status
                            sub_quest.status = quest.status
                            if quest.status == QuestStatus.COMPLETED:
                                sub_quest.turn_completed = game_state.game_turn
                            else:
                                sub_quest.turn_failed = game_state.game_turn
                            changed_quests.append(sub_quest)

        return changed_quests

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert all quests to a dictionary for saving.

        Returns:
            Dictionary of quest_id -> quest_dict
        """
        return {quest_id: quest.to_dict() for quest_id, quest in self.quests.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> "QuestManager":
        """
        Create a quest manager from a dictionary.

        Args:
            data: Dictionary of quest_id -> quest_dict

        Returns:
            QuestManager object
        """
        manager = cls()

        for quest_id, quest_data in data.items():
            quest_type = QuestType(quest_data["quest_type"])

            if quest_type == QuestType.FETCH:
                # We need to reconstruct the FetchQuest with its specific attributes
                # This would require additional data in the quest_data
                quest = FetchQuest(
                    item_to_fetch=quest_data.get("item_to_fetch", ""),
                    recipient=quest_data.get("recipient", ""),
                    **{
                        k: v
                        for k, v in quest_data.items()
                        if k not in ["item_to_fetch", "recipient"]
                    },
                )
            elif quest_type == QuestType.LOCATION:
                quest = LocationQuest(
                    target_location=quest_data.get("target_location", ""),
                    **{k: v for k, v in quest_data.items() if k != "target_location"},
                )
            elif quest_type == QuestType.COMBAT:
                quest = CombatQuest(
                    target_enemy=quest_data.get("target_enemy", ""),
                    **{k: v for k, v in quest_data.items() if k != "target_enemy"},
                )
            elif quest_type == QuestType.INFORMATION:
                quest = InformationQuest(
                    information=quest_data.get("information", ""),
                    source=quest_data.get("source", ""),
                    target=quest_data.get("target", ""),
                    **{
                        k: v
                        for k, v in quest_data.items()
                        if k not in ["information", "source", "target"]
                    },
                )
            else:
                quest = Quest.from_dict(quest_data)

            manager.add_quest(quest)

        return manager
