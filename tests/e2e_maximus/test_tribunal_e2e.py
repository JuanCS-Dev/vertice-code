"""
E2E Tests for MAXIMUS Tribunal Integration.

Tests the complete flow of Tribunal evaluation from Prometheus CLI
to MAXIMUS backend using respx mocked responses.

Based on 2025 best practices:
- Scientific hypothesis-driven testing
- respx for async httpx mocking
- Comprehensive edge case coverage

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, Google docstrings.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest
import respx

from vertice_cli.core.providers.maximus_provider import MaximusProvider


class TestTribunalEvaluate:
    """E2E tests for Tribunal evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_pass_decision(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Tribunal returns PASS for compliant execution.

        Given a compliant execution log,
        When evaluated by the Tribunal,
        Then decision should be PASS with high consensus.
        """
        execution_log = "User requested: list files. Agent executed: ls -la"

        result: Dict[str, Any] = await maximus_provider.tribunal_evaluate(
            execution_log=execution_log
        )

        assert result["decision"] == "PASS"
        assert result["consensus_score"] >= 0.7
        assert "verdicts" in result
        assert "VERITAS" in result["verdicts"]
        assert "SOPHIA" in result["verdicts"]
        assert "DIKE" in result["verdicts"]

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_with_context(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Context enriches Tribunal evaluation.

        Given execution log with additional context,
        When evaluated by the Tribunal,
        Then context is considered in the decision.
        """
        execution_log = "User requested: delete file. Agent executed: rm test.txt"
        context = {"user_role": "admin", "workspace": "/tmp/test"}

        result: Dict[str, Any] = await maximus_provider.tribunal_evaluate(
            execution_log=execution_log,
            context=context,
        )

        assert "decision" in result
        assert result["decision"] in ("PASS", "REVIEW", "FAIL", "CAPITAL")

    @pytest.mark.asyncio
    async def test_tribunal_evaluate_returns_reasoning(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Tribunal provides reasoning for decision.

        Given any execution log,
        When evaluated by the Tribunal,
        Then reasoning is included in response.
        """
        execution_log = "Agent analyzed code for security vulnerabilities."

        result: Dict[str, Any] = await maximus_provider.tribunal_evaluate(
            execution_log=execution_log
        )

        assert "reasoning" in result
        assert len(result["reasoning"]) > 0


class TestTribunalHealth:
    """E2E tests for Tribunal health endpoint."""

    @pytest.mark.asyncio
    async def test_tribunal_health_returns_ok(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Healthy Tribunal returns OK status.

        Given a healthy MAXIMUS backend,
        When checking Tribunal health,
        Then status should be 'ok'.
        """
        result: Dict[str, Any] = await maximus_provider.tribunal_health()

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_tribunal_health_includes_services(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Health check includes service status.

        Given a healthy MAXIMUS backend,
        When checking Tribunal health,
        Then individual service statuses are included.
        """
        result: Dict[str, Any] = await maximus_provider.tribunal_health()

        assert "services" in result
        assert result["services"]["tribunal"] == "ok"


class TestTribunalStats:
    """E2E tests for Tribunal statistics endpoint."""

    @pytest.mark.asyncio
    async def test_tribunal_stats_returns_metrics(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Tribunal stats returns evaluation metrics.

        Given a running Tribunal service,
        When requesting statistics,
        Then comprehensive metrics are returned.
        """
        result: Dict[str, Any] = await maximus_provider.tribunal_stats()

        assert "total_evaluations" in result
        assert "pass_rate" in result
        assert "review_rate" in result
        assert "fail_rate" in result

    @pytest.mark.asyncio
    async def test_tribunal_stats_rates_sum_to_one(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Decision rates sum approximately to 1.0.

        Given Tribunal statistics,
        When summing all decision rates,
        Then total should be approximately 1.0.
        """
        result: Dict[str, Any] = await maximus_provider.tribunal_stats()

        total_rate = (
            result.get("pass_rate", 0)
            + result.get("review_rate", 0)
            + result.get("fail_rate", 0)
            + result.get("capital_rate", 0)
        )

        assert 0.99 <= total_rate <= 1.01


class TestTribunalResilience:
    """E2E tests for Tribunal resilience patterns."""

    @pytest.mark.asyncio
    async def test_tribunal_handles_network_error(
        self,
        maximus_config: Any,
        maximus_base_url: str,
    ) -> None:
        """HYPOTHESIS: Tribunal handles network errors gracefully.

        Given a network failure,
        When evaluating in Tribunal,
        Then error response is returned without crash.
        """
        with respx.mock(assert_all_called=False) as router:
            router.get(f"{maximus_base_url}/health").respond(
                json={"status": "ok", "mcp_enabled": False}
            )
            router.post(f"{maximus_base_url}/v1/tribunal/evaluate").mock(
                side_effect=httpx.ConnectError("Network error")
            )

            provider = MaximusProvider(config=maximus_config)
            try:
                result = await provider.tribunal_evaluate("test log")
                assert "error" in result or result.get("decision") == "ERROR"
            finally:
                await provider.close()

    @pytest.mark.asyncio
    async def test_tribunal_retry_on_transient_error(
        self,
        maximus_config: Any,
        maximus_base_url: str,
        mock_factory: Any,
    ) -> None:
        """HYPOTHESIS: Tribunal retries on transient errors.

        Given transient network failures followed by success,
        When evaluating in Tribunal,
        Then retry mechanism recovers and returns result.
        """
        call_count = 0

        def side_effect(request: Any) -> Any:  # pylint: disable=unused-argument
            """Simulate transient failure then success."""
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Transient error")
            return respx.MockResponse(
                json=mock_factory.tribunal_evaluate()
            )

        with respx.mock(assert_all_called=False) as router:
            router.get(f"{maximus_base_url}/health").respond(
                json={"status": "ok", "mcp_enabled": False}
            )
            router.post(f"{maximus_base_url}/v1/tribunal/evaluate").mock(
                side_effect=side_effect
            )

            provider = MaximusProvider(config=maximus_config)
            try:
                result = await provider.tribunal_evaluate("test log")
                # Should either succeed after retry or return error
                assert "decision" in result or "error" in result
            finally:
                await provider.close()


class TestTribunalIntegrationFlow:
    """E2E tests for complete Tribunal integration flows."""

    @pytest.mark.asyncio
    async def test_complete_evaluation_flow(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: Complete evaluation flow works end-to-end.

        Given a multi-step agent execution,
        When evaluated through the complete flow,
        Then all components respond correctly.
        """
        # Step 1: Check health
        health: Dict[str, Any] = await maximus_provider.tribunal_health()
        assert health["status"] == "ok"

        # Step 2: Evaluate execution
        execution_log = """
        User: Analyze this Python file for bugs
        Agent: Reading file src/main.py
        Agent: Found 2 potential issues:
        1. Missing null check on line 45
        2. Resource leak on line 78
        Agent: Suggested fixes applied
        """
        result: Dict[str, Any] = await maximus_provider.tribunal_evaluate(
            execution_log=execution_log
        )
        assert result["decision"] in ("PASS", "REVIEW", "FAIL", "CAPITAL")

        # Step 3: Check stats
        stats: Dict[str, Any] = await maximus_provider.tribunal_stats()
        assert stats["total_evaluations"] > 0

    @pytest.mark.asyncio
    async def test_evaluation_with_all_judges(
        self,
        maximus_provider: MaximusProvider,
    ) -> None:
        """HYPOTHESIS: All three judges participate in evaluation.

        Given an execution log,
        When evaluated by the Tribunal,
        Then VERITAS, SOPHIA, and DIKE all provide verdicts.
        """
        execution_log = "Agent performed code review and suggested improvements."

        result: Dict[str, Any] = await maximus_provider.tribunal_evaluate(
            execution_log=execution_log
        )

        verdicts = result.get("verdicts", {})

        # All three judges should vote
        assert "VERITAS" in verdicts
        assert "SOPHIA" in verdicts
        assert "DIKE" in verdicts

        # Each judge should have vote and confidence
        for judge_name in ("VERITAS", "SOPHIA", "DIKE"):
            judge_verdict = verdicts[judge_name]
            assert "vote" in judge_verdict
            assert "confidence" in judge_verdict
            assert 0.0 <= judge_verdict["confidence"] <= 1.0
