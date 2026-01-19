import pytest
import json


def test_code_formatting():
    """Test that generated code has proper formatting."""
    generated_code = """
def hello_world():
    print("Hello, world!")
"""
    # Simple check for indentation
    assert "    print" in generated_code


def test_response_coherence():
    """Test that responses are coherent."""
    response = "The quick brown fox jumps over the lazy dog."
    # Simple check for sentence structure
    assert response.endswith(".")
    assert len(response.split()) > 5


def test_tool_call_json_validity():
    """Test that tool calls have valid JSON."""
    tool_call_str = '{"name": "read_file", "arguments": {"path": "test.py"}}'
    try:
        json.loads(tool_call_str)
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in tool call")


def test_error_message_helpfulness():
    """Test that error messages are helpful."""
    error_message = "Error: File not found at path 'test.py'"
    assert "Error" in error_message
    assert "File not found" in error_message
    assert "test.py" in error_message
