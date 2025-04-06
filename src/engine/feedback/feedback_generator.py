import textwrap

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from engine.feedback import Effect, CommandResult
from engine.intent_recognition import Intent


class FeedbackGenerator:
    """Generates detailed feedback for command results."""

    def __init__(self, game_state):
        """
        Initialize the feedback generator.

        Args:
            game_state: The current game state
        """
        self.game_state = game_state

    def generate_feedback(
        self, command_text: str, intent: Intent, result: Dict[str, Any]
    ) -> CommandResult:
        """
        Generate detailed feedback for a command result.

        Args:
            command_text: Original command text from player
            intent: Recognized intent
            result: Basic result dictionary from command handler

        Returns:
            CommandResult with detailed feedback
        """
        # Extract basic information
        success = result.get("success", False)
        message = result.get("message", "")
        action_type = result.get("action_type", "unknown")

        # Create the command result
        cmd_result = CommandResult(
            success=success, message=message, action_type=action_type
        )

        # Add effects if present
        if "effects" in result:
            for effect_data in result["effects"]:
                effect = Effect(
                    type=effect_data.get("type", "unknown"),
                    entity_type=effect_data.get("entity_type"),
                    entity_id=effect_data.get("entity_id"),
                    property=effect_data.get("property"),
                    old_value=effect_data.get("old_value"),
                    new_value=effect_data.get("new_value"),
                    description=effect_data.get("description"),
                    delay=effect_data.get("delay", 0.0),
                )
                cmd_result.add_effect(effect)

        # Add state change effects based on action type
        self._add_state_change_effects(cmd_result, intent, result)

        # Add alternatives for failed commands
        if not success:
            self._suggest_alternatives(command_text, intent, cmd_result)

        return cmd_result

    def _add_state_change_effects(
        self, cmd_result: CommandResult, intent: Intent, result: Dict[str, Any]
    ) -> None:
        """
        Add state change effects based on the command type and result.

        Args:
            cmd_result: The command result to update
            intent: The recognized intent
            result: The original result dictionary
        """
        if not cmd_result.success:
            return  # No state changes for failed commands

        # Movement effects
        if intent.type == IntentType.MOVE and result.get("new_location"):
            old_location = result.get("old_location", "unknown")
            new_location = result.get("new_location")

            cmd_result.add_effect(
                Effect(
                    type="state_change",
                    entity_type="player",
                    property="location",
                    old_value=old_location,
                    new_value=new_location,
                    description=f"You moved from {old_location} to {new_location}.",
                )
            )

        # Inventory effects
        elif intent.type == IntentType.TAKE and result.get("target"):
            item = result.get("target")

            cmd_result.add_effect(
                Effect(
                    type="state_change",
                    entity_type="inventory",
                    property="items",
                    new_value=item,
                    description=f"Added {item} to your inventory.",
                )
            )

        # Equipment effects
        elif intent.type == IntentType.EQUIP and result.get("equipped"):
            item = result.get("equipped")
            slot = result.get("slot", "unknown")

            cmd_result.add_effect(
                Effect(
                    type="state_change",
                    entity_type="equipment",
                    property=slot,
                    new_value=item,
                    description=f"Equipped {item} as your {slot}.",
                )
            )

        # NPC interaction effects
        elif intent.type == IntentType.TALK and result.get("target"):
            character = result.get("target")

            cmd_result.add_effect(
                Effect(
                    type="state_change",
                    entity_type="npcs",
                    entity_id=character,
                    property="met_player",
                    new_value=True,
                    description=f"You've now met {character}.",
                )
            )

    def _suggest_alternatives(
        self, command_text: str, intent: Intent, cmd_result: CommandResult
    ) -> None:
        """
        Suggest alternative commands when a command fails.

        Args:
            command_text: Original command text
            intent: Recognized intent
            cmd_result: Command result to add alternatives to
        """
        if intent.type == IntentType.MOVE:
            # Suggest valid exits
            current_location = self.game_state.player_location
            location_info = self.game_state._get_location_info(current_location)

            if "connected_locations" in location_info:
                for location in location_info["connected_locations"]:
                    cmd_result.suggest_alternative(f"go to {location}")

        elif intent.type == IntentType.TAKE:
            # Suggest visible items
            current_location = self.game_state.player_location
            location_info = self.game_state._get_location_info(current_location)

            if "items" in location_info:
                for item in location_info["items"]:
                    cmd_result.suggest_alternative(f"take {item}")

        elif intent.type == IntentType.USE:
            # Suggest inventory items
            for item in self.game_state.inventory:
                cmd_result.suggest_alternative(f"use {item}")

        elif intent.type == IntentType.TALK:
            # Suggest NPCs in location
            npcs_here = [
                npc
                for npc, data in self.game_state.npc_states.items()
                if data["location"] == self.game_state.player_location
            ]

            for npc in npcs_here:
                cmd_result.suggest_alternative(f"talk to {npc}")

        # For unknown intents, suggest basic commands
        elif intent.type == IntentType.UNKNOWN:
            cmd_result.suggest_alternative("look around")
            cmd_result.suggest_alternative("inventory")
            cmd_result.suggest_alternative("help")


