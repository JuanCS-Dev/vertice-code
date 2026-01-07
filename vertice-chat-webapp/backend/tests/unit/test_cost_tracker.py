"""
Unit tests for Cost Tracker
"""

import pytest
from decimal import Decimal
from app.llm.cost_tracker import calculate_cost


class TestCostTracker:
    """Test suite for Cost Tracker."""

    @pytest.mark.asyncio
    async def test_calculate_cost_base_only(self):
        """Test cost calculation with only base costs."""
        result = await calculate_cost(
            model="claude-sonnet-4-5-20250901",
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

        # Sonnet: $3/1M input, $15/1M output
        expected_input = Decimal("0.003")  # 1000 * 3 / 1M
        expected_output = Decimal("0.0075")  # 500 * 15 / 1M
        expected_total = expected_input + expected_output

        assert result["base_input_cost"] == expected_input
        assert result["base_output_cost"] == expected_output
        assert result["total_cost"] == expected_total
        assert result["savings"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_calculate_cost_with_caching(self):
        """Test cost calculation with prompt caching."""
        result = await calculate_cost(
            model="claude-sonnet-4-5-20250901",
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=2000,
            cache_write_tokens=1000,
        )

        # Cache write: 1.25x base price
        # Cache read: 0.10x base price
        # Savings: 0.90x base price
        expected_cache_write = Decimal("0.00375")  # 1000 * 3 * 1.25 / 1M
        expected_cache_read = Decimal("0.0006")  # 2000 * 3 * 0.10 / 1M
        expected_savings = Decimal("0.0054")  # 2000 * 3 * 0.90 / 1M

        assert result["cache_write_cost"] == expected_cache_write
        assert result["cache_read_cost"] == expected_cache_read
        assert result["savings"] == expected_savings

    @pytest.mark.asyncio
    async def test_calculate_cost_unknown_model(self):
        """Test cost calculation with unknown model falls back to Sonnet."""
        result = await calculate_cost(
            model="unknown-model",
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

        # Should use Sonnet pricing as fallback
        expected_input = Decimal("0.0003")  # 100 * 3 / 1M
        expected_output = Decimal("0.00075")  # 50 * 15 / 1M

        assert result["base_input_cost"] == expected_input
        assert result["base_output_cost"] == expected_output

    @pytest.mark.asyncio
    async def test_calculate_cost_haiku_model(self):
        """Test cost calculation with Haiku model."""
        result = await calculate_cost(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

        # Haiku: $0.25/1M input, $1.25/1M output
        expected_input = Decimal("0.00025")  # 1000 * 0.25 / 1M
        expected_output = Decimal("0.000625")  # 500 * 1.25 / 1M

        assert result["base_input_cost"] == expected_input
        assert result["base_output_cost"] == expected_output
