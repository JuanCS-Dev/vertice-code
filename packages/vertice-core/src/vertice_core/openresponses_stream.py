"""
Open Responses Streaming Protocol for Vertice.

Este módulo implementa o protocolo de streaming com eventos semânticos.
Cada evento segue o formato SSE (Server-Sent Events).

Referência: Open Responses Specification - Streaming
"""

from __future__ import annotations
import json
from typing import Optional, Generator
from dataclasses import dataclass, field

from .openresponses_types import (
    ItemStatus,
    MessageItem,
    ReasoningItem,
    OpenResponse,
    TokenUsage,
    OpenResponsesError,
)


# =============================================================================
# BASE EVENT
# =============================================================================


@dataclass
class StreamEvent:
    """
    Evento base de streaming.

    Todos os eventos têm:
    - type: Tipo do evento (usado no campo 'event' do SSE)
    - sequence_number: Número sequencial para ordenação
    """

    type: str = ""  # Default empty, set by subclasses in __post_init__
    sequence_number: int = 0

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        raise NotImplementedError

    def to_sse(self) -> str:
        """
        Converte para formato Server-Sent Events.

        Formato:
        event: <type>
        data: <json>

        """
        data = json.dumps(self.to_dict(), ensure_ascii=False)
        return f"event: {self.type}\ndata: {data}\n\n"


# =============================================================================
# STATE MACHINE EVENTS - Mudanças de estado do Response
# =============================================================================


@dataclass
class ResponseCreatedEvent(StreamEvent):
    """
    Evento: response.created

    Emitido quando Response é criado.
    """

    response: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.created"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "response": self.response,
        }


@dataclass
class ResponseInProgressEvent(StreamEvent):
    """
    Evento: response.in_progress

    Emitido quando Response começa processamento.
    """

    response: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.in_progress"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "response": self.response,
        }


@dataclass
class ResponseCompletedEvent(StreamEvent):
    """
    Evento: response.completed

    Emitido quando Response finaliza com sucesso.
    """

    response: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.completed"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "response": self.response,
        }


@dataclass
class ResponseFailedEvent(StreamEvent):
    """
    Evento: response.failed

    Emitido quando Response falha.
    """

    response: dict = field(default_factory=dict)
    error: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.failed"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "response": self.response,
            "error": self.error,
        }


# =============================================================================
# DELTA EVENTS - Mudanças incrementais
# =============================================================================


@dataclass
class OutputItemAddedEvent(StreamEvent):
    """
    Evento: response.output_item.added

    Emitido quando novo item é adicionado ao output.
    """

    output_index: int = 0
    item: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.output_item.added"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "output_index": self.output_index,
            "item": self.item,
        }


@dataclass
class ContentPartAddedEvent(StreamEvent):
    """
    Evento: response.content_part.added

    Emitido quando content part é adicionado a um item.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    part: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.content_part.added"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "part": self.part,
        }


@dataclass
class OutputTextDeltaEvent(StreamEvent):
    """
    Evento: response.output_text.delta

    Emitido para cada chunk de texto gerado.
    Este é o evento mais frequente durante streaming.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    delta: str = ""

    def __post_init__(self):
        self.type = "response.output_text.delta"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "delta": self.delta,
        }


@dataclass
class OutputTextDoneEvent(StreamEvent):
    """
    Evento: response.output_text.done

    Emitido quando texto está completo.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    text: str = ""

    def __post_init__(self):
        self.type = "response.output_text.done"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "text": self.text,
        }


@dataclass
class ContentPartDoneEvent(StreamEvent):
    """
    Evento: response.content_part.done

    Emitido quando content part está completo.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    part: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.content_part.done"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "part": self.part,
        }


@dataclass
class OutputItemDoneEvent(StreamEvent):
    """
    Evento: response.output_item.done

    Emitido quando item está completo.
    """

    output_index: int = 0
    item: dict = field(default_factory=dict)

    def __post_init__(self):
        self.type = "response.output_item.done"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "output_index": self.output_index,
            "item": self.item,
        }


