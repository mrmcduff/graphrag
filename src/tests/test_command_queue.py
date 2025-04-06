import unittest
import time
from engine.command_queue.command_priority import CommandPriority
from engine.command_queue.command_queue import CommandQueue, QueuedCommand


class TestCommandQueue(unittest.TestCase):
    def setUp(self):
        self.queue = CommandQueue()

        # Define some test command functions
        def cmd_low(x):
            return f"Low: {x}"

        def cmd_normal(x):
            return f"Normal: {x}"

        def cmd_high(x):
            return f"High: {x}"

        def cmd_critical(x):
            return f"Critical: {x}"

        self.cmd_low = cmd_low
        self.cmd_normal = cmd_normal
        self.cmd_high = cmd_high
        self.cmd_critical = cmd_critical

    def test_enqueue_and_order(self):
        # Enqueue commands with different priorities
        self.queue.enqueue(self.cmd_normal, args=(1,))
        self.queue.enqueue(self.cmd_low, args=(2,), priority=CommandPriority.LOW)
        self.queue.enqueue(self.cmd_high, args=(3,), priority=CommandPriority.HIGH)

        # Check queue length
        self.assertEqual(len(self.queue), 3)

        # Check queue order (should be HIGH, NORMAL, LOW)
        sorted_priorities = [cmd.priority for cmd in self.queue.queue]
        self.assertEqual(
            sorted_priorities,
            [CommandPriority.HIGH, CommandPriority.NORMAL, CommandPriority.LOW],
        )

    def test_delayed_execution(self):
        # Enqueue commands with different delays
        now = time.time()

        self.queue.enqueue(self.cmd_normal, args=(1,), delay=0.5)
        self.queue.enqueue(self.cmd_normal, args=(2,), delay=0.0)  # Immediate

        # Check that only the immediate command is ready
        next_cmd = self.queue.get_next_command()
        self.assertIsNotNone(next_cmd)
        self.assertEqual(next_cmd.args, (2,))

        # Check that delayed command is still in queue
        self.assertEqual(len(self.queue), 1)

        # Wait for delayed command to be ready
        time.sleep(0.6)

        # Now the delayed command should be ready
        next_cmd = self.queue.get_next_command()
        self.assertIsNotNone(next_cmd)
        self.assertEqual(next_cmd.args, (1,))

        # Queue should be empty
        self.assertEqual(len(self.queue), 0)

    def test_process_queue(self):
        # Enqueue multiple commands
        self.queue.enqueue(self.cmd_normal, args=(1,))
        self.queue.enqueue(self.cmd_normal, args=(2,))

        # Process the queue
        results = self.queue.process_queue()

        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results, ["Normal: 1", "Normal: 2"])

        # Queue should be empty
        self.assertEqual(len(self.queue), 0)

    def test_interrupt(self):
        # Set up a queue with lower priority commands
        self.queue.enqueue(self.cmd_normal, args=(1,))
        self.queue.enqueue(self.cmd_low, args=(2,), priority=CommandPriority.LOW)

        # Create a critical command
        critical_cmd = QueuedCommand(
            command_func=self.cmd_critical,
            args=(3,),
            kwargs={},
            priority=CommandPriority.CRITICAL,
            delay=0.0,
            creation_time=time.time(),
        )

        # Interrupt with critical command
        self.queue.interrupt(critical_cmd)

        # Check queue state after interrupt
        self.assertEqual(
            len(self.queue), 2
        )  # Should have removed the LOW priority command

        # Process queue
        results = self.queue.process_queue()

        # Check results - should be CRITICAL then NORMAL
        self.assertEqual(results, ["Critical: 3", "Normal: 1"])


if __name__ == "__main__":
    unittest.main()
