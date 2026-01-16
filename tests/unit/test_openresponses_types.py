"""Testes para Open Responses Types."""

import pytest
from vertice_core.openresponses_types import (
    ItemStatus,
    MessageRole,
    MessageItem,
    FunctionCallItem,
    FunctionCallOutputItem,
    OutputTextContent,
    OpenResponse,
    TokenUsage,
    OpenResponsesError,
    ErrorType,
)


class TestItemStatus:
    """Testes para ItemStatus enum."""

    def test_values(self):
        assert ItemStatus.IN_PROGRESS.value == "in_progress"
        assert ItemStatus.COMPLETED.value == "completed"
        assert ItemStatus.INCOMPLETE.value == "incomplete"
        assert ItemStatus.FAILED.value == "failed"


class TestMessageItem:
    """Testes para MessageItem."""

    def test_creation(self):
        item = MessageItem()
        assert item.type == "message"
        assert item.id.startswith("msg_")
        assert item.role == MessageRole.ASSISTANT
        assert item.status == ItemStatus.IN_PROGRESS
        assert item.content == []

    def test_to_dict(self):
        item = MessageItem(role=MessageRole.USER)
        d = item.to_dict()
        assert d["type"] == "message"
        assert d["role"] == "user"
        assert d["status"] == "in_progress"

    def test_append_text(self):
        item = MessageItem()
        item.append_text("Hello")
        item.append_text(" World")
        assert item.get_text() == "Hello World"

    def test_get_text_empty(self):
        item = MessageItem()
        assert item.get_text() == ""


class TestFunctionCallItem:
    """Testes para FunctionCallItem."""

    def test_creation(self):
        item = FunctionCallItem(name="get_weather", arguments='{"location":"SF"}')
        assert item.type == "function_call"
        assert item.id.startswith("fc_")
        assert item.name == "get_weather"
        assert item.arguments == '{"location":"SF"}'


class TestOpenResponse:
    """Testes para OpenResponse."""

    def test_creation(self):
        resp = OpenResponse(model="gemini-3-pro")
        assert resp.id.startswith("resp_")
        assert resp.status == ItemStatus.IN_PROGRESS
        assert resp.model == "gemini-3-pro"
        assert resp.output == []

    def test_add_message(self):
        resp = OpenResponse()
        msg = resp.add_message()
        assert len(resp.output) == 1

        # Test with custom role
        msg2 = resp.add_message(MessageRole.USER)
        assert msg2.role == MessageRole.USER

    def test_add_function_call(self):
        resp = OpenResponse()
        fc = resp.add_function_call("get_weather", '{"location":"SF"}')
        assert len(resp.output) == 1
        assert fc.name == "get_weather"
        assert fc.arguments == '{"location":"SF"}'

    def test_complete(self):
        resp = OpenResponse()
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        resp.complete(usage)

        assert resp.status == ItemStatus.COMPLETED
        assert resp.usage == usage

    def test_fail(self):
        resp = OpenResponse()
        error = OpenResponsesError(type=ErrorType.SERVER_ERROR, message="Test error")
        resp.fail(error)

        assert resp.status == ItemStatus.FAILED
        assert resp.error == error

    def test_to_dict(self):
        resp = OpenResponse(model="test-model")
        d = resp.to_dict()

        assert d["id"] == resp.id
        assert d["status"] == "in_progress"
        assert d["model"] == "test-model"
        assert d["output"] == []


class TestTokenUsage:
    """Testes para TokenUsage."""

    def test_creation(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_to_dict(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        d = usage.to_dict()
        assert d["input_tokens"] == 100
        assert d["output_tokens"] == 50
        assert d["total_tokens"] == 0


class TestOpenResponsesError:
    """Testes para OpenResponsesError."""

    def test_creation(self):
        error = OpenResponsesError(
            type=ErrorType.INVALID_REQUEST,
            code="test_error",
            message="Test message",
            param="test_param",
        )
        assert error.type == ErrorType.INVALID_REQUEST
        assert error.code == "test_error"
        assert error.message == "Test message"
        assert error.param == "test_param"

    def test_to_dict(self):
        error = OpenResponsesError(type=ErrorType.SERVER_ERROR, message="Server error")
        d = error.to_dict()

        assert d["type"] == "server_error"
        assert d["code"] == "server_error"
        assert d["message"] == "Server error"
        assert "param" not in d

    def test_to_dict_with_param(self):
        error = OpenResponsesError(type=ErrorType.INVALID_REQUEST, param="model")
        d = error.to_dict()
        assert d["param"] == "model"


class TestOutputTextContent:
    """Testes para OutputTextContent."""

    def test_creation(self):
        content = OutputTextContent(text="Hello world")
        assert content.type == "output_text"
        assert content.text == "Hello world"
        assert content.annotations == []

    def test_to_dict(self):
        content = OutputTextContent(text="Test")
        d = content.to_dict()
        assert d["type"] == "output_text"
        assert d["text"] == "Test"
        assert d["annotations"] == []


class TestFunctionCallOutputItem:
    """Testes para FunctionCallOutputItem."""

    def test_creation(self):
        item = FunctionCallOutputItem(call_id="call_123", output='{"result": "success"}')
        assert item.type == "function_call_output"
        assert item.call_id == "call_123"
        assert item.output == '{"result": "success"}'
        assert item.status == ItemStatus.COMPLETED

    def test_to_dict(self):
        item = FunctionCallOutputItem(call_id="call_456", output="result")
        d = item.to_dict()
        assert d["type"] == "function_call_output"
        assert d["call_id"] == "call_456"
        assert d["output"] == "result"
