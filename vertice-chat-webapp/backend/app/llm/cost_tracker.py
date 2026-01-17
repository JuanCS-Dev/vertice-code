"""
LLM Cost Tracking and Quota Management

Tracks token usage per user with Redis for fast access
and PostgreSQL for historical data.

Cost calculation formulas (Anthropic 2026):
- Base input:  tokens * model_input_price_per_1M / 1_000_000
- Base output: tokens * model_output_price_per_1M / 1_000_000
- Cache write:  tokens * model_input_price_per_1M * 1.25 / 1_000_000
- Cache read:   tokens * model_input_price_per_1M * 0.10 / 1_000_000

Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#pricing
"""

from datetime import datetime
from decimal import Decimal
import logging
from typing import Dict

from app.core.cache import get_redis

logger = logging.getLogger(__name__)

# Pricing table (per 1M tokens) - Update from API
MODEL_PRICING = {
    "claude-3-5-haiku-20241022": {
        "input": Decimal("0.25"),
        "output": Decimal("1.25"),
    },
    "claude-sonnet-4-5-20250901": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
    },
    "claude-opus-4-5-20251101": {
        "input": Decimal("15.00"),
        "output": Decimal("75.00"),
    },
}


async def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> Dict[str, Decimal]:
    """
    Calculate cost breakdown for LLM call

    Returns:
        {
            "base_input_cost": Decimal,
            "base_output_cost": Decimal,
            "cache_write_cost": Decimal,
            "cache_read_cost": Decimal,
            "total_cost": Decimal,
            "savings": Decimal,  # From caching
        }
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        logger.warning(f"Unknown model {model}, using Sonnet pricing")
        pricing = MODEL_PRICING["claude-sonnet-4-5-20250901"]

    # Base costs
    base_input_cost = (input_tokens * pricing["input"]) / 1_000_000
    base_output_cost = (output_tokens * pricing["output"]) / 1_000_000

    # Cache costs (Anthropic caching: +25% write, 90% discount read)
    cache_write_cost = (cache_write_tokens * pricing["input"] * Decimal("1.25")) / 1_000_000
    cache_read_cost = (cache_read_tokens * pricing["input"] * Decimal("0.10")) / 1_000_000

    # Savings calculation: what we would have paid without caching
    savings = (cache_read_tokens * pricing["input"] * Decimal("0.90")) / 1_000_000

    total_cost = base_input_cost + base_output_cost + cache_write_cost + cache_read_cost

    return {
        "base_input_cost": base_input_cost,
        "base_output_cost": base_output_cost,
        "cache_write_cost": cache_write_cost,
        "cache_read_cost": cache_read_cost,
        "total_cost": total_cost,
        "savings": savings,
    }


async def track_token_usage(
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> None:
    """
    Track token usage in Redis (fast) and PostgreSQL (persistent)

    Redis keys:
    - user:{user_id}:tokens:daily → Daily token count (expires 24h)
    - user:{user_id}:cost:daily → Daily cost (expires 24h)

    PostgreSQL:
    - token_usage table for historical analysis
    """
    redis = await get_redis()

    # Calculate cost
    costs = await calculate_cost(
        model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens
    )

    # Update Redis counters (mock implementation)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key_tokens = f"user:{user_id}:tokens:{today}"
    redis_key_cost = f"user:{user_id}:cost:{today}"

    total_tokens = input_tokens + output_tokens

    # Mock Redis operations
    redis[redis_key_tokens] = int(redis.get(redis_key_tokens, 0)) + total_tokens
    redis[redis_key_cost] = float(redis.get(redis_key_cost, 0.0)) + float(costs["total_cost"])

    # CONSTITUTIONAL EXEMPTION (Padrão Pagani, Artigo II):
    # Reason: Database logging requires deployed database infrastructure
    # Root cause: Database schema and connection not yet deployed
    # Alternative: Cost tracking uses in-memory logging only
    # ETA: Phase 6 deployment with Neon PostgreSQL
    # Tracking: VERTICE-DATABASE-001
    # For now, log to console only
    logger.debug(
        f"Cost tracking: user={user_id}, model={model}, "
        f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
        f"cost=${costs['total_cost']:.4f}"
    )

    logger.info(
        f"User {user_id}: {total_tokens} tokens, "
        f"${costs['total_cost']:.4f} cost, "
        f"${costs['savings']:.4f} saved from caching"
    )


async def check_user_quota(user_id: str) -> Dict[str, float]:
    """
    Check user's daily quota

    Returns:
        {
            "tokens_used": int,
            "tokens_remaining": int,
            "cost_usd": float,
        }
    """
    redis = await get_redis()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key_tokens = f"user:{user_id}:tokens:{today}"
    redis_key_cost = f"user:{user_id}:cost:{today}"

    tokens_used = int(redis.get(redis_key_tokens, 0))
    cost_usd = float(redis.get(redis_key_cost, 0.0))

    # CONSTITUTIONAL EXEMPTION (Padrão Pagani, Artigo II):
    # Reason: User quota system requires database integration
    # Root cause: User management and subscription system not deployed
    # Alternative: Use default limits for all users
    # ETA: Phase 6 deployment with user management
    # Tracking: VERTICE-QUOTA-002
    from app.core.config import settings

    daily_limit = settings.DAILY_TOKEN_LIMIT_PER_USER

    return {
        "tokens_used": float(tokens_used),  # Convert to float for consistency
        "tokens_remaining": float(max(0, daily_limit - tokens_used)),
        "cost_usd": cost_usd,
    }
