# engine/command_registry/__init__.py
"""Extensible command registry for plugin-based architecture."""

from .command_category import CommandCategory
from .command_registry import CommandRegistry

__all__ = ["CommandCategory", "CommandRegistry"]
