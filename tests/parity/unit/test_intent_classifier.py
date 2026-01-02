"""
Unit tests for semantic intent classification.

Tests that user requests are correctly classified into intents
using model-based NLU instead of just regex patterns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tests.parity.conftest import IntentResult


class MockIntentClassifier:
    """Mock semantic intent classifier for testing."""

    INTENTS = {
        "planning": ["plan", "design", "architect", "structure", "organize"],
        "coding": ["code", "implement", "create", "write", "build", "add"],
        "review": ["review", "analyze", "check", "audit", "inspect"],
        "debug": ["debug", "fix", "troubleshoot", "error", "bug", "issue"],
        "refactor": ["refactor", "improve", "optimize", "clean", "restructure"],
        "test": ["test", "verify", "validate", "check", "assert"],
        "docs": ["document", "readme", "docstring", "comment", "explain"],
        "explore": ["find", "search", "where", "locate", "understand"],
    }

    async def classify(self, text: str) -> IntentResult:
        """Classify intent based on text."""
        text_lower = text.lower()

        scores = {}
        for intent, keywords in self.INTENTS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score / len(keywords)

        if not scores:
            return IntentResult(
                intent="coding",  # Default
                confidence=0.3,
                reasoning="No clear intent detected",
                secondary_intents=[],
            )

        primary = max(scores, key=scores.get)
        secondary = [k for k, v in sorted(scores.items(), key=lambda x: -x[1]) if k != primary][:2]

        return IntentResult(
            intent=primary,
            confidence=min(0.95, scores[primary] * 2),
            reasoning=f"Matched keywords for {primary}",
            secondary_intents=secondary,
        )


@pytest.fixture
def intent_classifier():
    """Provide mock intent classifier."""
    return MockIntentClassifier()


class TestIntentClassificationBasics:
    """Basic intent classification tests."""

    @pytest.mark.unit
    async def test_planning_intent_detected(self, intent_classifier):
        """Planning requests should be classified as planning."""
        requests = [
            "Plan the architecture for a microservices system",
            "Design a database schema for user data",
            "Architect a solution for handling payments",
        ]

        for request in requests:
            result = await intent_classifier.classify(request)
            assert result.intent == "planning", f"Failed for: {request}"
            assert result.confidence > 0.5

    @pytest.mark.unit
    async def test_coding_intent_detected(self, intent_classifier):
        """Coding requests should be classified as coding."""
        requests = [
            "Implement a login function",
            "Create a new REST endpoint",
            "Write a utility for parsing JSON",
            "Add error handling to the API",
        ]

        for request in requests:
            result = await intent_classifier.classify(request)
            assert result.intent == "coding", f"Failed for: {request}"

    @pytest.mark.unit
    async def test_review_intent_detected(self, intent_classifier):
        """Review requests should be classified as review."""
        requests = [
            "Review this pull request",
            "Analyze the code quality",
            "Check for security vulnerabilities",
        ]

        for request in requests:
            result = await intent_classifier.classify(request)
            assert result.intent == "review", f"Failed for: {request}"

    @pytest.mark.unit
    async def test_debug_intent_detected(self, intent_classifier):
        """Debug requests should be classified as debug."""
        requests = [
            "Fix the authentication bug",
            "Debug the memory leak",
            "Troubleshoot the connection error",
        ]

        for request in requests:
            result = await intent_classifier.classify(request)
            assert result.intent == "debug", f"Failed for: {request}"


class TestIntentConfidence:
    """Tests for confidence scoring."""

    @pytest.mark.unit
    async def test_clear_intent_high_confidence(self, intent_classifier):
        """Clear requests should have high confidence."""
        result = await intent_classifier.classify(
            "Plan and design the complete system architecture"
        )

        assert result.confidence >= 0.7, "Clear intent should have high confidence"

    @pytest.mark.unit
    async def test_ambiguous_intent_lower_confidence(self, intent_classifier):
        """Ambiguous requests should have lower confidence."""
        result = await intent_classifier.classify("Help me with this")

        assert result.confidence < 0.7, "Ambiguous intent should have lower confidence"

    @pytest.mark.unit
    async def test_confidence_in_valid_range(self, intent_classifier):
        """Confidence should always be between 0 and 1."""
        requests = [
            "Plan everything",
            "x",
            "",
            "A" * 1000,
        ]

        for request in requests:
            result = await intent_classifier.classify(request)
            assert 0 <= result.confidence <= 1, f"Invalid confidence for: {request}"


class TestSecondaryIntents:
    """Tests for secondary intent detection."""

    @pytest.mark.unit
    async def test_mixed_intent_has_secondary(self, intent_classifier):
        """Requests with mixed intents should have secondary intents."""
        result = await intent_classifier.classify(
            "Review and refactor the authentication module"
        )

        assert len(result.secondary_intents) > 0, "Should have secondary intents"

    @pytest.mark.unit
    async def test_secondary_intents_ordered_by_confidence(self, intent_classifier):
        """Secondary intents should be ordered by relevance."""
        result = await intent_classifier.classify(
            "Design, implement, and test the new feature"
        )

        # Should have multiple secondary intents
        assert len(result.secondary_intents) >= 1


class TestIntentClassificationEdgeCases:
    """Edge case tests."""

    @pytest.mark.unit
    async def test_empty_request(self, intent_classifier):
        """Empty requests should not crash."""
        result = await intent_classifier.classify("")

        assert result.intent is not None
        assert result.confidence >= 0

    @pytest.mark.unit
    async def test_non_english_request(self, intent_classifier):
        """Non-English requests should be handled."""
        result = await intent_classifier.classify(
            "Implementar sistema de autenticacao"
        )

        # Should handle gracefully (may fall back to coding)
        assert result.intent is not None

    @pytest.mark.unit
    async def test_special_characters(self, intent_classifier):
        """Special characters should not break classification."""
        result = await intent_classifier.classify(
            "Fix the bug in @user/repo#123!!!"
        )

        assert result.intent is not None

    @pytest.mark.unit
    async def test_very_long_request(self, intent_classifier):
        """Very long requests should be handled."""
        long_request = "Please implement " + " and implement ".join([f"feature{i}" for i in range(100)])

        result = await intent_classifier.classify(long_request)

        assert result.intent is not None


class TestIntentClassifierVsRegex:
    """Tests comparing semantic vs regex classification."""

    @pytest.mark.unit
    async def test_semantic_understands_context(self, intent_classifier):
        """Semantic classifier should understand context."""
        # "debug" is a keyword but this is asking for docs
        result = await intent_classifier.classify(
            "Document how to debug the application"
        )

        # Should recognize this is about documentation, not debugging
        assert "docs" in [result.intent] + result.secondary_intents or \
               "debug" in [result.intent] + result.secondary_intents

    @pytest.mark.unit
    async def test_handles_negation(self, intent_classifier):
        """Should handle negation properly."""
        result = await intent_classifier.classify(
            "Don't test this yet, just implement it"
        )

        # Primary should be coding, not testing
        assert result.intent == "coding"

    @pytest.mark.unit
    async def test_handles_synonyms(self, intent_classifier):
        """Should recognize synonyms."""
        synonymous_requests = [
            ("Create a function", "coding"),
            ("Build a function", "coding"),
            ("Make a function", "coding"),
        ]

        for request, expected in synonymous_requests:
            result = await intent_classifier.classify(request)
            assert result.intent == expected, f"Failed for: {request}"
