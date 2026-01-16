"""
Testes de Integração para Open Responses.

Este módulo testa a integração completa do sistema Open Responses,
incluindo fluxos end-to-end, streaming e interoperabilidade.
"""

import pytest
from typing import List

from vertice_core.openresponses_types import (
    ItemStatus,
    MessageRole,
    MessageItem,
    FunctionCallItem,
    FunctionCallOutputItem,
    ReasoningItem,
    SummaryTextContent,
    OpenResponse,
    TokenUsage,
    OpenResponsesError,
    ErrorType,
    UrlCitation,
    JsonSchemaResponseFormat,
    VerticeTelemetryItem,
    VerticeGovernanceItem,
)
from vertice_core.openresponses_stream import (
    OpenResponsesStreamBuilder,
    ResponseCreatedEvent,
    ResponseCompletedEvent,
    OutputTextDeltaEvent,
    ReasoningContentDeltaEvent,
)
from vertice_core.openresponses_multimodal import (
    InputImageContent,
    InputFileContent,
    ImageDetail,
)
from vertice_tui.core.openresponses_events import (
    OpenResponsesEvent,
    OpenResponsesOutputTextDeltaEvent,
    parse_open_responses_event,
)


class TestCompleteResponseFlow:
    """Testes de fluxo completo de resposta."""

    def test_simple_text_response(self):
        """Testa resposta simples de texto."""
        response = OpenResponse(model="gemini-3-pro")
        
        message = response.add_message()
        message.append_text("Hello, how can I help you?")
        message.status = ItemStatus.COMPLETED
        
        response.complete()
        
        assert response.status == ItemStatus.COMPLETED
        assert len(response.output) == 1
        assert response.output[0].get_text() == "Hello, how can I help you?"

    def test_response_with_reasoning(self):
        """Testa resposta com raciocínio."""
        response = OpenResponse(model="gemini-3-pro")
        
        # Adiciona reasoning
        reasoning = ReasoningItem()
        reasoning.append_content("Step 1: Understand the question\n")
        reasoning.append_content("Step 2: Formulate answer\n")
        reasoning.set_summary("Analyzed question and prepared response")
        reasoning.status = ItemStatus.COMPLETED
        response.output.append(reasoning)
        
        # Adiciona resposta
        message = response.add_message()
        message.append_text("Based on my analysis, the answer is 42.")
        message.status = ItemStatus.COMPLETED
        
        response.complete()
        
        assert len(response.output) == 2
        assert response.output[0].type == "reasoning"
        assert response.output[1].type == "message"
        assert "42" in response.output[1].get_text()

    def test_response_with_function_call(self):
        """Testa resposta com chamada de função."""
        response = OpenResponse(model="gemini-3-pro")
        
        # Modelo solicita função
        fc = response.add_function_call("get_weather", '{"location": "São Paulo"}')
        fc.status = ItemStatus.COMPLETED
        
        # Desenvolver envia resultado
        fc_output = FunctionCallOutputItem(
            call_id=fc.call_id,
            output='{"temperature": 25, "condition": "sunny"}',
        )
        response.output.append(fc_output)
        
        # Modelo responde com base no resultado
        message = response.add_message()
        message.append_text("The weather in São Paulo is sunny, 25°C.")
        message.status = ItemStatus.COMPLETED
        
        response.complete()
        
        assert len(response.output) == 3
        assert response.output[0].type == "function_call"
        assert response.output[1].type == "function_call_output"
        assert response.output[2].type == "message"

    def test_response_with_citations(self):
        """Testa resposta com citações."""
        response = OpenResponse(model="gemini-3-pro")
        
        message = response.add_message()
        message.append_text("Python was created by Guido van Rossum in 1991.")
        
        # Adiciona citação
        message.content[0].annotations.append(UrlCitation(
            url="https://en.wikipedia.org/wiki/Python",
            title="Python - Wikipedia",
            start_index=0,
            end_index=47,
        ))
        message.status = ItemStatus.COMPLETED
        
        response.complete()
        
        assert len(message.content[0].annotations) == 1
        assert message.content[0].annotations[0].url == "https://en.wikipedia.org/wiki/Python"

    def test_response_with_telemetry(self):
        """Testa resposta com telemetria Vertice."""
        response = OpenResponse(model="gemini-3-pro")
        
        message = response.add_message()
        message.append_text("Response content")
        message.status = ItemStatus.COMPLETED
        
        # Adiciona telemetria
        telemetry = VerticeTelemetryItem(
            latency_ms=142,
            cache_hit=False,
            model="gemini-3-pro",
            provider="vertex-ai",
            tokens_input=50,
            tokens_output=30,
        )
        response.output.append(telemetry)
        
        response.complete()
        
        assert len(response.output) == 2
        assert response.output[1].type == "vertice:telemetry"
        assert response.output[1].latency_ms == 142


