import os
import textwrap
import time
from typing import Dict, Any, Optional


class OutputManager:
    """Class to handle formatting and display of game output."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the output manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Set default configuration values
        self.width = self.config.get("width", 80)
        self.delay = self.config.get(
            "delay", 0.02
        )  # Delay between characters for typing effect
        self.use_color = self.config.get("use_color", True)
        self.wrap_text = self.config.get("wrap_text", True)

        # Set color codes if color is enabled
        if self.use_color:
            # ANSI color codes
            self.colors = {
                "reset": "\033[0m",
                "bold": "\033[1m",
                "italic": "\033[3m",
                "underline": "\033[4m",
                "black": "\033[30m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m",
                "bg_black": "\033[40m",
                "bg_red": "\033[41m",
                "bg_green": "\033[42m",
                "bg_yellow": "\033[43m",
                "bg_blue": "\033[44m",
                "bg_magenta": "\033[45m",
                "bg_cyan": "\033[46m",
                "bg_white": "\033[47m",
            }
        else:
            # Empty color codes if color is disabled
            self.colors = {
                k: ""
                for k in [
                    "reset",
                    "bold",
                    "italic",
                    "underline",
                    "black",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                    "bg_black",
                    "bg_red",
                    "bg_green",
                    "bg_yellow",
                    "bg_blue",
                    "bg_magenta",
                    "bg_cyan",
                    "bg_white",
                ]
            }

    def display_text(self, text: str, style: str = "normal") -> None:
        """
        Display text with optional styling and typing effect.

        Args:
            text: The text to display
            style: Style to apply ("normal", "important", "system", "error")
        """
        # Apply styling based on the style parameter
        if style == "important":
            styled_text = f"{self.colors['bold']}{self.colors['yellow']}{text}{self.colors['reset']}"
        elif style == "system":
            styled_text = f"{self.colors['italic']}{self.colors['cyan']}{text}{self.colors['reset']}"
        elif style == "error":
            styled_text = (
                f"{self.colors['bold']}{self.colors['red']}{text}{self.colors['reset']}"
            )
        else:
            styled_text = text

        # Wrap text if enabled
        if self.wrap_text:
            lines = []
            for line in styled_text.split("\n"):
                if line.strip():
                    lines.extend(textwrap.wrap(line, width=self.width))
                else:
                    lines.append("")
            wrapped_text = "\n".join(lines)
        else:
            wrapped_text = styled_text

        # Display text with typing effect if delay is > 0
        if self.delay > 0 and style != "system":
            for char in wrapped_text:
                print(char, end="", flush=True)
                time.sleep(self.delay)
            print()
        else:
            print(wrapped_text)

    def display_result(self, result: Dict[str, Any]) -> None:
        """
        Display the result of a command.

        Args:
            result: Dictionary with command result information
        """
        # Extract key information from the result
        message = result.get("message", "")
        success = result.get("success", False)
        action_type = result.get("action_type", "unknown")

        # Handle different result types
        if action_type == "combat" and "combat_active" in result:
            # Combat result
            if result["combat_active"]:
                # Active combat
                self.display_text(message)

                # Display health if available
                if "player_health" in result and "enemy_health" in result:
                    enemy = result.get("enemy", "Enemy")
                    health_display = (
                        f"\nYou: {result['player_health']} HP | "
                        f"{enemy}: {result['enemy_health']} HP"
                    )
                    self.display_text(health_display, "system")
            else:
                # Combat ended
                style = (
                    "important" if result.get("combat_result") == "victory" else "error"
                )
                self.display_text(message, style)

        elif action_type == "inventory":
            # Inventory result
            self.display_text(message, "system")

        elif action_type == "system":
            # System command result
            if result.get("help_displayed", False):
                # Help text gets special formatting
                self.display_text(message, "system")
            elif not success:
                # Failed system command
                self.display_text(message, "error")
            else:
                # Successful system command
                self.display_text(message, "system")

        elif action_type == "movement":
            # Movement result
            if success:
                self.display_text(message)
            else:
                self.display_text(message, "error")

        elif action_type == "narrative":
            # Narrative or descriptive text
            self.display_text(message)

        else:
            # Default handling
            if success:
                self.display_text(message)
            else:
                self.display_text(message, "error")

    def display_separator(self) -> None:
        """Display a separator line."""
        if self.use_color:
            separator = f"{self.colors['cyan']}{'-' * self.width}{self.colors['reset']}"
        else:
            separator = "-" * self.width
        print(separator)

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")
