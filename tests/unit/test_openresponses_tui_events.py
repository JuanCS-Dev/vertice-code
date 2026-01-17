"""Testes para Open Responses Events na TUI."""

from vertice_tui.core.openresponses_events import (
    OpenResponsesEvent,
    parse_open_responses_event,
)


class TestOpenResponsesEvent:
    """Testes para parsing de eventos Open Responses."""

    def test_parse_response_created_event(self):
        """Test parsing response.created event."""
        sse_line = 'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_123","status":"in_progress","model":"gemini-3-pro"}}\n\n'

        event = parse_open_responses_event(sse_line)

        assert isinstance(event, OpenResponsesEvent)
        assert event.event_type == "response.created"
        assert event.sequence_number == 1
        assert event.raw_data["type"] == "response.created"

    def test_parse_response_in_progress_event(self):
        """Test parsing response.in_progress event."""
        sse_line = 'event: response.in_progress\ndata: {"type":"response.in_progress","sequence_number":2,"response":{"id":"resp_123","status":"in_progress"}}\n\n'

        event = parse_open_responses_event(sse_line)

        assert isinstance(event, OpenResponsesEvent)
        assert event.event_type == "response.in_progress"
        assert event.sequence_number == 2

    def test_parse_output_text_delta_event(self):
        """Test parsing response.output_text.delta event."""
        sse_line = 'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"item_id":"msg_456","output_index":0,"content_index":0,"delta":"Hello"}\n\n'

        event = parse_open_responses_event(sse_line)

        assert isinstance(event, OpenResponsesEvent)
        assert event.event_type == "response.output_text.delta"
        assert event.sequence_number == 5
        assert event.raw_data["delta"] == "Hello"

    def test_parse_response_completed_event(self):
        """Test parsing response.completed event."""
        sse_line = 'event: response.completed\ndata: {"type":"response.completed","sequence_number":10,"response":{"id":"resp_123","status":"completed","usage":{"input_tokens":10,"output_tokens":20,"total_tokens":30}}}\n\n'

        event = parse_open_responses_event(sse_line)

        assert isinstance(event, OpenResponsesEvent)
        assert event.event_type == "response.completed"
        assert event.sequence_number == 10

    def test_parse_invalid_event(self):
        """Test parsing invalid SSE line."""
        sse_line = "invalid line"

        event = parse_open_responses_event(sse_line)

        assert event is None

    def test_sequence_numbers(self):
        """Test that sequence numbers are properly tracked."""
        events_data = [
            (
                'event: response.created\ndata: {"type":"response.created","sequence_number":1,"response":{"id":"resp_1"}}\n\n',
                1,
            ),
            (
                'event: response.in_progress\ndata: {"type":"response.in_progress","sequence_number":2,"response":{"id":"resp_1"}}\n\n',
                2,
            ),
            (
                'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","sequence_number":5,"delta":"test"}\n\n',
                5,
            ),
            (
                'event: response.completed\ndata: {"type":"response.completed","sequence_number":10,"response":{"id":"resp_1"}}\n\n',
                10,
            ),
        ]

        for sse_line, expected_seq in events_data:
            event = parse_open_responses_event(sse_line)
            assert event is not None
            assert event.sequence_number == expected_seq
