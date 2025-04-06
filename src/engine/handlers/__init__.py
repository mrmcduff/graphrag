# engine/handlers/__init__.py
"""Command handlers for different types of player commands."""

from .command_handler import CommandHandler
from .movement_handler import MovementHandler
from .examine_handler import ExamineHandler
from .take_handler import TakeHandler
from .use_handler import UseHandler
from .talk_handler import TalkHandler
from .inventory_handler import InventoryHandler
from .equip_handler import EquipHandler
from .combat_handler import CombatHandler
from .system_handler import SystemHandler
