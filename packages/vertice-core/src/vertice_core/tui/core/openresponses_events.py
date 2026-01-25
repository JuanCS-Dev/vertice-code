"""
Open Responses Events for Vertice TUI.

Defines event classes for handling Open Responses streaming protocol
in the Textual UI framework.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json


@dataclass
class OpenResponsesEvent:
    """
    Base event for Open Responses streaming.

    All Open Responses events inherit from this class.
    """

    event_type: str
    sequence_number: int
    raw_data: Dict[str, Any]

    @classmethod
    def from_sse_line(cls, line: str) -> Optional["OpenResponsesEvent"]:
        """
        Parse SSE line into OpenResponsesEvent.

        Expected format (single line for simplicity):
        event: response.created\\ndata: {"type":"response.created",...}\\n\\n
        """
        lines = line.strip().split("\n")

        if len(lines) < 2 or not lines[0].startswith("event: "):
            return None

        try:
            # Parse event type
            event_type = lines[0].split("event: ")[1].strip()

            # Parse data
            data_line = None
            for line_part in lines:
                if line_part.startswith("data: "):
                    data_line = line_part
                    break

            if not data_line:
                return None

            data_str = data_line[6:].strip()  # Remove "data: "

            if data_str == "[DONE]":
                return OpenResponsesDoneEvent()

            raw_data = json.loads(data_str)
            sequence_number = raw_data.get("sequence_number", 0)

            # Create specific event type based on event_type
            event_class = EVENT_TYPE_TO_CLASS.get(event_type, cls)
            return event_class(
                event_type=event_type, sequence_number=sequence_number, raw_data=raw_data
            )
        except (json.JSONDecodeError, KeyError, IndexError, ValueError):
            pass

        return None


@dataclass
class OpenResponsesDoneEvent(OpenResponsesEvent):
    """Terminal event: [DONE]"""

    event_type: str = "[DONE]"
    sequence_number: int = -1
    raw_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SPECIFIC EVENT TYPES - Used by response_view.py
# =============================================================================


@dataclass
class OpenResponsesResponseCreatedEvent(OpenResponsesEvent):
    """Event: response.created"""

    @property
    def response_id(self) -> str:
        return self.raw_data.get("response", {}).get("id", "")

    @property
    def model(self) -> str:
        return self.raw_data.get("response", {}).get("model", "")


@dataclass
class OpenResponsesResponseInProgressEvent(OpenResponsesEvent):
    """Event: response.in_progress"""

    @property
    def response_id(self) -> str:
        return self.raw_data.get("response", {}).get("id", "")


@dataclass
class OpenResponsesOutputItemAddedEvent(OpenResponsesEvent):
    """Event: response.output_item.added"""

    @property
    def output_index(self) -> int:
        return self.raw_data.get("output_index", 0)

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item", {}).get("id", "")

    @property
    def item_type(self) -> str:
        return self.raw_data.get("item", {}).get("type", "message")


@dataclass
class OpenResponsesOutputTextDeltaEvent(OpenResponsesEvent):
    """Event: response.output_text.delta"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def delta(self) -> str:
        return self.raw_data.get("delta", "")

    @property
    def output_index(self) -> int:
        return self.raw_data.get("output_index", 0)

    @property
    def content_index(self) -> int:
        return self.raw_data.get("content_index", 0)


@dataclass
class OpenResponsesOutputTextDoneEvent(OpenResponsesEvent):
    """Event: response.output_text.done"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def text(self) -> str:
        return self.raw_data.get("text", "")


@dataclass
class OpenResponsesResponseCompletedEvent(OpenResponsesEvent):
    """Event: response.completed"""

    @property
    def response_id(self) -> str:
        return self.raw_data.get("response", {}).get("id", "")

    @property
    def usage(self) -> Dict[str, int]:
        return self.raw_data.get("response", {}).get("usage", {})


@dataclass
class OpenResponsesResponseFailedEvent(OpenResponsesEvent):
    """Event: response.failed"""

    @property
    def response_id(self) -> str:
        return self.raw_data.get("response", {}).get("id", "")

    @property
    def error(self) -> Dict[str, Any]:
        return self.raw_data.get("error", {})


@dataclass
class OpenResponsesContentPartAddedEvent(OpenResponsesEvent):
    """Event: response.content_part.added"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def content_index(self) -> int:
        return self.raw_data.get("content_index", 0)

    @property
    def part(self) -> Dict[str, Any]:
        return self.raw_data.get("part", {})


