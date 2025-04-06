from enum import IntEnum


class CommandPriority(IntEnum):
    """Priority levels for commands in the queue."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
