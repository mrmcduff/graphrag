import re
from typing import Dict, List

from engine.intent_recognition import Intent, IntentType


class IntentRecognizer:
    """Recognizes intents from natural language input."""

    def __init__(self, llm_manager=None):
        """
        Initialize the intent recognizer.

        Args:
            llm_manager: Optional LLM manager for advanced recognition
        """
        self.llm_manager = llm_manager
        self.patterns = self._init_patterns()
        self.keywords = self._init_keywords()
        # Track context for better recognition
        self.recent_intents = []

    def _init_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize regex patterns for each intent type."""
        return {
            IntentType.MOVE: [
                r"(?:go|move|walk|run|travel)(?:\s+to)?\s+(.+)",
                r"go (\w+)",
                r"^(?:north|south|east|west|n|s|e|w)$",
            ],
            IntentType.EXAMINE: [
                r"(?:look|examine|inspect|check)(?:\s+at)?\s+(.+)",
                r"^look$",
            ],
            IntentType.TAKE: [
                r"(?:take|get|grab|pick up)\s+(.+)",
            ],
            IntentType.USE: [
                r"(?:use|activate|apply)\s+(.+(?:\s+on\s+.+)?)",
            ],
            IntentType.TALK: [
                r"(?:talk|speak|chat)(?:\s+to)?\s+(.+)",
            ],
            IntentType.ATTACK: [
                r"(?:attack|fight|hit|strike)\s+(.+)",
            ],
            IntentType.INVENTORY: [
                r"^(?:inventory|items|i)$",
            ],
            IntentType.EQUIP: [
                r"(?:equip|wear|wield)\s+(.+)",
            ],
            IntentType.HELP: [
                r"^(?:help|commands|\?)$",
            ],
            IntentType.QUIT: [
                r"^(?:quit|exit|bye)$",
            ],
            IntentType.SAVE: [
                r"save(?:\s+(?:game|to))?(?:\s+(.+))?",
            ],
            IntentType.LOAD: [
                r"load(?:\s+(?:game|from))?(?:\s+(.+))?",
            ],
            IntentType.MAP: [
                r"^(?:map|world(?:\s+map)?|local(?:\s+map)?)$",
            ],
        }

    def _init_keywords(self) -> Dict[IntentType, List[str]]:
        """Initialize keywords associated with each intent type."""
        return {
            IntentType.MOVE: [
                "go",
                "move",
                "walk",
                "travel",
                "north",
                "south",
                "east",
                "west",
            ],
            IntentType.EXAMINE: ["look", "examine", "inspect", "check", "see"],
            IntentType.TAKE: ["take", "get", "grab", "pick"],
            IntentType.USE: ["use", "activate", "apply"],
            IntentType.TALK: ["talk", "speak", "chat", "converse"],
            IntentType.ATTACK: ["attack", "fight", "hit", "strike"],
            IntentType.INVENTORY: ["inventory", "items", "i"],
            IntentType.EQUIP: ["equip", "wear", "wield"],
            IntentType.HELP: ["help", "commands", "?"],
            IntentType.QUIT: ["quit", "exit", "bye"],
            IntentType.SAVE: ["save"],
            IntentType.LOAD: ["load"],
            IntentType.MAP: ["map"],
        }

    def recognize(self, text: str) -> List[Intent]:
        """
        Recognize intents from the input text.
        Returns a list of potential intents, sorted by confidence.
        """
        # Start with pattern-based recognition
        pattern_intents = self._pattern_recognition(text)

        # Keyword-based recognition as fallback
        keyword_intents = self._keyword_recognition(text)

        # Combine and sort by confidence
        all_intents = pattern_intents + keyword_intents

        # Remove duplicates (keep highest confidence for each intent type)
        unique_intents = {}
        for intent in all_intents:
            if (
                intent.type not in unique_intents
                or intent.confidence > unique_intents[intent.type].confidence
            ):
                unique_intents[intent.type] = intent

        # Convert back to list and sort by confidence
        all_intents = list(unique_intents.values())
        all_intents.sort(key=lambda x: x.confidence, reverse=True)

        # If we have an LLM available and no high-confidence intents,
        # use it for more advanced recognition
        if self.llm_manager and (not all_intents or all_intents[0].confidence < 0.8):
            llm_intent = self._llm_recognition(text, all_intents)
            if llm_intent:
                # Insert LLM intent at the beginning if it has higher confidence
                if not all_intents or llm_intent.confidence > all_intents[0].confidence:
                    all_intents = [llm_intent] + all_intents
                else:
                    all_intents.append(llm_intent)
                    all_intents.sort(key=lambda x: x.confidence, reverse=True)

        # If we still have no intents, create an UNKNOWN intent
        if not all_intents:
            all_intents = [
                Intent(
                    type=IntentType.UNKNOWN,
                    confidence=0.1,
                    parameters={},
                    original_text=text,
                )
            ]

        # Update recent intents
        if all_intents:
            self.recent_intents.append(all_intents[0])
            if len(self.recent_intents) > 5:  # Keep only 5 most recent
                self.recent_intents.pop(0)

        return all_intents

    def _pattern_recognition(self, text: str) -> List[Intent]:
        """Recognize intents using regex patterns."""
        intents = []

        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    confidence = 0.9  # High confidence for exact pattern matches
                    parameters = {}

                    # Extract parameters from groups
                    groups = match.groups()
                    if groups:
                        if intent_type == IntentType.MOVE:
                            parameters["direction"] = groups[0]
                        elif intent_type == IntentType.EXAMINE:
                            parameters["target"] = (
                                groups[0] if groups else "surroundings"
                            )
                        elif intent_type == IntentType.TAKE:
                            parameters["item"] = groups[0]
                        elif intent_type == IntentType.USE:
                            use_parts = groups[0].split(" on ")
                            parameters["item"] = use_parts[0]
                            if len(use_parts) > 1:
                                parameters["target"] = use_parts[1]
                        elif intent_type == IntentType.TALK:
                            parameters["character"] = groups[0]
                        elif intent_type == IntentType.ATTACK:
                            parameters["target"] = groups[0]
                        elif intent_type == IntentType.EQUIP:
                            parameters["item"] = groups[0]
                        elif intent_type == IntentType.SAVE:
                            if groups[0]:
                                parameters["filename"] = groups[0]
                        elif intent_type == IntentType.LOAD:
                            if groups[0]:
                                parameters["filename"] = groups[0]

                    intents.append(
                        Intent(
                            type=intent_type,
                            confidence=confidence,
                            parameters=parameters,
                            original_text=text,
                        )
                    )

        return intents

    def _keyword_recognition(self, text: str) -> List[Intent]:
        """Recognize intents based on keyword presence."""
        intents = []
        words = text.lower().split()

        for intent_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in words:
                    # Calculate confidence based on keyword relevance
                    confidence = 0.6  # Medium confidence for keyword matches

                    # Extract potential parameters
                    parameters = {}
                    keyword_index = words.index(keyword)

                    if (
                        intent_type == IntentType.MOVE
                        and keyword_index < len(words) - 1
                    ):
                        parameters["direction"] = words[keyword_index + 1]
                    elif (
                        intent_type == IntentType.EXAMINE
                        and keyword_index < len(words) - 1
                    ):
                        parameters["target"] = " ".join(words[keyword_index + 1 :])
                    elif (
                        intent_type == IntentType.TAKE
                        and keyword_index < len(words) - 1
                    ):
                        parameters["item"] = " ".join(words[keyword_index + 1 :])
                    elif (
                        intent_type == IntentType.USE and keyword_index < len(words) - 1
                    ):
                        use_text = " ".join(words[keyword_index + 1 :])
                        use_parts = use_text.split(" on ")
                        parameters["item"] = use_parts[0]
                        if len(use_parts) > 1:
                            parameters["target"] = use_parts[1]
                    elif (
                        intent_type == IntentType.TALK
                        and keyword_index < len(words) - 1
                    ):
                        parameters["character"] = " ".join(words[keyword_index + 1 :])
                    elif (
                        intent_type == IntentType.ATTACK
                        and keyword_index < len(words) - 1
                    ):
                        parameters["target"] = " ".join(words[keyword_index + 1 :])
                    elif (
                        intent_type == IntentType.EQUIP
                        and keyword_index < len(words) - 1
                    ):
                        parameters["item"] = " ".join(words[keyword_index + 1 :])

                    intents.append(
                        Intent(
                            type=intent_type,
                            confidence=confidence,
                            parameters=parameters,
                            original_text=text,
                        )
                    )

        return intents

    def _llm_recognition(
        self, text: str, existing_intents: List[Intent]
    ) -> Optional[Intent]:
        """Use LLM for advanced intent recognition when pattern/keyword matching is insufficient."""
        if not self.llm_manager:
            return None

        # Construct prompt for LLM
        intent_types = [
            intent.name for intent in IntentType if intent != IntentType.UNKNOWN
        ]

        prompt = f"""
        I need to understand the player's intent in this text adventure game command:

        "{text}"

        Possible intents are: {", ".join(intent_types)}

        Respond with:
        1. The most likely intent
        2. A confidence score (0.0-1.0)
        3. Any parameters extracted from the command

        Format: INTENT|CONFIDENCE|PARAM1:VALUE1|PARAM2:VALUE2
        """

        try:
            # Generate response using LLM
            response = self.llm_manager.generate_text(prompt, max_tokens=100)

            # Parse response
            parts = response.strip().split("|")
            if len(parts) >= 2:
                intent_name = parts[0].strip().upper()
                try:
                    intent_type = IntentType[intent_name]
                    confidence = float(parts[1])

                    # Parse parameters
                    parameters = {}
                    if len(parts) > 2:
                        for param_part in parts[2:]:
                            if ":" in param_part:
                                param_name, param_value = param_part.split(":", 1)
                                parameters[param_name.strip()] = param_value.strip()

                    return Intent(
                        type=intent_type,
                        confidence=confidence,
                        parameters=parameters,
                        original_text=text,
                    )
                except (KeyError, ValueError):
                    pass  # Invalid intent type or confidence value
        except Exception:
            pass  # LLM generation failed

        return None