# class OutputManager:
#     """Manages the display of command results."""

#     def __init__(self, config: Dict[str, Any] = None):
#         """
#         Initialize the output manager.

#         Args:
#             config: Configuration dictionary
#         """
#         self.config = config or {}
#         self.width = self.config.get("width", 80)
#         self.use_color = self.config.get("use_color", True)
#         self.typing_effect = self.config.get("typing_effect", False)
#         self.typing_speed = self.config.get("typing_speed", 0.02)

#     def display_result(self, result: CommandResult) -> None:
#         """
#         Display a command result to the player.

#         Args:
#             result: The command result to display
#         """
#         if result.feedback_type == "text":
#             self._display_text_result(result)
#         elif result.feedback_type == "visual":
#             self._display_visual_result(result)
#         # Handle other feedback types...

#     def _display_text_result(self, result: CommandResult) -> None:
#         """
#         Display a text-based command result.

#         Args:
#             result: The command result to display
#         """
#         import time

#         # Format the message with word wrapping
#         wrapped_message = textwrap.fill(result.message, width=self.width)

#         # Apply color if enabled
#         if self.use_color:
#             try:
#                 import colorama
#                 colorama.init()

#                 # Use color based on success/failure
#                 if result.success:
#                     color = colorama.Fore.GREEN
#                 else:
#                     color = colorama.Fore.RED

#                 wrapped_message = f"{color}{wrapped_message}{colorama.Style.RESET_ALL}"
#             except ImportError:
#                 # Continue without color if colorama isn't available
#                 pass

#         # Display with typing effect if enabled
#         if self.typing_effect:
#             for char in wrapped_message:
#                 print(char, end="", flush=True)
#                 time.sleep(self.typing_speed)
#             print()
#         else:
#             print(wrapped_message)

#         # Display alternatives if the command failed
#         if not result.success and result.alternatives:
#             print("\nDid you mean:")
#             for alternative in result.alternatives[:3]:  # Show up to 3 alternatives
#                 print(f"  - {alternative}")

#     def _display_visual_result(self, result: CommandResult) -> None:
#         """
#         Display a visual result (e.g., ASCII art, map).

#         Args:
#             result: The command result to display
#         """
#         print(result.message)

#         # If there are additional visual elements
#         for effect in result.effects:
#             if effect.type == "visual" and effect.description:
#                 print(effect.description)

#     def display_text(self, text: str) -> None:
#         """
#         Display plain text to the player.

#         Args:
#             text: The text to display
#         """
#         wrapped_text = textwrap.fill(text, width=self.width)

#         if self.typing_effect:
#             import time
#             for char in wrapped_text:
#                 print(char, end="", flush=True)
#                 time.sleep(self.typing_speed)
#             print()
#         else:
#             print(wrapped_text)
