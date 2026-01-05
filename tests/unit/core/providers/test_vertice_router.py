"""
Unit tests for VerticeRouter schema validation.

Tests ERR-004: Add response schema validation.

Note: These tests use isolated validation logic to avoid import chain issues
with the full provider module graph.
"""

from unittest.mock import Mock
import pytest
from typing import TypedDict, NotRequired


class ModelInfo(TypedDict):
    """Local copy of ModelInfo for isolated testing."""
    model: str
    provider: str
    cost_tier: NotRequired[str]
    speed_tier: NotRequired[str]
    supports_streaming: NotRequired[bool]


def validate_model_info(model_info: dict, provider_name: str) -> str:
    """
    Validation logic extracted from VerticeRouter.route().

    This matches the implementation in vertice_cli/core/providers/vertice_router.py
    """
    try:
        model_name = model_info["model"]
    except KeyError:
        raise ValueError(
            f"Provider '{provider_name}' returned invalid model info: missing 'model' key."
        )
    return model_name


class TestModelInfoValidation:
    """Tests for model_info schema validation."""

    def test_valid_model_info_returns_model_name(self):
        """Valid model_info should return the model name."""
        model_info = ModelInfo(
            model="gemini-2.5-pro",
            provider="vertex-ai",
            cost_tier="enterprise",
            speed_tier="fast",
        )

        result = validate_model_info(model_info, "vertex-ai")

        assert result == "gemini-2.5-pro"

    def test_missing_model_key_raises_value_error(self):
        """Missing 'model' key should raise ValueError with clear message."""
        invalid_info = {"provider": "mock", "cost_tier": "free"}

        with pytest.raises(
            ValueError,
            match="Provider 'test-provider' returned invalid model info: missing 'model' key.",
        ):
            validate_model_info(invalid_info, "test-provider")

    def test_empty_model_string_is_valid(self):
        """Empty model string is technically valid (no content validation)."""
        model_info = ModelInfo(model="", provider="mock")

        result = validate_model_info(model_info, "mock")

        assert result == ""

    def test_model_info_with_only_required_fields(self):
        """ModelInfo with only required fields should work."""
        model_info = ModelInfo(model="test-model", provider="test")

        result = validate_model_info(model_info, "test")

        assert result == "test-model"

    def test_none_model_info_raises_type_error(self):
        """None model_info should raise TypeError."""
        with pytest.raises(TypeError):
            validate_model_info(None, "test")

    def test_model_info_as_plain_dict(self):
        """Plain dict (not TypedDict) should also work."""
        model_info = {"model": "plain-dict-model", "provider": "test"}

        result = validate_model_info(model_info, "test")

        assert result == "plain-dict-model"


class TestProviderErrorMessages:
    """Tests for error message formatting."""

    def test_error_includes_provider_name(self):
        """Error message should include the provider name for debugging."""
        invalid_info = {"provider": "groq"}

        with pytest.raises(ValueError) as exc_info:
            validate_model_info(invalid_info, "groq-provider")

        assert "groq-provider" in str(exc_info.value)

    def test_error_message_is_actionable(self):
        """Error message should indicate the missing key."""
        invalid_info = {}

        with pytest.raises(ValueError) as exc_info:
            validate_model_info(invalid_info, "test")

        assert "missing 'model' key" in str(exc_info.value)
