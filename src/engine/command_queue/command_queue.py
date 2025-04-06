from dataclasses import dataclass
from typing import Callable, Any, List, Optional
import time

from command_priority import CommandPriority


@dataclass
class QueuedCommand:
    """A command in the command queue."""

    command_func: Callable
    args: tuple
    kwargs: dict
    priority: CommandPriority
    delay: float  # Delay in seconds before execution
    creation_time: float  # When the command was created

    @property
    def execution_time(self):
        """Calculate when this command should execute."""
        return self.creation_time + self.delay

    def is_ready(self, current_time: float) -> bool:
        """Check if the command is ready to execute."""
        return current_time >= self.execution_time


class CommandQueue:
    """Manages a priority queue of commands."""

    def __init__(self):
        """Initialize the command queue."""
        self.queue: List[QueuedCommand] = []

    def enqueue(
        self,
        command_func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: CommandPriority = CommandPriority.NORMAL,
        delay: float = 0.0,
    ) -> None:
        """
        Add a command to the queue.

        Args:
            command_func: The function to call
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            priority: Priority level for this command
            delay: Delay in seconds before execution
        """
        if kwargs is None:
            kwargs = {}

        queued_command = QueuedCommand(
            command_func=command_func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            delay=delay,
            creation_time=time.time(),
        )

        self.queue.append(queued_command)

        # Sort by priority (highest first), then by execution time (earliest first)
        self.queue.sort(key=lambda cmd: (-cmd.priority, cmd.execution_time))

    def get_next_command(self) -> Optional[QueuedCommand]:
        """
        Get the next command that's ready to execute.
        Returns None if no commands are ready.
        """
        current_time = time.time()

        for i, command in enumerate(self.queue):
            if command.is_ready(current_time):
                return self.queue.pop(i)

        return None

    def process_queue(self) -> List[Any]:
        """
        Process all ready commands in the queue.
        Returns the results of all executed commands.
        """
        results = []

        while True:
            command = self.get_next_command()
            if not command:
                break

            try:
                result = command.command_func(*command.args, **command.kwargs)
                results.append(result)
            except Exception as e:
                # Log the error but continue processing other commands
                print(f"Error executing command: {e}")

        return results

    def clear(self) -> None:
        """Clear all commands from the queue."""
        self.queue.clear()

    def clear_by_type(self, command_type) -> None:
        """Clear all commands of a specific type."""
        self.queue = [
            cmd for cmd in self.queue if not isinstance(cmd.command_func, command_type)
        ]

    def interrupt(self, new_command: QueuedCommand) -> None:
        """
        Interrupt the queue with a high-priority command.
        This clears lower-priority commands and adds the new one.
        """
        # Remove commands with lower priority
        self.queue = [cmd for cmd in self.queue if cmd.priority >= new_command.priority]

        # Add the new command
        self.queue.append(new_command)

        # Re-sort
        self.queue.sort(key=lambda cmd: (-cmd.priority, cmd.execution_time))

    def __len__(self) -> int:
        """Get the number of commands in the queue."""
        return len(self.queue)
