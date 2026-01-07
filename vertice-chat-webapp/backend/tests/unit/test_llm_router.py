"""
Unit tests for LLM Router
"""

import pytest
from app.llm.router import classify_intent, route_to_model, Message, IntentType, ModelTier


class TestLLMRouter:
    """Test suite for LLM Router."""

    def test_classify_intent_simple_query(self):
        """Test classification of simple queries."""
        messages = [Message(role="user", content="What is 2+2?")]

        intent = classify_intent(messages)
        assert intent == IntentType.SIMPLE_QUERY

    def test_classify_intent_code_generation(self):
        """Test classification of code generation requests."""
        messages = [Message(role="user", content="Write a function to calculate fibonacci")]

        intent = classify_intent(messages)
        assert intent == IntentType.CODE_GENERATION

    def test_classify_intent_long_context(self):
        """Test classification of long context queries."""
        long_content = "A" * 10000  # 10K characters
        messages = [Message(role="user", content=long_content)]

        intent = classify_intent(messages)
        assert intent == IntentType.LONG_CONTEXT

    def test_classify_intent_complex_reasoning(self):
        """Test classification of complex reasoning queries."""
        messages = [Message(role="user", content="Explain quantum computing in detail")]

        intent = classify_intent(messages)
        assert intent == IntentType.COMPLEX_REASONING

    def test_route_to_model_simple_query(self):
        """Test routing for simple queries."""
        messages = [Message(role="user", content="Hello?")]

        model = route_to_model(messages, "test-user")
        assert model == ModelTier.FAST.value

    def test_route_to_model_code_generation(self):
        """Test routing for code generation."""
        messages = [Message(role="user", content="Write a Python function")]

        model = route_to_model(messages, "test-user")
        assert model == ModelTier.BALANCED.value

    def test_route_to_model_complex_reasoning(self):
        """Test routing for complex reasoning."""
        messages = [Message(role="user", content="Analyze this complex problem")]

        model = route_to_model(messages, "test-user")
        assert model == ModelTier.POWERFUL.value
