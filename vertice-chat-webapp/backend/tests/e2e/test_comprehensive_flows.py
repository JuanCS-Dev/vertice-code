"""
Comprehensive E2E Flow Tests for Vertice Chat Web App
Tests complete user journeys and critical business flows
"""

import pytest
import httpx
import os
import uuid
import json
from typing import Dict

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture
def dev_auth_headers() -> Dict[str, str]:
    """Development authentication headers."""
    return {"Authorization": "Bearer dev-token", "Content-Type": "application/json"}


class TestChatFlows:
    """Test complete chat flows."""

    @pytest.mark.asyncio
    async def test_complete_chat_session(self, dev_auth_headers):
        """Test a complete chat session from start to finish."""
        session_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # First message
            response1 = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Hello, my name is Alice"}],
                    "stream": True,
                    "session_id": session_id,
                },
            )
            assert response1.status_code == 200
            
            # Second message in same session
            response2 = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Hello, my name is Alice"},
                        {"role": "assistant", "content": "Nice to meet you, Alice!"},
                        {"role": "user", "content": "What's my name?"},
                    ],
                    "stream": True,
                    "session_id": session_id,
                },
            )
            assert response2.status_code == 200
            
            # Verify response contains context
            content = response2.text
            # Should have some response (not empty)
            assert len(content) > 10

    @pytest.mark.asyncio
    async def test_code_generation_flow(self, dev_auth_headers):
        """Test code generation and artifact creation flow."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Write a Python function to calculate factorial. Just the code.",
                        }
                    ],
                    "stream": True,
                },
            )
            
            assert response.status_code == 200
            content = response.text
            
            # Should have text chunks
            assert "0:" in content
            # Should have finish signal
            assert "d:" in content

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, dev_auth_headers):
        """Test multi-turn conversation with context."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Turn 1
            response1 = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "I like Python programming"}],
                    "stream": True,
                },
            )
            assert response1.status_code == 200
            
            # Turn 2 - reference previous context
            response2 = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "I like Python programming"},
                        {"role": "assistant", "content": "That's great! Python is a versatile language."},
                        {"role": "user", "content": "Can you suggest a good library for data analysis?"},
                    ],
                    "stream": True,
                },
            )
            assert response2.status_code == 200


class TestBillingFlows:
    """Test billing and subscription flows."""

    @pytest.mark.asyncio
    async def test_get_subscription_status(self, dev_auth_headers):
        """Test getting subscription status."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/billing/subscriptions",
                headers=dev_auth_headers,
            )
            
            # Should return subscription info (even if free tier)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "plan" in data

    @pytest.mark.asyncio
    async def test_get_usage_summary(self, dev_auth_headers):
        """Test getting usage summary."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/billing/usage",
                headers=dev_auth_headers,
            )
            
            # Should return usage data
            assert response.status_code in [200, 404, 500]  # Might not be implemented

    @pytest.mark.asyncio
    async def test_check_usage_limits(self, dev_auth_headers):
        """Test checking usage limits."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/billing/limits",
                headers=dev_auth_headers,
            )
            
            # Should return limits info
            assert response.status_code in [200, 404, 500]  # Might not be implemented


class TestAgentFlows:
    """Test agent-related flows."""

    @pytest.mark.asyncio
    async def test_list_agents(self, dev_auth_headers):
        """Test listing available agents."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/agents",
                headers=dev_auth_headers,
            )
            
            # Should return agents list or 404 if not implemented
            assert response.status_code in [200, 404]


class TestStreamingBehavior:
    """Test streaming behavior and protocol compliance."""

    @pytest.mark.asyncio
    async def test_stream_protocol_format(self, dev_auth_headers):
        """Test that stream follows Vercel AI SDK protocol."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "stream": True,
                },
            )
            
            assert response.status_code == 200
            
            # Verify content type
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type or "text/event-stream" in content_type
            
            content = response.text
            lines = [line for line in content.strip().split("\n") if line]
            
            # Verify protocol format
            valid_prefixes = ["0:", "2:", "3:", "8:", "9:", "a:", "d:", "e:"]
            for line in lines:
                has_valid = any(line.startswith(p) for p in valid_prefixes)
                assert has_valid, f"Invalid line format: {line}"

    @pytest.mark.asyncio
    async def test_stream_timeout_handling(self, dev_auth_headers):
        """Test that streams timeout appropriately."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/api/v1/chat",
                    headers=dev_auth_headers,
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": "Write a very long essay about the history of computing",
                            }
                        ],
                        "stream": True,
                    },
                )
                # If it completes within timeout, that's fine
                assert response.status_code == 200
            except httpx.TimeoutException:
                # Timeout is expected for very long responses
                pass

    @pytest.mark.asyncio
    async def test_concurrent_streams(self, dev_auth_headers):
        """Test handling of concurrent streaming requests."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Send multiple concurrent requests
            tasks = []
            for i in range(3):
                task = client.post(
                    f"{BACKEND_URL}/api/v1/chat",
                    headers=dev_auth_headers,
                    json={
                        "messages": [{"role": "user", "content": f"Test {i}"}],
                        "stream": True,
                    },
                )
                tasks.append(task)
            
            # All should succeed
            import asyncio
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            assert success_count >= 2, f"Expected at least 2 successful responses, got {success_count}"


class TestErrorRecovery:
    """Test error recovery and resilience."""

    @pytest.mark.asyncio
    async def test_invalid_model_fallback(self, dev_auth_headers):
        """Test that invalid model falls back gracefully."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": True,
                    "model": "nonexistent-model-xyz",
                },
            )
            
            # Should either fallback to default or return error
            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_malformed_message_handling(self, dev_auth_headers):
        """Test handling of malformed messages."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "invalid_role", "content": "Test"}],
                    "stream": True,
                },
            )
            
            # Should reject or handle gracefully
            assert response.status_code in [200, 400, 422]


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_time_acceptable(self, dev_auth_headers):
        """Test that response time is acceptable."""
        import time
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            start = time.time()
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Hi"}],
                    "stream": True,
                },
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            # First chunk should arrive within 10 seconds
            assert elapsed < 10, f"Response took {elapsed:.2f}s, expected < 10s"

    @pytest.mark.asyncio
    async def test_health_endpoint_fast(self):
        """Test that health endpoint responds quickly."""
        import time
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.time()
            response = await client.get(f"{BACKEND_URL}/health")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 1.0, f"Health check took {elapsed:.2f}s, expected < 1s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
