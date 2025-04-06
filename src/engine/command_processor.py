import random
import os
import sys
from typing import TYPE_CHECKING
from engine.command_queue.command_queue import CommandQueue
from engine.command_registry.command_registry import CommandRegistry
from engine.context.command_context import CommandContext
from engine.feedback.feedback_generator import FeedbackGenerator
from engine.intent_recognition import IntentRecognizer, Intent, IntentType
from engine.feedback import CommandResult, Effect
from engine.handlers import (
    ExamineHandler,
    MovementHandler,
    InventoryHandler,
    TakeHandler,
    UseHandler,
    TalkHandler,
    EquipHandler,
    CombatHandler,
    SystemHandler,
)

if TYPE_CHECKING:
    from game_engine import GameState  # Only imported for type checking
    from graphrag import GraphRAGEngine
    from combat import CombatSystem
    from llm import LLMManager


class CommandProcessor:
    """Process and execute player commands with advanced natural language understanding."""

    def __init__(
        self,
        game_state: "GameState",
        graph_rag_engine: "GraphRAGEngine",
        combat_system: "CombatSystem",
        llm_manager: "LLMManager",
    ):
        """
        Initialize the command processor.

        Args:
            game_state: The current game state
            graph_rag_engine: The GraphRAG engine
            combat_system: The combat system
            llm_manager: The LLM manager
        """
        self.game_state = game_state
        self.graph_rag_engine = graph_rag_engine
        self.combat_system = combat_system
        self.llm_manager = llm_manager

        # Initialize advanced command processing components
        self.intent_recognizer = IntentRecognizer(llm_manager)
        self.command_context = CommandContext(game_state)
        self.command_registry = CommandRegistry(game_state)
        self.feedback_generator = FeedbackGenerator(game_state)

        # Initialize command queue
        self.command_queue = CommandQueue()

        # Register handlers
        self._register_command_handlers()

    def _register_command_handlers(self):
        """Register the command handlers with the registry."""
        # Core handler types
        self.command_registry.register_handler(MovementHandler(self.game_state))
        self.command_registry.register_handler(
            ExamineHandler(self.game_state, self.graph_rag_engine)
        )
        self.command_registry.register_handler(TakeHandler(self.game_state))
        self.command_registry.register_handler(
            UseHandler(self.game_state, self.graph_rag_engine)
        )
        self.command_registry.register_handler(
            TalkHandler(self.game_state, self.graph_rag_engine)
        )
        self.command_registry.register_handler(InventoryHandler(self.game_state))
        self.command_registry.register_handler(
            EquipHandler(self.game_state, self.combat_system)
        )
        self.command_registry.register_handler(
            CombatHandler(self.game_state, self.combat_system)
        )
        self.command_registry.register_handler(SystemHandler(self.game_state))

        # Try to load any custom handlers from plugins
        try:
            plugins_path = os.path.join(
                os.path.dirname(__file__), "..", "plugins", "commands"
            )
            if os.path.exists(plugins_path):
                sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
                self.command_registry.load_handlers_from_module("plugins.commands")
        except Exception as e:
            print(f"Warning: Failed to load command plugins: {e}")

    def setup_llm_provider(self, choice: int) -> None:
        """
        Set up the LLM provider based on user choice.

        Args:
            choice: Integer representing the LLM provider choice (1-6)
        """
        from llm.providers.base import LLMType
        from util.config import get_api_key, load_environment_variables

        # Load environment variables from .env file
        load_environment_variables()

        if choice == 1:
            # Local API
            host = input("Enter host (default: localhost): ") or "localhost"
            port = input("Enter port (default: 8000): ") or "8000"
            self.llm_manager.add_provider(
                LLMType.LOCAL_API,
                self.llm_manager.create_provider(
                    LLMType.LOCAL_API, host=host, port=int(port)
                ),
            )
            self.llm_manager.set_active_provider(LLMType.LOCAL_API)

        elif choice == 2:
            # Local direct
            model_path = input("Enter model path: ")
            self.llm_manager.add_provider(
                LLMType.LOCAL_DIRECT,
                self.llm_manager.create_provider(
                    LLMType.LOCAL_DIRECT, model_path=model_path
                ),
            )
            self.llm_manager.set_active_provider(LLMType.LOCAL_DIRECT)

        elif choice == 3:
            # OpenAI
            api_key = get_api_key("openai")
            if not api_key:
                api_key = input("Enter OpenAI API key: ")
            model = (
                input("Enter model name (default: gpt-3.5-turbo): ") or "gpt-3.5-turbo"
            )
            self.llm_manager.add_provider(
                LLMType.OPENAI,
                self.llm_manager.create_provider(
                    LLMType.OPENAI, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.OPENAI)

        elif choice == 4:
            # Anthropic
            api_key = get_api_key("anthropic")
            if not api_key:
                api_key = input("Enter Anthropic API key: ")
            model = (
                input("Enter model name (default: claude-3-haiku-20240307): ")
                or "claude-3-haiku-20240307"
            )
            self.llm_manager.add_provider(
                LLMType.ANTHROPIC,
                self.llm_manager.create_provider(
                    LLMType.ANTHROPIC, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.ANTHROPIC)

        elif choice == 5:
            # Google
            api_key = get_api_key("google")
            if not api_key:
                api_key = input("Enter Google API key: ")
            model = input("Enter model name (default: gemini-pro): ") or "gemini-pro"
            self.llm_manager.add_provider(
                LLMType.GOOGLE,
                self.llm_manager.create_provider(
                    LLMType.GOOGLE, api_key=api_key, model=model
                ),
            )
            self.llm_manager.set_active_provider(LLMType.GOOGLE)

        else:
            # Rule-based (fallback)
            self.llm_manager.add_provider(
                LLMType.RULE_BASED, self.llm_manager.create_provider(LLMType.RULE_BASED)
            )
            self.llm_manager.set_active_provider(LLMType.RULE_BASED)

    def process_command(self, command: str) -> CommandResult:
        """
        Process a player command with natural language understanding.

        Args:
            command: The player's command string

        Returns:
            CommandResult with the results of the command
        """
        # Check if we're in combat
        if self.combat_system.active_combat:
            return self._process_combat_command(command)

        # Recognize intent
        intents = self.intent_recognizer.recognize(command)
        if not intents:
            # No intent recognized
            return CommandResult(
                success=False,
                message="I don't understand that command.",
                action_type="unknown",
            )

        # Get highest confidence intent
        intent = intents[0]

        # Get handler for the intent
        handler = self.command_registry.get_handler_for_intent(intent)

        if handler:
            # Process with the appropriate handler
            basic_result = handler.handle(intent, self.command_context)
        else:
            # No handler found, use GraphRAG fallback
            response = self.graph_rag_engine.generate_response(command, self.game_state)
            basic_result = {
                "success": True,
                "message": response,
                "action_type": "narrative",
            }

        # Generate detailed feedback
        result = self.feedback_generator.generate_feedback(
            command, intent, basic_result
        )

        # Update game turn only if action was successful
        if result.success:
            self.game_state.game_turn += 1

            # Queue any delayed effects
            for effect in result.effects:
                if effect.delay > 0:
                    self.command_queue.enqueue(
                        self._process_delayed_effect, args=(effect,), delay=effect.delay
                    )

        return result

    def _process_combat_command(self, command: str) -> CommandResult:
        """
        Process commands during active combat.

        Args:
            command: The combat command

        Returns:
            CommandResult with the results of the combat action
        """
        # Recognize intent in combat context
        intents = self.intent_recognizer.recognize(command)
        intent = (
            intents[0]
            if intents
            else Intent(
                type=IntentType.UNKNOWN,
                confidence=0.1,
                parameters={},
                original_text=command,
            )
        )

        # Very simple routing based on intent type
        if intent.type in [IntentType.ATTACK, IntentType.USE]:
            target = intent.parameters.get("target", "")

            # Process combat action
            result = self.combat_system.process_combat_action(
                intent.type.name.lower(), target
            )

            # Convert to CommandResult
            combat_message = "\n".join(result.get("combat_log", []))

            cmd_result = CommandResult(
                success=result.get("success", False),
                message=combat_message or result.get("message", ""),
                action_type="combat",
            )

            # Add combat-specific effects
            if "player_health" in result:
                cmd_result.add_effect(
                    Effect(
                        type="state_change",
                        entity_type="player",
                        property="health",
                        new_value=result["player_health"],
                        description="Your health changed.",
                    )
                )

            if "enemy_health" in result:
                cmd_result.add_effect(
                    Effect(
                        type="state_change",
                        entity_type="enemy",
                        property="health",
                        new_value=result["enemy_health"],
                        description="Enemy health changed.",
                    )
                )

            # Check if combat has ended
            is_active = result.get("combat_status", "") == "active"
            if not is_active:
                combat_result = None
                if result.get("combat_status") == "player_victory":
                    combat_result = "victory"
                elif result.get("combat_status") == "player_defeated":
                    combat_result = "defeat"
                elif result.get("combat_status") == "player_fled":
                    combat_result = "fled"

                cmd_result.add_effect(
                    Effect(
                        type="state_change",
                        entity_type="combat",
                        property="active",
                        new_value=False,
                        description=f"Combat ended with {combat_result}.",
                    )
                )

            return cmd_result

        elif intent.type == IntentType.QUIT or intent.original_text.lower() == "flee":
            # Handle fleeing
            success = random.random() > 0.5  # 50% chance to flee

            if success:
                self.combat_system.active_combat = None
                return CommandResult(
                    success=True,
                    message="You successfully flee from combat!",
                    action_type="combat",
                    effects=[
                        Effect(
                            type="state_change",
                            entity_type="combat",
                            property="active",
                            new_value=False,
                            description="Combat ended with fled.",
                        )
                    ],
                )
            else:
                # Failed to flee
                result = self.combat_system.process_enemy_action()
                return CommandResult(
                    success=False,
                    message=f"You fail to escape! {result.get('message', '')}",
                    action_type="combat",
                )

        # Default response for unknown combat commands
        return CommandResult(
            success=False,
            message="Invalid combat command. You can 'attack', 'use [item]', or 'flee'.",
            action_type="combat",
            alternatives=["attack", "use health potion", "flee"],
        )

    def _process_delayed_effect(self, effect: Effect) -> CommandResult:
        """
        Process a delayed effect.

        Args:
            effect: The effect to process

        Returns:
            CommandResult representing the effect
        """
        # Apply the effect to the game state
        if effect.entity_type and effect.entity_id and effect.property:
            # TODO: Implement proper state updates for delayed effects
            pass

        # Return a command result for the effect
        return CommandResult(
            success=True,
            message=effect.description or "Something changes in the world.",
            effects=[effect],
        )
