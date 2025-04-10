"""
Debug utility module for controlling debug output.
"""

# Global debug flag
DEBUG_MODE = False


def set_debug_mode(enabled: bool) -> None:
    """
    Set the global debug mode flag.

    Args:
        enabled: Whether debug mode should be enabled
    """
    global DEBUG_MODE
    DEBUG_MODE = enabled


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.

    Returns:
        True if debug mode is enabled, False otherwise
    """
    return DEBUG_MODE


def debug_print(*args, **kwargs) -> None:
    """
    Print debug messages only when debug mode is enabled.

    Args:
        *args: Arguments to pass to print function
        **kwargs: Keyword arguments to pass to print function
    """
    if DEBUG_MODE:
        print(*args, **kwargs)
