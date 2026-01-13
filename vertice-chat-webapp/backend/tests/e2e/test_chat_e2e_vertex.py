"""
E2E Test for Chat Endpoint with REAL Vertex AI

This test makes actual API calls to Vertex AI to verify the complete
streaming flow works end-to-end.

Requirements:
- GOOGLE_CLOUD_PROJECT environment variable set
- Application Default Credentials configured (gcloud auth application-default login)

Run with:
    cd /media/juan/DATA/Vertice-Code/vertice-chat-webapp/backend
    python -m pytest tests/e2e/test_chat_e2e_vertex.py -v -s
"""

import pytest
import httpx
import asyncio
import os
import re

# Skip if no GCP credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_CLOUD_PROJECT"),
    reason="Requires GOOGLE_CLOUD_PROJECT environment variable"
)

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture
def dev_auth_headers():
    """Development authentication headers."""
    return {
        "Authorization": "Bearer dev-token",
        "Content-Type": "application/json"
    }


class TestChatE2EVertex:
    """End-to-end tests with real Vertex AI."""
    
    @pytest.mark.asyncio
    async def test_simple_hello_stream(self, dev_auth_headers):
        """Test basic streaming with a simple hello message."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Say 'Hello World' and nothing else."}],
                    "stream": True,
                    "model": "gemini-2.5-pro"
                }
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Verify content type
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type, f"Expected text/plain, got {content_type}"
            
            # Parse stream and verify format
            content = response.text
            lines = content.strip().split("\n")
            
            assert len(lines) >= 2, f"Expected at least 2 lines, got {len(lines)}: {content}"
            
            # Check for text chunks (0:"...")
            text_chunks = [line for line in lines if line.startswith('0:')]
            assert len(text_chunks) > 0, f"No text chunks found in: {content}"
            
            # Check for finish signal (d:{...})
            finish_lines = [line for line in lines if line.startswith('d:')]
            assert len(finish_lines) == 1, f"Expected 1 finish signal, got {len(finish_lines)}: {content}"
            
            # Verify finish reason
            assert '"finishReason"' in finish_lines[0], f"Missing finishReason in: {finish_lines[0]}"
            
            # Extract text and verify it contains something
            full_text = ""
            for chunk in text_chunks:
                # Parse 0:"text" format
                match = re.match(r'^0:"(.*)"$', chunk)
                if match:
                    full_text += match.group(1).replace("\\n", "\n")
            
            print(f"\n[E2E] Response text: {full_text}")
            assert len(full_text) > 0, "Response text is empty"
    
    @pytest.mark.asyncio
    async def test_stream_code_generation(self, dev_auth_headers):
        """Test streaming a code generation request."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{
                        "role": "user",
                        "content": "Write a Python function that calculates fibonacci(n). Just the code, no explanation."
                    }],
                    "stream": True
                }
            )
            
            assert response.status_code == 200
            
            content = response.text
            lines = content.strip().split("\n")
            
            # Should have text chunks
            text_chunks = [line for line in lines if line.startswith('0:')]
            assert len(text_chunks) > 5, "Code generation should produce multiple chunks"
            
            # Extract full text
            full_text = ""
            for chunk in text_chunks:
                match = re.match(r'^0:"(.*)"$', chunk)
                if match:
                    full_text += match.group(1).replace("\\n", "\n")
            
            print(f"\n[E2E] Generated code:\n{full_text}")
            
            # Verify it looks like Python code
            assert "def " in full_text or "fibonacci" in full_text.lower(), \
                f"Response doesn't look like code: {full_text[:200]}"
    
    @pytest.mark.asyncio
    async def test_conversation_history(self, dev_auth_headers):
        """Test that conversation history is properly handled."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [
                        {"role": "user", "content": "Remember: the secret word is 'BUTTERFLY'."},
                        {"role": "assistant", "content": "Got it! I'll remember that the secret word is BUTTERFLY."},
                        {"role": "user", "content": "What is the secret word? Reply with just the word."}
                    ],
                    "stream": True
                }
            )
            
            assert response.status_code == 200
            
            content = response.text
            text_chunks = [line for line in content.strip().split("\n") if line.startswith('0:')]
            
            full_text = ""
            for chunk in text_chunks:
                match = re.match(r'^0:"(.*)"$', chunk)
                if match:
                    full_text += match.group(1)
            
            print(f"\n[E2E] Secret word response: {full_text}")
            assert "BUTTERFLY" in full_text.upper(), f"Model should remember context: {full_text}"
    
    @pytest.mark.asyncio
    async def test_error_empty_messages(self, dev_auth_headers):
        """Test error handling for empty messages."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [],
                    "stream": True
                }
            )
            
            # Should get validation error
            assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_unauthenticated_rejected(self):
        """Test that requests without auth are rejected."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers={"Content-Type": "application/json"},
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": True
                }
            )
            
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestStreamProtocolFormat:
    """Verify the exact stream protocol format."""
    
    @pytest.mark.asyncio
    async def test_protocol_format_compliance(self, dev_auth_headers):
        """Verify output matches Vercel AI SDK Data Stream Protocol."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                headers=dev_auth_headers,
                json={
                    "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                    "stream": True
                }
            )
            
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split("\n")
            
            # Verify each line format
            for line in lines:
                if not line.strip():
                    continue
                
                # Text chunk: 0:"..."
                # Data: 2:[...]
                # Finish: d:{...}
                # Error: 3:"..."
                valid_prefixes = ['0:', '2:', '3:', '8:', '9:', 'a:', 'd:']
                has_valid_prefix = any(line.startswith(p) for p in valid_prefixes)
                
                assert has_valid_prefix, f"Invalid line format: {line}"
            
            print(f"\n[E2E] All {len(lines)} lines comply with Data Stream Protocol")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
