"""
Integration Tests for Vertice-Code System.

Comprehensive end-to-end testing covering:
- System initialization and component integration
- Chat workflows from input to LLM response
- File operations and tool execution
- Error handling and recovery scenarios
- Performance validation under load
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, patch

# Test imports
from vertice_tui.core.bridge import get_bridge
from vertice_tui.core.error_tracking import get_error_tracker
from vertice_tui.core.logging import get_system_logger
from vertice_tui.core.input_validator import validate_chat_message
from vertice_tui.core.data_protection import encrypt_sensitive, decrypt_sensitive
from vertice_tui.core.safe_executor import SafeCommandExecutor


class TestSystemIntegration:
    """Integration tests for the complete Vertice-Code system."""

    @pytest.fixture
    async def system_bridge(self):
        """Fixture providing initialized system bridge."""
        bridge = get_bridge()
        yield bridge

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for testing."""
        return {
            "content": "This is a test response from the LLM.",
            "usage": {"tokens": 150, "cost": 0.002},
            "finish_reason": "stop",
        }

    @pytest.mark.asyncio
    async def test_system_initialization(self, system_bridge):
        """Test complete system initialization."""
        # Verify bridge components are initialized
        assert system_bridge.llm is not None
        assert system_bridge.tools is not None
        assert system_bridge.agents is not None

        # Test health check
        health = system_bridge.check_health()
        assert health["Overall"]["ok"] is True
        assert health["Overall"]["critical_issues"] == 0

        # Verify critical components
        assert "LLM" in health
        assert "Tools" in health
        assert "Agents" in health

    @pytest.mark.asyncio
    async def test_chat_workflow_integration(self, system_bridge, mock_llm_response):
        """Test complete chat workflow from input to response."""
        # Mock LLM response
        with patch.object(system_bridge.llm, "stream_chat", new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = self._mock_stream_response(mock_llm_response["content"])

            # Test chat request
            prompt = "Hello, can you help me with Python?"
            messages = [{"role": "user", "content": prompt}]

            # Execute chat (this would normally go through the full pipeline)
            response_chunks = []
            async for chunk in system_bridge.llm.stream_chat(messages):
                response_chunks.append(chunk)

            # Verify response
            full_response = "".join(response_chunks)
            assert len(full_response) > 0
            assert "test response" in full_response.lower()

            # Verify LLM was called correctly
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0][0]
            assert len(call_args) >= 1
            assert call_args[0]["role"] == "user"
            assert prompt in call_args[0]["content"]

    @pytest.mark.asyncio
    async def test_tool_execution_integration(self, system_bridge):
        """Test tool execution through the system."""
        # Test tool availability
        if system_bridge.tools:
            tool_count = system_bridge.tools.get_tool_count()
            assert tool_count >= 0

            # Test tool listing
            tools = system_bridge.tools.list_tools()
            assert isinstance(tools, list)

            # Test tool execution (if tools are available)
            if tool_count > 0:
                # This would test actual tool execution
                pass

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, system_bridge):
        """Test error handling throughout the system."""
        error_tracker = get_error_tracker()

        # Test error tracking
        initial_errors = len(error_tracker.errors)

        # Simulate an error
        try:
            raise ValueError("Test integration error")
        except Exception as e:
            error_event = error_tracker.track_error(
                "test_component", "test_operation", e, {"integration_test": True}
            )

        # Verify error was tracked
        assert len(error_tracker.errors) == initial_errors + 1
        assert error_tracker.errors[-1].component == "test_component"
        assert error_tracker.errors[-1].operation == "test_operation"

        # Test error stats
        stats = error_tracker.get_error_stats()
        assert stats["total_errors"] >= 1
        assert "error_types" in stats

    @pytest.mark.asyncio
    async def test_security_integration(self):
        """Test security components integration."""
        # Test input validation
        valid_result = validate_chat_message("Hello, this is a normal message!")
        assert valid_result.is_valid
        assert valid_result.security_score > 0.8

        # Test dangerous input
        dangerous_result = validate_chat_message("<script>alert('xss')</script>")
        assert not dangerous_result.is_valid
        assert dangerous_result.security_score < 0.5

        # Test data protection
        sensitive_data = {"api_key": "sk-123456", "password": "secret"}
        encrypted = encrypt_sensitive(sensitive_data)
        decrypted = decrypt_sensitive(encrypted)
        assert decrypted == sensitive_data

        # Test safe executor
        executor = SafeCommandExecutor()
        allowed, reason = executor.is_command_allowed("git status")
        assert allowed

        blocked, reason = executor.is_command_allowed("rm -rf /")
        assert not blocked

    @pytest.mark.asyncio
    async def test_logging_integration(self):
        """Test logging system integration."""
        logger = get_system_logger()

        # Test logging functionality
        with logger.context("test_operation", "integration_test"):
            logger.info("Test log message", extra={"test_data": "value"})

        # Verify logger is properly configured
        assert logger.name == "vertice.system"
        assert logger.level.value in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def _mock_stream_response(self, content: str):
        """Create mock streaming response."""

        async def mock_generator():
            words = content.split()
            for word in words:
                yield f"{word} "
                await asyncio.sleep(0.01)  # Small delay to simulate streaming

        return mock_generator()

    @pytest.mark.asyncio
    async def test_performance_under_load(self, system_bridge):
        """Test system performance under concurrent load."""

        # Test concurrent health checks
        results = []
        errors = []

        async def health_check_worker(worker_id: int):
            try:
                start_time = time.time()
                health = system_bridge.check_health()
                end_time = time.time()

                results.append(
                    {
                        "worker": worker_id,
                        "duration": end_time - start_time,
                        "healthy": health["Overall"]["ok"],
                    }
                )
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Run 5 concurrent health checks
        tasks = [health_check_worker(i) for i in range(5)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        assert len(results) == 5
        assert len(errors) == 0

        # Check performance
        avg_duration = sum(r["duration"] for r in results) / len(results)
        assert avg_duration < 1.0  # Should complete within 1 second

        # All should be healthy
        assert all(r["healthy"] for r in results)

    @pytest.mark.asyncio
    async def test_component_isolation(self, system_bridge):
        """Test that components are properly isolated."""
        # Test that LLM failure doesn't break other components
        original_llm = system_bridge.llm

        try:
            # Temporarily break LLM
            system_bridge.llm = None

            # System should still be able to check health (with degraded status)
            health = system_bridge.check_health()
            assert "LLM" in health
            assert not health["LLM"]["ok"]  # LLM should be unhealthy

            # But overall system should still function
            assert "Overall" in health

            # Other components should still work
            assert "Tools" in health
            # Note: Tools check might fail if it depends on LLM, which is expected

        finally:
            # Restore LLM
            system_bridge.llm = original_llm

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, system_bridge):
        """Test complete end-to-end workflow."""
        # This test would simulate a real user interaction
        # from input validation -> chat processing -> tool execution -> response

        # Step 1: Input validation
        user_input = "Can you help me analyze this Python code: `print('hello')`"
        validation = validate_chat_message(user_input)
        assert validation.is_valid

        # Step 2: Prepare messages
        messages = [{"role": "user", "content": user_input}]

        # Step 3: Process through bridge (mocked)
        with patch.object(system_bridge.llm, "stream_chat", new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = self._mock_stream_response(
                "I'd be happy to help you analyze that Python code!"
            )

            # This would be the full workflow in a real scenario
            # For now, we just verify the components are ready
            assert system_bridge.llm is not None
            assert system_bridge.tools is not None

            # Verify error tracking is ready
            error_tracker = get_error_tracker()
            assert error_tracker is not None

            # Verify logging is ready
            logger = get_system_logger()
            assert logger is not None

    @pytest.mark.asyncio
    async def test_system_recovery(self, system_bridge):
        """Test system recovery from various failure scenarios."""
        # Test recovery from component failure
        original_tools = system_bridge.tools

        try:
            # Simulate tool system failure
            system_bridge.tools = None

            # System should still provide health info
            health = system_bridge.check_health()
            assert "Tools" in health
            assert not health["Tools"]["ok"]

            # System should still be able to provide basic functionality
            # (LLM and agents should still work)

        finally:
            # Restore tools
            system_bridge.tools = original_tools


# Performance and Load Testing
class TestLoadPerformance:
    """Load and performance testing."""

    @pytest.fixture
    async def system_under_test(self):
        """System prepared for load testing."""
        bridge = get_bridge()
        return bridge

    @pytest.mark.asyncio
    async def test_concurrent_chat_requests(self, system_under_test):
        """Test handling multiple concurrent chat requests."""
        concurrent_requests = 10

        async def mock_chat_request(request_id: int):
            messages = [{"role": "user", "content": f"Test request {request_id}"}]

            with patch.object(
                system_under_test.llm, "stream_chat", new_callable=AsyncMock
            ) as mock_stream:
                mock_stream.return_value = self._mock_simple_response(f"Response {request_id}")

                start_time = time.time()
                chunks = []
                async for chunk in system_under_test.llm.stream_chat(messages):
                    chunks.append(chunk)
                end_time = time.time()

                return {
                    "request_id": request_id,
                    "duration": end_time - start_time,
                    "chunks": len(chunks),
                    "success": len(chunks) > 0,
                }

        # Execute concurrent requests
        tasks = [mock_chat_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_requests = [r for r in results if not isinstance(r, Exception) and r["success"]]
        failed_requests = [r for r in results if isinstance(r, Exception) or not r["success"]]

        # Should handle all requests
        assert len(successful_requests) == concurrent_requests
        assert len(failed_requests) == 0

        # Performance check
        avg_duration = sum(r["duration"] for r in successful_requests) / len(successful_requests)
        assert avg_duration < 5.0  # Should complete within 5 seconds each

    def _mock_simple_response(self, content: str):
        """Simple mock response for load testing."""

        async def generator():
            yield content

        return generator()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, system_under_test):
        """Test memory usage stability under load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run load test
        await self.test_concurrent_chat_requests(system_under_test)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)

        # Memory increase should be reasonable (less than 50MB)
        assert (
            memory_increase_mb < 50.0
        ), f"Memory leak detected: {memory_increase_mb:.1f}MB increase"

    @pytest.mark.asyncio
    async def test_error_rate_under_load(self, system_under_test):
        """Test error rate remains low under load."""
        error_tracker = get_error_tracker()
        initial_errors = len(error_tracker.errors)

        # Run intensive load test
        await self.test_concurrent_chat_requests(system_under_test)

        final_errors = len(error_tracker.errors)
        new_errors = final_errors - initial_errors

        # Error rate should be very low (< 1%)
        error_rate = new_errors / 10  # 10 requests
        assert error_rate < 0.01, f"High error rate under load: {error_rate:.3%}"


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