class TestStreamingIntegration:
    """Testes de integração de streaming."""

    def test_stream_simple_message(self):
        """Testa streaming de mensagem simples."""
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        
        builder.start()
        message = builder.add_message()
        builder.text_delta(message, "Hello ")
        builder.text_delta(message, "World!")
        builder.complete()
        
        events = builder.get_events()
        
        # Verifica sequência de eventos
        event_types = [e.type for e in events]
        assert "response.created" in event_types
        assert "response.output_text.delta" in event_types
        assert "response.completed" in event_types

    def test_stream_with_reasoning(self):
        """Testa streaming com raciocínio."""
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        
        builder.start()
        
        # Stream reasoning
        reasoning = builder.add_reasoning()
        builder.reasoning_delta(reasoning, "Thinking...")
        builder.reasoning_delta(reasoning, " Processing...")
        
        # Stream message
        message = builder.add_message()
        builder.text_delta(message, "The answer is 42")
        
        builder.complete()
        
        events = builder.get_events()
        event_types = [e.type for e in events]
        
        assert "response.reasoning_content.delta" in event_types
        assert "response.output_text.delta" in event_types

    def test_sse_format(self):
        """Testa formato SSE de saída."""
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        
        builder.start()
        message = builder.add_message()
        builder.text_delta(message, "Test")
        builder.complete()
        
        sse_output = list(builder.get_pending_events_sse())
        
        # Verifica formato SSE
        for sse in sse_output:
            assert "event: " in sse
            assert "data: " in sse
            assert sse.endswith("\n\n")

    def test_done_event(self):
        """Testa evento terminal DONE."""
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        
        done = builder.done()
        
        assert done == "data: [DONE]\n\n"


class TestTUIEventParsing:
    """Testes de parsing de eventos para TUI."""

    def test_parse_text_delta(self):
        """Testa parsing de delta de texto."""
        sse_line = 'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_123","delta":"Hello World"}\n\n'
        
        event = parse_open_responses_event(sse_line)
        
        assert event is not None
        assert isinstance(event, OpenResponsesOutputTextDeltaEvent)
        assert event.delta == "Hello World"

    def test_parse_invalid_returns_none(self):
        """Testa que linha inválida retorna None."""
        event = parse_open_responses_event("invalid line")
        assert event is None

    def test_event_sequence_numbers(self):
        """Testa que sequence numbers são extraídos."""
        sse_line = 'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_123"}}\n\n'
        
        event = parse_open_responses_event(sse_line)
        
        assert event is not None
        assert event.sequence_number == 1


class TestMultimodalIntegration:
    """Testes de integração multimodal."""

    def test_image_content_url(self):
        """Testa conteúdo de imagem via URL."""
        img = InputImageContent(
            image_url="https://example.com/image.png",
            detail=ImageDetail.HIGH,
        )
        
        d = img.to_dict()
        
        assert d["type"] == "input_image"
        assert d["image_url"] == "https://example.com/image.png"
        assert d["detail"] == "high"

    def test_image_content_base64(self):
        """Testa conteúdo de imagem via base64."""
        img = InputImageContent(
            image_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            media_type="image/png",
        )
        
        d = img.to_dict()
        
        assert d["type"] == "input_image"
        assert "image_base64" in d
        assert d["media_type"] == "image/png"

    def test_file_content(self):
        """Testa conteúdo de arquivo."""
        file = InputFileContent(
            file_data="SGVsbG8gV29ybGQ=",  # "Hello World" in base64
            media_type="text/plain",
            filename="hello.txt",
        )
        
        d = file.to_dict()
        
        assert d["type"] == "input_file"
        assert d["filename"] == "hello.txt"


class TestStructuredOutput:
    """Testes de structured output."""

    def test_json_schema_format(self):
        """Testa formato JSON Schema."""
        schema = JsonSchemaResponseFormat(
            name="user_info",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name"],
            },
        )
        
        d = schema.to_dict()
        
        assert d["type"] == "json_schema"
        assert d["json_schema"]["name"] == "user_info"
        assert d["json_schema"]["strict"] is True

    def test_json_schema_with_description(self):
        """Testa JSON Schema com descrição."""
        schema = JsonSchemaResponseFormat(
            name="restaurant",
            description="A restaurant recommendation",
            schema={"type": "object"},
        )
        
        d = schema.to_dict()
        
        assert "description" in d["json_schema"]


class TestErrorHandling:
    """Testes de tratamento de erros."""

    def test_response_failure(self):
        """Testa falha de resposta."""
        response = OpenResponse(model="gemini-3-pro")
        
        error = OpenResponsesError(
            type=ErrorType.MODEL_ERROR,
            code="rate_limit_exceeded",
            message="Too many requests",
        )
        response.fail(error)
        
        assert response.status == ItemStatus.FAILED
        assert response.error is not None
        assert response.error.type == ErrorType.MODEL_ERROR

    def test_stream_failure(self):
        """Testa falha durante streaming."""
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        
        builder.start()
        message = builder.add_message()
        builder.text_delta(message, "Partial...")
        
        error = OpenResponsesError(
            type=ErrorType.SERVER_ERROR,
            message="Connection lost",
        )
        builder.fail(error)
        
        events = builder.get_events()
        last_event = events[-1]
        
        assert last_event.type == "response.failed"
