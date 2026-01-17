"""
Open Responses E2E Tests - Integration Tests

Testa a integração completa entre TUI, CLI e WebApp com Open Responses.
Cenários realistas de uso end-to-end.
"""

import pytest
from tests.e2e.openresponses import get_e2e_tester


class TestOpenResponsesIntegrationE2E:
    """Testes de integração completa Open Responses."""

    @pytest.fixture
    async def tester(self):
        """Fixture para o tester e2e."""
        tester = get_e2e_tester()
        await tester.setup()
        yield tester
        await tester.teardown()

    @pytest.mark.asyncio
    async def test_full_system_open_responses_workflow(self, tester):
        """Test workflow completo do sistema com Open Responses."""
        result = tester.start_test(
            "full_system_open_responses_workflow",
            "integration",
            "open_responses",
            "complete_workflow",
        )

        try:
            # 1. Test CLI provider capabilities
            cli_success = await tester.test_cli_open_responses_integration(result)

            # 2. Test structured output pipeline
            structured_success = await tester.test_structured_output_e2e(result)

            # 3. Test multimodal processing
            multimodal_success = await tester.test_multimodal_input_processing(result)

            # 4. Test TUI event parsing
            tui_success = await tester.test_tui_open_responses_parsing(result)

            # Overall success
            success = cli_success and structured_success and multimodal_success and tui_success

            result.add_metric("cli_integration", cli_success)
            result.add_metric("structured_output", structured_success)
            result.add_metric("multimodal_processing", multimodal_success)
            result.add_metric("tui_parsing", tui_success)
            result.add_metric("full_system_integration", success)

            result.mark_complete(success)

            assert success, "Full system integration should work"

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_cross_component_reasoning_flow(self, tester):
        """Test fluxo de reasoning entre componentes."""
        result = tester.start_test(
            "cross_component_reasoning_flow", "integration", "open_responses", "reasoning_flow"
        )

        try:
            from vertice_core.openresponses_types import ReasoningItem
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # 1. Criar reasoning item (como CLI/agents fariam)
            reasoning = ReasoningItem()
            reasoning.append_content(
                "Analisando solicitação do usuário sobre desenvolvimento de software..."
            )
            reasoning.append_content(
                "Identificando requisitos: modularidade, testabilidade, documentação"
            )
            reasoning.set_summary(
                "Solicitação analisada: desenvolvimento de aplicação Python com foco em qualidade"
            )

            # 2. Stream reasoning (como providers fariam)
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
            builder.start()
            reasoning_item = builder.add_reasoning()

            for word in ["Processando", "requisitos...", "Otimizando", "solução..."]:
                builder.reasoning_delta(reasoning_item, f"{word} ")

            builder.complete()

            # 3. Parse events (como TUI/WebApp fariam)
            from vertice_tui.core.openresponses_events import parse_open_responses_event

            events = builder.get_events()
            parsed_events = []

            for event in events:
                sse_line = event.to_sse()
                parsed = parse_open_responses_event(sse_line)
                if parsed:
                    parsed_events.append(parsed.event_type)

            # Validar fluxo completo
            assert len(parsed_events) > 5, "Should have multiple parsed events"
            assert (
                "response.reasoning_content.delta" in parsed_events
            ), "Should have reasoning delta events"
            assert "response.completed" in parsed_events, "Should complete successfully"

            result.add_metric("reasoning_content_length", len(reasoning.get_reasoning_text()))
            result.add_metric("reasoning_summary_length", len(reasoning.get_summary_text()))
            result.add_metric("stream_events_created", len(events))
            result.add_metric("events_parsed_successfully", len(parsed_events))
            result.add_metric("cross_component_flow_valid", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_open_responses_protocol_compatibility(self, tester):
        """Test compatibilidade entre diferentes protocolos Open Responses."""
        result = tester.start_test(
            "open_responses_protocol_compatibility", "integration", "both", "protocol_compatibility"
        )

        try:
            from vertice_core.openresponses_types import (
                MessageItem,
                ReasoningItem,
                FunctionCallItem,
                UrlCitation,
                JsonSchemaResponseFormat,
            )

            # Test 1: Message items com annotations
            message = MessageItem(role="assistant")
            # Adicionar conteúdo primeiro antes de tentar acessar
            message.append_text("Sample content for testing citations")
            message.add_citation("https://docs.python.org", "Python Docs", 0, 10)
            message.add_citation("https://github.com/example", "Example Repo", 15, 25)

            assert len(message.content[-1].annotations) == 2, "Should have 2 citations"
            assert isinstance(
                message.content[-1].annotations[0], UrlCitation
            ), "Should be UrlCitation"
            assert isinstance(
                message.content[-1].annotations[1], UrlCitation
            ), "Should be UrlCitation"

            # Test 2: Reasoning com structured output
            reasoning = ReasoningItem()
            reasoning.append_content("Planning structured response...")
            reasoning.set_summary("Response structure planned")

            # Test 3: Function calls com citations
            function_call = FunctionCallItem(
                name="search_docs", arguments='{"query":"python async"}'
            )

            # Test 4: JSON Schema validation
            schema = JsonSchemaResponseFormat(
                name="search_results",
                schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array", "items": {"type": "string"}},
                        "total": {"type": "integer"},
                    },
                },
            )

            # Validar estruturas
            message_dict = message.to_dict()
            reasoning_dict = reasoning.to_dict()
            function_dict = function_call.to_dict()
            schema_dict = schema.to_dict()

            assert "annotations" in message_dict["content"][0], "Message should have annotations"
            assert "summary" in reasoning_dict, "Reasoning should have summary"
            assert function_dict["name"] == "search_docs", "Function call should have name"
            assert schema_dict["json_schema"]["name"] == "search_results", "Schema should have name"

            result.add_metric("message_with_annotations", True)
            result.add_metric("reasoning_with_summary", True)
            result.add_metric("function_call_valid", True)
            result.add_metric("schema_format_valid", True)
            result.add_metric("protocol_compatibility", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_performance_and_scalability(self, tester):
        """Test performance e escalabilidade do sistema Open Responses."""
        result = tester.start_test(
            "performance_and_scalability", "integration", "open_responses", "performance_test"
        )

        try:
            import time
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # Test 1: Stream building performance
            start_time = time.time()
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")

            # Criar stream complexo
            builder.start()
            message = builder.add_message()

            # Adicionar muito texto (simulando response grande)
            for i in range(100):
                builder.text_delta(message, f"Chunk {i} with some content. ")

            reasoning = builder.add_reasoning()
            for i in range(50):
                builder.reasoning_delta(reasoning, f"Thought {i}. ")

            builder.complete()

            stream_time = time.time() - start_time

            # Test 2: Event parsing performance
            events = builder.get_events()
            start_time = time.time()

            from vertice_tui.core.openresponses_events import parse_open_responses_event

            parsed_count = 0
            for event in events:
                sse_line = event.to_sse()
                parsed = parse_open_responses_event(sse_line)
                if parsed:
                    parsed_count += 1

            parse_time = time.time() - start_time

            # Métricas de performance
            result.add_metric("stream_build_time_ms", int(stream_time * 1000))
            result.add_metric("events_created", len(events))
            result.add_metric("parse_time_ms", int(parse_time * 1000))
            result.add_metric("events_parsed", parsed_count)
            result.add_metric(
                "avg_parse_time_per_event_us", int((parse_time / len(events)) * 1000000)
            )

            # Asserts de performance
            assert stream_time < 5.0, f"Stream building too slow: {stream_time}s"
            assert parse_time < 2.0, f"Event parsing too slow: {parse_time}s"
            assert parsed_count == len(
                events
            ), f"Failed to parse {len(events) - parsed_count} events"

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, tester):
        """Test tratamento de erros e recuperação."""
        result = tester.start_test(
            "error_handling_and_recovery", "integration", "open_responses", "error_recovery"
        )

        try:
            from vertice_core.openresponses_types import OpenResponsesError, ErrorType
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # Test 1: Error creation and handling
            errors = [
                OpenResponsesError(
                    ErrorType.INVALID_REQUEST, "invalid_model", "Model not found", "model"
                ),
                OpenResponsesError(ErrorType.SERVER_ERROR, "timeout", "Request timed out"),
                OpenResponsesError(
                    ErrorType.MODEL_ERROR, "generation_failed", "Model failed to generate"
                ),
            ]

            for error in errors:
                error_dict = error.to_dict()
                assert "type" in error_dict, f"Error should have type: {error_dict}"
                assert "message" in error_dict, f"Error should have message: {error_dict}"

            # Test 2: Error propagation in stream
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
            builder.start()

            # Simular erro durante streaming
            error = OpenResponsesError(
                ErrorType.SERVER_ERROR,
                "stream_interrupted",
                "Stream was interrupted due to network issues",
            )

            builder.fail(error)
            events = builder.get_events()

            # Verificar evento de erro
            error_events = [e for e in events if e.type == "response.failed"]
            assert len(error_events) == 1, "Should have error event"

            error_event = error_events[0]
            assert error_event.error, "Error event should contain error data"
            assert "type" in error_event.error, "Error should have type"

            result.add_metric("errors_created", len(errors))
            result.add_metric("error_events_generated", len(error_events))
            result.add_metric("error_propagation_working", True)
            result.add_metric("error_recovery_mechanism", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_real_world_scenario_simulation(self, tester):
        """Test simulação de cenário real de uso."""
        result = tester.start_test(
            "real_world_scenario_simulation", "integration", "open_responses", "real_world_usage"
        )

        try:
            # Simular cenário: Developer usando Open Responses para code review
            from vertice_core.openresponses_types import (
                MessageItem,
                ReasoningItem,
                OutputTextContent,
                JsonSchemaResponseFormat,
            )
            from vertice_core.openresponses_stream import OpenResponsesStreamBuilder

            # 1. User message with code
            user_message = MessageItem(role="user")
            user_message.content = [
                OutputTextContent(
                    text="""
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Test
print(calculate_fibonacci(10))
"""
                )
            ]

            # 2. AI reasoning about the code
            reasoning = ReasoningItem()
            reasoning.append_content("Analisando função Fibonacci...")
            reasoning.append_content(
                "Problema identificado: implementação recursiva ineficiente para n > 30"
            )
            reasoning.append_content("Solução: implementar versão iterativa com memoização")
            reasoning.set_summary("Código tem problema de performance para valores grandes de n")

            # 3. AI response with structured suggestions
            ai_response = MessageItem(role="assistant")
            ai_response.content = [
                OutputTextContent(
                    text="Sua implementação recursiva funciona, mas terá problemas de performance para n > 30 devido à exponencial complexidade."
                )
            ]

            # Adicionar citações
            ai_response.add_citation(
                "https://en.wikipedia.org/wiki/Fibonacci_sequence", "Fibonacci Sequence - Wikipedia"
            )
            ai_response.add_citation(
                "https://docs.python.org/3/tutorial/controlflow.html", "Python Control Flow"
            )

            # 4. Structured output for code suggestions
            code_suggestion_schema = JsonSchemaResponseFormat(
                name="code_review_suggestions",
                schema={
                    "type": "object",
                    "properties": {
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["low", "medium", "high"],
                                    },
                                    "description": {"type": "string"},
                                    "line": {"type": "integer"},
                                    "suggestion": {"type": "string"},
                                },
                            },
                        },
                        "overall_rating": {
                            "type": "string",
                            "enum": ["poor", "fair", "good", "excellent"],
                        },
                    },
                },
            )

            # 5. Stream the complete interaction
            builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
            builder.start()

            # Add reasoning
            reasoning_stream = builder.add_reasoning()
            for thought in reasoning.content:
                if isinstance(thought, OutputTextContent):
                    builder.reasoning_delta(reasoning_stream, thought.text)

            # Add response
            response_item = builder.add_message()
            builder.text_delta(response_item, ai_response.get_text())

            builder.complete()

            # Validate complete scenario
            events = builder.get_events()
            user_dict = user_message.to_dict()
            reasoning_dict = reasoning.to_dict()
            response_dict = ai_response.to_dict()
            schema_dict = code_suggestion_schema.to_dict()

            # Assertions
            assert len(events) > 10, "Should have comprehensive event stream"
            assert "content" in user_dict, "User message should have content"
            assert "summary" in reasoning_dict, "Reasoning should have summary"
            assert len(ai_response.annotations) == 2, "Response should have citations"
            assert (
                schema_dict["json_schema"]["name"] == "code_review_suggestions"
            ), "Schema should be configured"

            result.add_metric("scenario_events", len(events))
            result.add_metric("user_message_valid", True)
            result.add_metric("reasoning_complete", True)
            result.add_metric("response_with_citations", len(ai_response.annotations))
            result.add_metric("structured_schema_valid", True)
            result.add_metric("real_world_scenario_success", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")
