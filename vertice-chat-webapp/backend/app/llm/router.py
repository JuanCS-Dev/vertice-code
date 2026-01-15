"""
Intelligent Model Router
Routes requests to optimal LLM based on intent, complexity, and cost

Strategy:
- Simple queries → Claude Haiku (fast + cheap)
- Medium complexity → Claude Sonnet (balanced)
- Complex reasoning → Claude Opus (powerful)
- Voice/Audio → GPT-4o Realtime or Gemini Live

Cost comparison (per 1M tokens):
- Flash:  $0.075 input / $0.30 output
- Pro:    $1.25 input / $5.00 output

Reference: https://ai.google.dev/pricing
"""

from typing import List
from enum import Enum
import logging


# Simple message type for routing
class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tiers by capability and cost (2026 Sovereign Mode)"""

    FAST = "claude-3-5-haiku-20241022"
    BALANCED = "claude-sonnet-4-5-20250901"
    POWERFUL = "claude-opus-4-5-20251101"
    # Legacy fallback
    GEMINI_FAST = "gemini-3-flash-preview"


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

    # CONSTITUTIONAL EXEMPTION (Padrão Pagani, Artigo II):
    # Reason: Quota checking requires user database integration
    # Root cause: User management and quota system not deployed
    # Alternative: Use default limits for all users
    # ETA: Phase 6 deployment with user management
    # Tracking: VERTICE-QUOTA-001
    # For now, skip quota checking and use intent-based routing

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
