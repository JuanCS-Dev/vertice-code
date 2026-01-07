"""
Intelligent Model Router
Routes requests to optimal LLM based on intent, complexity, and cost

Strategy:
- Simple queries → Claude Haiku (fast + cheap)
- Medium complexity → Claude Sonnet (balanced)
- Complex reasoning → Claude Opus (powerful)
- Voice/Audio → GPT-4o Realtime or Gemini Live

Cost comparison (per 1M tokens):
- Haiku:  $0.25 input / $1.25 output
- Sonnet: $3 input / $15 output
- Opus:   $15 input / $75 output

Reference: https://www.anthropic.com/pricing
"""

from typing import List, Literal
from enum import Enum
import re
import logging


# Simple message type for routing
class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tiers by capability and cost"""

    FAST = "claude-3-5-haiku-20241022"  # Fastest, cheapest
    BALANCED = "claude-sonnet-4-5-20250901"  # Best balance
    POWERFUL = "claude-opus-4-5-20251101"  # Most capable


class IntentType(str, Enum):
    """User intent classification"""

    SIMPLE_QUERY = "simple"
    CODE_GENERATION = "code"
    COMPLEX_REASONING = "reasoning"
    LONG_CONTEXT = "long_context"


def classify_intent(messages: List[Message]) -> IntentType:
    """
    Classify user intent from conversation

    Heuristics:
    - Code keywords → CODE_GENERATION
    - Long messages (>1000 chars) → LONG_CONTEXT
    - Question marks, simple queries → SIMPLE_QUERY
    - Otherwise → COMPLEX_REASONING
    """
    latest_message = messages[-1].content.lower()

    # Code indicators
    code_keywords = ["write code", "implement", "function", "class", "debug", "fix bug"]
    if any(kw in latest_message for kw in code_keywords):
        return IntentType.CODE_GENERATION

    # Long context
    total_length = sum(len(msg.content) for msg in messages)
    if total_length >= 10000:  # ~2500 tokens
        return IntentType.LONG_CONTEXT

    # Simple query
    if latest_message.endswith("?") and len(latest_message) < 200:
        return IntentType.SIMPLE_QUERY

    return IntentType.COMPLEX_REASONING


def route_to_model(messages: List[Message], user_id: str) -> str:
    """
    Route to optimal model based on intent and user quota

    Decision tree:
    1. Classify intent
    2. Check user's remaining quota
    3. Select model tier
    4. Return model ID
    """
    intent = classify_intent(messages)

    logger.info(f"Routing user {user_id} with intent {intent}")

    # TODO: Check user quota from DB
    # For now, use intent-based routing

    if intent == IntentType.SIMPLE_QUERY:
        model = ModelTier.FAST
    elif intent == IntentType.CODE_GENERATION:
        model = ModelTier.BALANCED
    elif intent == IntentType.COMPLEX_REASONING:
        model = ModelTier.POWERFUL
    else:  # LONG_CONTEXT
        model = ModelTier.BALANCED  # Sonnet handles 200K context well

    logger.info(f"Selected model: {model}")
    return model.value