@dataclass
class OpenResponsesContentPartDoneEvent(OpenResponsesEvent):
    """Event: response.content_part.done"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def content_index(self) -> int:
        return self.raw_data.get("content_index", 0)


@dataclass
class OpenResponsesReasoningContentDeltaEvent(OpenResponsesEvent):
    """Event: response.reasoning_content.delta"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def delta(self) -> str:
        return self.raw_data.get("delta", "")


@dataclass
class OpenResponsesReasoningSummaryDeltaEvent(OpenResponsesEvent):
    """Event: response.reasoning_summary.delta"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def delta(self) -> str:
        return self.raw_data.get("delta", "")


@dataclass
class OpenResponsesFunctionCallArgumentsDeltaEvent(OpenResponsesEvent):
    """Event: response.function_call_arguments.delta"""

    @property
    def item_id(self) -> str:
        return self.raw_data.get("item_id", "")

    @property
    def delta(self) -> str:
        return self.raw_data.get("delta", "")


# Event type mapping for automatic class selection
EVENT_TYPE_TO_CLASS: Dict[str, type] = {
    "response.created": OpenResponsesResponseCreatedEvent,
    "response.in_progress": OpenResponsesResponseInProgressEvent,
    "response.output_item.added": OpenResponsesOutputItemAddedEvent,
    "response.output_text.delta": OpenResponsesOutputTextDeltaEvent,
    "response.output_text.done": OpenResponsesOutputTextDoneEvent,
    "response.content_part.added": OpenResponsesContentPartAddedEvent,
    "response.content_part.done": OpenResponsesContentPartDoneEvent,
    "response.reasoning_content.delta": OpenResponsesReasoningContentDeltaEvent,
    "response.reasoning_summary.delta": OpenResponsesReasoningSummaryDeltaEvent,
    "response.function_call_arguments.delta": OpenResponsesFunctionCallArgumentsDeltaEvent,
    "response.completed": OpenResponsesResponseCompletedEvent,
    "response.failed": OpenResponsesResponseFailedEvent,
}


class OpenResponsesParser:
    """
    Stateful parser for Open Responses SSE stream.
    Handles events split across multiple lines.
    """

    def __init__(self) -> None:
        self._current_event: Optional[str] = None
        self._current_data: list[str] = []

    def feed(self, line: str) -> Optional[OpenResponsesEvent]:
        """
        Feed a single line from the stream.
        Returns an event if a full SSE block is completed.
        Optimized for maximum streaming performance.
        """
        # Fast strip and empty check
        line = line.strip()
        if not line:
            # Empty line signals end of event block
            if self._current_event and self._current_data:
                # Fast string joining for performance
                full_data = "".join(self._current_data)

                if full_data == "[DONE]":
                    event = OpenResponsesDoneEvent()
                else:
                    try:
                        # Fast JSON parsing
                        raw_data = json.loads(full_data)
                        sequence_number = raw_data.get("sequence_number", 0)
                        # Fast dictionary lookup
                        event_class = EVENT_TYPE_TO_CLASS.get(
                            self._current_event, OpenResponsesEvent
                        )
                        event = event_class(
                            event_type=self._current_event,
                            sequence_number=sequence_number,
                            raw_data=raw_data,
                        )
                    except json.JSONDecodeError:
                        event = None

                self._current_event = None
                self._current_data = []
                return event
            return None

        if line.startswith("event: "):
            self._current_event = line[7:].strip()
        elif line.startswith("data: "):
            self._current_data.append(line[6:].strip())

        return None


def parse_open_responses_event(line: str) -> Optional[OpenResponsesEvent]:
    """
    Legacy parser for single-block strings.
    For real streams, use OpenResponsesParser.
    """
    return OpenResponsesEvent.from_sse_line(line)


__all__ = [
    "OpenResponsesEvent",
    "OpenResponsesDoneEvent",
    "OpenResponsesResponseCreatedEvent",
    "OpenResponsesResponseInProgressEvent",
    "OpenResponsesOutputItemAddedEvent",
    "OpenResponsesOutputTextDeltaEvent",
    "OpenResponsesOutputTextDoneEvent",
    "OpenResponsesContentPartAddedEvent",
    "OpenResponsesContentPartDoneEvent",
    "OpenResponsesReasoningContentDeltaEvent",
    "OpenResponsesReasoningSummaryDeltaEvent",
    "OpenResponsesFunctionCallArgumentsDeltaEvent",
    "OpenResponsesResponseCompletedEvent",
    "OpenResponsesResponseFailedEvent",
    "OpenResponsesParser",
    "parse_open_responses_event",
    "EVENT_TYPE_TO_CLASS",
]
