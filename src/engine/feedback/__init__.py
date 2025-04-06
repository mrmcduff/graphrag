# engine/feedback/__init__.py
"""Enhanced feedback system for command results."""

from .command_result import CommandResult
from .effect import Effect
from .feedback_generator import FeedbackGenerator

__all__ = ["CommandResult", "Effect", "FeedbackGenerator"]
