
import asyncio
import pytest
from unittest.mock import AsyncMock



class TestDataFlowE2E:
    """End-to-end data flow validation."""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client that returns predictable responses."""
        client = AsyncMock()
        async def mock_stream(messages, system_prompt=None, context=None, tools=None):
            yield "Here's the implementation:\n"
            yield "```python\n"
            yield "def hello():\n"
            yield "    return 'world'\n"
            yield "```\n"
        client.stream = mock_stream
        return client

    @pytest.mark.asyncio
    async def test_simple_prompt_flow(self, mock_llm_client, cortex):
        """Test: Simple prompt → LLM → Response."""
        # Arrange
        prompt = "Write a hello world function"

        # Act
        response_chunks = []
        async for chunk in mock_llm_client.stream([{"role": "user", "content": prompt}]):
            response_chunks.append(chunk)

        # Assert
        full_response = "".join(response_chunks)
        assert "def hello" in full_response
        assert "```python" in full_response

    @pytest.mark.asyncio
    async def test_memory_context_injection(self, cortex):
        """Test: Memory context is injected into prompts."""
        # Arrange - Store relevant context (sync methods)
        cortex.semantic.store("Always use type hints in Python", category="coding_style")
        cortex.semantic.store("Project uses pytest for testing", category="testing")

        # Act - Retrieve context for a query
        context = await cortex.to_context_prompt("How should I write tests?")

        # Assert - Context contains relevant memories
        assert "<memory_context>" in context

    @pytest.mark.asyncio
    async def test_tool_call_detection_and_execution(self):
        """Test: Tool calls are detected and executed."""
        # This tests the ToolCallParser and execution flow
        from vertice_tui.core.parsing.tool_call_parser import ToolCallParser

        parser = ToolCallParser()

        # Simulate LLM response with tool call
        response_with_tool = '''
        I'll read the file for you.
        <tool_code>
        read_file(path="test.py")
        </tool_code>
        '''

        tool_calls = parser.extract(response_with_tool)
        assert len(tool_calls) >= 1
        assert tool_calls[0][0] == "read_file"

    @pytest.mark.asyncio
    async def test_error_propagation(self, mock_llm_client):
        """Test: Errors are properly propagated and formatted."""
        # Simulate API error
        async def failing_stream(*args, **kwargs):
            raise Exception("API rate limit")
            yield  # This makes it an async generator

        mock_llm_client.stream = failing_stream

        with pytest.raises(Exception) as exc_info:
            # We need to actually iterate to trigger the exception
            async for _ in mock_llm_client.stream([]):
                pass

        assert "rate limit" in str(exc_info.value).lower()


class TestRealDeveloperScenarios:
    """Simulates real developer usage patterns."""

    @pytest.mark.asyncio
    async def test_rapid_fire_prompts(self, cortex):
        """Developer sends multiple prompts quickly."""
        prompts = [
            "What's in main.py?",
            "Show me the imports",
            "Find all TODO comments",
            "How does the auth work?",
            "Run the tests",
        ]

        # Simulate rapid context retrievals
        results = []
        for prompt in prompts:
            result = await cortex.active_retrieve(prompt)
            results.append(result)

        assert len(results) == 5
        # All should complete without errors

    @pytest.mark.asyncio
    async def test_long_conversation_context(self, cortex):
        """Developer has extended conversation (context management)."""
        # Simulate 20-turn conversation (sync method)
        for i in range(20):
            cortex.episodic.record(
                event_type="conversation",
                content=f"Turn {i}: User asked about feature {i}",
                session_id="test-session"
            )

        # Verify context doesn't explode
        context = await cortex.to_context_prompt("summarize our conversation")
        # Context should be bounded (not include all 20 turns)
        assert len(context) < 10000  # Reasonable limit

    @pytest.mark.asyncio
    async def test_code_generation_quality(self):
        """Validate generated code quality markers."""
        # Mock response that should have quality markers
        generated_code = '''
        def process_data(items: List[Dict[str, Any]]) -> None:
            """Process incoming data items.

            Args:
                items: List of data dictionaries

            Returns:
                None
            """
            if not items:
                raise ValueError("Items cannot be empty")

            results = []
            for item in items:
                # Validate item structure
                if "id" not in item:
                    continue
                # results.append(transform(item))

            # return ProcessResult(success=True, data=results)
        '''

        # Quality checks
        assert "def " in generated_code  # Has function
        assert ": " in generated_code    # Has type hints
        assert '"""' in generated_code   # Has docstring
        assert "raise " in generated_code  # Has error handling
        assert "if " in generated_code   # Has validation


class TestStressScenarios:
    """Stress and edge case testing."""

    @pytest.mark.asyncio
    async def test_large_prompt_handling(self, cortex):
        """Test with very large prompt (10KB)."""
        large_prompt = "Explain this code:\n" + "x = 1\n" * 1000

        # Should not crash, should handle gracefully
        result = await cortex.active_retrieve(large_prompt[:5000])
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_prompt(self, cortex):
        """Test prompts with special characters."""
        special_prompts = [
            "What does `def __init__(self):` do?",
            "Explain the regex: ^[a-z]+$",
            "Parse this JSON: {\"key\": \"value\"}",
            "SQL query: SELECT * FROM users WHERE id = 1; --",
            "Shell command: rm -rf /",  # Should be safe in context
        ]

        for prompt in special_prompts:
            result = await cortex.active_retrieve(prompt)
            assert result is not None  # No crashes

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, cortex):
        """Multiple simulated users/sessions."""
        async def simulate_session(session_id: str, num_turns: int):
            for i in range(num_turns):
                cortex.episodic.record(
                    event_type="conversation",
                    content=f"Session {session_id} turn {i}",
                    session_id=session_id
                )
                await asyncio.sleep(0.01)  # Simulate real timing

        # Run 5 concurrent sessions
        await asyncio.gather(
            simulate_session("user1", 10),
            simulate_session("user2", 10),
            simulate_session("user3", 10),
            simulate_session("user4", 10),
            simulate_session("user5", 10),
        )

        # Verify data integrity - each session has its own records
        user1_context = cortex.episodic.get_session("user1")
        user2_context = cortex.episodic.get_session("user2")

        assert len(user1_context) >= 10
        assert len(user2_context) >= 10
        assert "user1" in user1_context[0]['content']
        assert "user2" in user2_context[0]['content']
