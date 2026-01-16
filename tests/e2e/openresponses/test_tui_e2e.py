"""
Open Responses E2E Tests - TUI Component

Testa a integração Open Responses na TUI (Textual UI).
Foca em parsing de eventos SSE e handling de responses.
"""

import pytest
from tests.e2e.openresponses import get_e2e_tester, E2ETestResult


class TestOpenResponsesTUIE2E:
    """Testes E2E para Open Responses na TUI."""

    @pytest.fixture
    async def tester(self):
        """Fixture para o tester e2e."""
        tester = get_e2e_tester()
        await tester.setup()
        yield tester
        await tester.teardown()

    @pytest.mark.asyncio
    async def test_tui_event_parsing_basic(self, tester):
        """Test parsing básico de eventos Open Responses."""
        result = tester.start_test(
            "tui_event_parsing_basic", "tui", "open_responses", "basic_event_parsing"
        )

        try:
            success = await tester.test_tui_open_responses_parsing(result)
            result.mark_complete(success)

            # Assertions
            assert result.success, f"Test failed with errors: {result.errors}"
            assert result.metrics.get("total_parsed", 0) >= 4, "Should parse at least 4 events"
            assert "response.created" in result.metrics.get("parsed_events", []), (
                "Should parse response.created"
            )
            assert "response.completed" in result.metrics.get("parsed_events", []), (
                "Should parse response.completed"
            )

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_tui_response_view_integration(self, tester):
        """Test integração com ResponseView widget."""
        result = tester.start_test(
            "tui_response_view_integration", "tui", "open_responses", "response_view_handling"
        )

        try:
            from vertice_tui.widgets.response_view import ResponseView
            from vertice_tui.core.openresponses_events import OpenResponsesEvent

            # Criar ResponseView
            view = ResponseView()

            # Simular evento Open Responses
            mock_event = OpenResponsesEvent(
                event_type="response.created",
                sequence_number=1,
                raw_data={"type": "response.created", "response": {"id": "test_123"}},
            )

            # Testar handling do evento
            view.handle_open_responses_event(mock_event)

            result.add_metric("view_created", True)
            result.add_metric("event_handled", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_tui_streaming_sequence(self, tester):
        """Test sequência completa de streaming na TUI."""
        result = tester.start_test(
            "tui_streaming_sequence", "tui", "open_responses", "complete_streaming_flow"
        )

        try:
            from vertice_tui.core.openresponses_events import parse_open_responses_event

            # Sequência completa de eventos SSE
            sse_sequence = [
                'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_001","model":"gemini-3-pro"}}\n\n',
                'event: response.in_progress\ndata: {"type":"response.in_progress","sequence_number":2,"response":{"id":"resp_001"}}\n\n',
                'event: response.output_item.added\ndata: {"type":"response.output_item.added","sequence_number":3,"item":{"id":"msg_001","type":"message","role":"assistant"}}\n\n',
                'event: response.content_part.added\ndata: {"type":"response.content_part.added","sequence_number":4,"item_id":"msg_001","part":{"type":"output_text"}}\n\n',
                'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_001","delta":"Olá"}\n\n',
                'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":6,"item_id":"msg_001","delta":" mundo!"}\n\n',
                'event: response.output_text.done\ndata: {"type":"response.output_text.done","sequence_number":7,"item_id":"msg_001","text":"Olá mundo!"}\n\n',
                'event: response.content_part.done\ndata: {"type":"response.content_part.done","sequence_number":8,"item_id":"msg_001"}\n\n',
                'event: response.output_item.done\ndata: {"type":"response.output_item.done","sequence_number":9,"item":{"id":"msg_001","status":"completed"}}\n\n',
                'event: response.completed\ndata: {"type":"response.completed","sequence_number":10,"response":{"id":"resp_001","status":"completed","usage":{"input_tokens":2,"output_tokens":3,"total_tokens":5}}}\n\n',
                "data: [DONE]\n\n",
            ]

            events_parsed = []
            sequence_numbers = []

            for sse_line in sse_sequence:
                event = parse_open_responses_event(sse_line)
                if event:
                    events_parsed.append(event.event_type)
                    sequence_numbers.append(event.sequence_number)

            # Validar sequência
            expected_events = [
                "response.created",
                "response.in_progress",
                "response.output_item.added",
                "response.content_part.added",
                "response.output_text.delta",
                "response.output_text.delta",
                "response.output_text.done",
                "response.content_part.done",
                "response.output_item.done",
                "response.completed",
            ]

            assert events_parsed == expected_events, f"Event sequence mismatch: {events_parsed}"
            assert sequence_numbers == list(range(1, 11)), (
                f"Sequence numbers incorrect: {sequence_numbers}"
            )

            result.add_metric("events_parsed", len(events_parsed))
            result.add_metric("sequence_valid", True)
            result.add_metric("completion_detected", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_tui_reasoning_display(self, tester):
        """Test display de reasoning items na TUI."""
        result = tester.start_test(
            "tui_reasoning_display", "tui", "open_responses", "reasoning_item_display"
        )

        try:
            from vertice_core.openresponses_types import (
                ReasoningItem,
                SummaryTextContent,
                OutputTextContent,
            )

            # Criar reasoning item
            reasoning = ReasoningItem()
            reasoning.append_content("Pensando sobre a pergunta do usuário...")
            reasoning.set_summary("Análise completa da query realizada")

            # Testar formatação
            content_text = reasoning.get_reasoning_text()
            summary_text = reasoning.get_summary_text()

            assert "Pensando sobre a pergunta" in content_text
            assert "Análise completa" in summary_text

            result.add_metric("reasoning_content_length", len(content_text))
            result.add_metric("reasoning_summary_length", len(summary_text))
            result.add_metric("reasoning_item_valid", True)

            result.mark_complete(True)

        except Exception as e:
            result.add_error(f"Exception: {str(e)}")
            result.mark_complete(False)
            pytest.fail(f"Test failed: {str(e)}")
