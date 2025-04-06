import textwrap
from typing import Any, Dict
from src.engine.feedback.command_result import CommandResult


class OutputManager:
    """Manages the display of command results."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the output manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.width = self.config.get("width", 80)
        self.use_color = self.config.get("use_color", True)
        self.typing_effect = self.config.get("typing_effect", False)
        self.typing_speed = self.config.get("typing_speed", 0.02)

    def display_result(self, result: CommandResult) -> None:
        """
        Display a command result to the player.

        Args:
            result: The command result to display
        """
        if result.feedback_type == "text":
            self._display_text_result(result)
        elif result.feedback_type == "visual":
            self._display_visual_result(result)
        # Handle other feedback types...

    def _display_text_result(self, result: CommandResult) -> None:
        """
        Display a text-based command result.

        Args:
            result: The command result to display
        """
        import time

        # Format the message with word wrapping
        wrapped_message = textwrap.fill(result.message, width=self.width)

        # Apply color if enabled
        if self.use_color:
            try:
                import colorama

                colorama.init()

                # Use color based on success/failure
                if result.success:
                    color = colorama.Fore.GREEN
                else:
                    color = colorama.Fore.RED

                wrapped_message = f"{color}{wrapped_message}{colorama.Style.RESET_ALL}"
            except ImportError:
                # Continue without color if colorama isn't available
                pass

        # Display with typing effect if enabled
        if self.typing_effect:
            for char in wrapped_message:
                print(char, end="", flush=True)
                time.sleep(self.typing_speed)
            print()
        else:
            print(wrapped_message)

        # Display alternatives if the command failed
        if not result.success and result.alternatives:
            print("\nDid you mean:")
            for alternative in result.alternatives[:3]:  # Show up to 3 alternatives
                print(f"  - {alternative}")

    def _display_visual_result(self, result: CommandResult) -> None:
        """
        Display a visual result (e.g., ASCII art, map).

        Args:
            result: The command result to display
        """
        print(result.message)

        # If there are additional visual elements
        for effect in result.effects:
            if effect.type == "visual" and effect.description:
                print(effect.description)

    def display_text(self, text: str) -> None:
        """
        Display plain text to the player.

        Args:
            text: The text to display
        """
        wrapped_text = textwrap.fill(text, width=self.width)

        if self.typing_effect:
            import time

            for char in wrapped_text:
                print(char, end="", flush=True)
                time.sleep(self.typing_speed)
            print()
        else:
            print(wrapped_text)