@dataclass
class FunctionCallArgumentsDeltaEvent(StreamEvent):
    """
    Evento: response.function_call_arguments.delta

    Emitido durante streaming de argumentos de function call.
    """

    item_id: str = ""
    output_index: int = 0
    delta: str = ""

    def __post_init__(self):
        self.type = "response.function_call_arguments.delta"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "delta": self.delta,
        }


@dataclass
class ReasoningContentDeltaEvent(StreamEvent):
    """
    Evento: response.reasoning_content.delta

    Emitido durante streaming de conteúdo de raciocínio.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    delta: str = ""

    def __post_init__(self):
        self.type = "response.reasoning_content.delta"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "delta": self.delta,
        }


@dataclass
class ReasoningSummaryDeltaEvent(StreamEvent):
    """
    Evento: response.reasoning_summary.delta

    Emitido durante streaming de resumo de raciocínio.
    """

    item_id: str = ""
    output_index: int = 0
    delta: str = ""

    def __post_init__(self):
        self.type = "response.reasoning_summary.delta"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "delta": self.delta,
        }


@dataclass
class ReasoningContentDoneEvent(StreamEvent):
    """
    Evento: response.reasoning_content.done

    Emitido quando conteúdo de raciocínio está completo.
    """

    item_id: str = ""
    output_index: int = 0
    content_index: int = 0
    text: str = ""

    def __post_init__(self):
        self.type = "response.reasoning_content.done"

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "sequence_number": self.sequence_number,
            "item_id": self.item_id,
            "output_index": self.output_index,
            "content_index": self.content_index,
            "text": self.text,
        }


# =============================================================================
# STREAM BUILDER - API Fluente para gerar streams
# =============================================================================


class OpenResponsesStreamBuilder:
    """
    Builder para criar streams Open Responses.

    Uso:
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        builder.start()
        msg = builder.add_message()

        for chunk in text_chunks:
            builder.text_delta(msg, chunk)
            yield builder.get_last_event_sse()

        builder.complete()
        yield from builder.get_pending_events_sse()
        yield builder.done()
    """

    def __init__(self, model: str):
        self.response = OpenResponse(model=model, status=ItemStatus.IN_PROGRESS)
        self._sequence = 0
        self._events: list[StreamEvent] = []

    def _next_seq(self) -> int:
        """Incrementa e retorna próximo sequence number."""
        self._sequence += 1
        return self._sequence

    def start(self) -> "OpenResponsesStreamBuilder":
        """
        Emite eventos iniciais (created + in_progress).

        DEVE ser chamado primeiro.
        """
        self._events.append(
            ResponseCreatedEvent(sequence_number=self._next_seq(), response=self.response.to_dict())
        )
        self._events.append(
            ResponseInProgressEvent(
                sequence_number=self._next_seq(),
                response={"id": self.response.id, "status": "in_progress"},
            )
        )
        return self

    def add_message(self) -> MessageItem:
        """
        Adiciona MessageItem e emite output_item.added.

        Retorna o item para uso posterior.
        """
        item = self.response.add_message()
        output_index = len(self.response.output) - 1

        self._events.append(
            OutputItemAddedEvent(
                sequence_number=self._next_seq(), output_index=output_index, item=item.to_dict()
            )
        )

        # Adiciona content_part.added para o texto
        self._events.append(
            ContentPartAddedEvent(
                sequence_number=self._next_seq(),
                item_id=item.id,
                output_index=output_index,
                content_index=0,
                part={"type": "output_text", "annotations": [], "text": ""},
            )
        )

        return item

    def text_delta(self, item: MessageItem, delta: str) -> "OpenResponsesStreamBuilder":
        """
        Emite delta de texto para um item.

        Args:
            item: MessageItem alvo
            delta: Chunk de texto a adicionar
        """
        item.append_text(delta)
        output_index = self.response.output.index(item)

        self._events.append(
            OutputTextDeltaEvent(
                sequence_number=self._next_seq(),
                item_id=item.id,
                output_index=output_index,
                content_index=0,
                delta=delta,
            )
        )
        return self

    def add_reasoning(self) -> ReasoningItem:
        """
        Adiciona ReasoningItem e emite output_item.added.

        Retorna o item para uso posterior.
        """
        item = ReasoningItem(status=ItemStatus.IN_PROGRESS)
        self.response.output.append(item)
        output_index = len(self.response.output) - 1

        self._events.append(
            OutputItemAddedEvent(
                sequence_number=self._next_seq(), output_index=output_index, item=item.to_dict()
            )
        )

        return item

    def reasoning_delta(self, item: ReasoningItem, delta: str) -> "OpenResponsesStreamBuilder":
        """
        Emite delta de raciocínio para um item.
        """
        item.append_content(delta)
        output_index = self.response.output.index(item)

        self._events.append(
            ReasoningContentDeltaEvent(
                sequence_number=self._next_seq(),
                item_id=item.id,
                output_index=output_index,
                content_index=0,
                delta=delta,
            )
        )
        return self

    def complete(self, usage: Optional[TokenUsage] = None) -> "OpenResponsesStreamBuilder":
        """
        Finaliza response com sucesso.

        Emite eventos de finalização para todos os items.
        """
        # Finaliza cada item
        for idx, item in enumerate(self.response.output):
            if isinstance(item, MessageItem):
                # output_text.done
                self._events.append(
                    OutputTextDoneEvent(
                        sequence_number=self._next_seq(),
                        item_id=item.id,
                        output_index=idx,
                        content_index=0,
                        text=item.get_text(),
                    )
                )
                # content_part.done
                if item.content:
                    self._events.append(
                        ContentPartDoneEvent(
                            sequence_number=self._next_seq(),
                            item_id=item.id,
                            output_index=idx,
                            content_index=0,
                            part=item.content[0].to_dict(),
                        )
                    )

            # output_item.done
            item.status = ItemStatus.COMPLETED
            self._events.append(
                OutputItemDoneEvent(
                    sequence_number=self._next_seq(), output_index=idx, item=item.to_dict()
                )
            )

        # Finaliza response
        self.response.complete(usage)
        self._events.append(
            ResponseCompletedEvent(
                sequence_number=self._next_seq(), response=self.response.to_dict()
            )
        )

        return self

    def fail(self, error: OpenResponsesError) -> "OpenResponsesStreamBuilder":
        """
        Finaliza response com erro.
        """
        self.response.fail(error)
        self._events.append(
            ResponseFailedEvent(
                sequence_number=self._next_seq(),
                response=self.response.to_dict(),
                error=error.to_dict(),
            )
        )
        return self

    def get_events(self) -> list[StreamEvent]:
        """Retorna todos os eventos pendentes."""
        return self._events

    def get_last_event(self) -> Optional[StreamEvent]:
        """Retorna último evento."""
        return self._events[-1] if self._events else None

    def get_last_event_sse(self) -> str:
        """Retorna último evento em formato SSE."""
        event = self.get_last_event()
        return event.to_sse() if event else ""

    def get_pending_events_sse(self) -> Generator[str, None, None]:
        """Gera todos os eventos pendentes em SSE."""
        for event in self._events:
            yield event.to_sse()

    def clear_events(self) -> None:
        """Limpa lista de eventos."""
        self._events.clear()

    @staticmethod
    def done() -> str:
        """
        Retorna evento terminal [DONE].

        DEVE ser o último item do stream.
        """
        return "data: [DONE]\n\n"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base
    "StreamEvent",
    # State Machine Events
    "ResponseCreatedEvent",
    "ResponseInProgressEvent",
    "ResponseCompletedEvent",
    "ResponseFailedEvent",
    # Delta Events
    "OutputItemAddedEvent",
    "ContentPartAddedEvent",
    "OutputTextDeltaEvent",
    "OutputTextDoneEvent",
    "ContentPartDoneEvent",
    "OutputItemDoneEvent",
    "FunctionCallArgumentsDeltaEvent",
    # Reasoning Events
    "ReasoningContentDeltaEvent",
    "ReasoningSummaryDeltaEvent",
    "ReasoningContentDoneEvent",
    # Builder
    "OpenResponsesStreamBuilder",
]
