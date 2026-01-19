import pytest
from unittest.mock import Mock
from prometheus.tools.tool_factory import ToolFactory, ToolSpec


def test_get_tool_blocks_dangerous_code():
    """Tests that get_tool() blocks dangerous code execution."""
    # 1. Setup
    mock_llm_client = Mock()
    mock_sandbox_executor = Mock()
    factory = ToolFactory(llm_client=mock_llm_client, sandbox_executor=mock_sandbox_executor)

    # 2. Create malicious tool spec
    malicious_code = "import os\nos.system('echo malicious')"
    spec = ToolSpec(
        name="malicious_tool",
        description="A tool that tries to execute a dangerous command.",
        parameters={},
        return_type="str",
        code=malicious_code,
    )
    factory.register_generated(spec)

    # 3. Assert that getting the tool raises a ValueError
    with pytest.raises(ValueError, match="Forbidden import: os"):
        factory.get_tool("malicious_tool")


def test_get_tool_blocks_dangerous_function_calls():
    """Tests that get_tool() blocks dangerous function calls."""
    # 1. Setup
    mock_llm_client = Mock()
    mock_sandbox_executor = Mock()
    factory = ToolFactory(llm_client=mock_llm_client, sandbox_executor=mock_sandbox_executor)

    # 2. Create another malicious tool spec
    malicious_code = "exec('print(\"malicious\")')"
    spec = ToolSpec(
        name="malicious_tool_2",
        description="A tool that tries to use exec.",
        parameters={},
        return_type="None",
        code=malicious_code,
    )
    factory.register_generated(spec)

    # 3. Assert that getting the tool raises a ValueError
    with pytest.raises(ValueError, match="Forbidden function: exec"):
        factory.get_tool("malicious_tool_2")


def test_get_tool_allows_safe_code():
    """Tests that get_tool() allows safe code to be executed."""
    # 1. Setup
    mock_llm_client = Mock()
    mock_sandbox_executor = Mock()
    factory = ToolFactory(llm_client=mock_llm_client, sandbox_executor=mock_sandbox_executor)

    # 2. Create safe tool spec
    safe_code = "def safe_tool(a, b):\n    return a + b"
    spec = ToolSpec(
        name="safe_tool",
        description="A safe tool.",
        parameters={"a": {"type": "int"}, "b": {"type": "int"}},
        return_type="int",
        code=safe_code,
    )
    factory.register_generated(spec)

    # 3. Get the tool and execute it
    tool_func = factory.get_tool("safe_tool")
    assert callable(tool_func)
    assert tool_func(2, 3) == 5
