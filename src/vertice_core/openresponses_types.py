"""
Open Responses Type Definitions for Vertice.

Este módulo implementa os tipos core da especificação Open Responses.
Todos os types seguem o padrão de discriminated unions via campo 'type'.

Referência: Open Responses Specification (Janeiro 2026)
"""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Union, Literal, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    pass
from dataclasses import dataclass, field
import uuid


# =============================================================================
# ENUMS - Estados e Tipos
# =============================================================================


class ItemStatus(str, Enum):
    """
    Status do ciclo de vida de um Item.

    Spec: "Items are state machines"
    - in_progress: Model está gerando este item
    - completed: Item finalizado (TERMINAL)
    - incomplete: Token budget esgotado (TERMINAL)
    - failed: Erro durante processamento (TERMINAL)
    """

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class ItemType(str, Enum):
    """
    Discriminador para Item union.

    Spec: "Items are polymorphic"
    """

    MESSAGE = "message"
    FUNCTION_CALL = "function_call"
    FUNCTION_CALL_OUTPUT = "function_call_output"
    REASONING = "reasoning"


class MessageRole(str, Enum):
    """
    Roles de mensagem.

    Spec: "Content - User Content vs Model Content"
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    DEVELOPER = "developer"  # Novo role para instruções técnicas


class FinishReason(str, Enum):
    """Razões de finalização de response."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"


class ErrorType(str, Enum):
    """
    Tipos de erro.

    Spec: "Errors - Error Types"
    """

    SERVER_ERROR = "server_error"
    MODEL_ERROR = "model_error"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    TOO_MANY_REQUESTS = "too_many_requests"


# =============================================================================
# TEXT FORMAT - Controle de formato de saída
# =============================================================================


class TextFormatType(str, Enum):
    """Tipos de formato de texto."""

    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


@dataclass
class TextResponseFormat:
    """
    Formato de resposta padrão (texto livre).
    """

    type: Literal["text"] = "text"

    def to_dict(self) -> dict:
        return {"type": self.type}


@dataclass
class JsonObjectResponseFormat:
    """
    Formato de resposta JSON object.

    O modelo retornará JSON válido, mas sem schema específico.
    """

    type: Literal["json_object"] = "json_object"

    def to_dict(self) -> dict:
        return {"type": self.type}


@dataclass
class JsonSchemaResponseFormat:
    """
    Formato de resposta JSON com schema definido.

    Spec: "Structured Output permite forçar JSON válido"

    Exemplo:
    {
        "type": "json_schema",
        "json_schema": {
            "name": "user_info",
            "strict": true,
            "schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
    """

    type: Literal["json_schema"] = "json_schema"
    name: str = ""
    description: Optional[str] = None
    schema: Dict[str, Any] = field(default_factory=dict)
    strict: bool = True

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "json_schema": {
                "name": self.name,
                "strict": self.strict,
                "schema": self.schema,
            },
        }
        if self.description:
            result["json_schema"]["description"] = self.description
        return result

    @classmethod
    def from_pydantic_model(cls, model_class, name: str = None) -> "JsonSchemaResponseFormat":
        """
        Cria JsonSchemaResponseFormat a partir de model Pydantic.

        Args:
            model_class: Classe Pydantic (BaseModel subclass)
            name: Nome opcional (usa nome da classe se não fornecido)

        Returns:
            JsonSchemaResponseFormat configurado
        """
        schema = model_class.model_json_schema()
        return cls(
            name=name or model_class.__name__.lower(),
            description=model_class.__doc__,
            schema=schema,
            strict=True,
        )


# Type alias para TextFormat union
TextFormat = TextResponseFormat | JsonObjectResponseFormat | JsonSchemaResponseFormat


# =============================================================================
# EXTENSÕES VERTICE - Tipos customizados com prefixo vertice:
# =============================================================================


@dataclass
class VerticeTelemetryItem:
    """
    Item de telemetria (extensão Vertice).

    Spec: "New item types MUST be prefixed with implementor slug"

    Exemplo:
    {
        "type": "vertice:telemetry",
        "id": "vt_123",
        "status": "completed",
        "latency_ms": 142,
        "cache_hit": false,
        "model": "gemini-3-pro-preview",
        "provider": "vertex-ai"
    }
    """

    type: Literal["vertice:telemetry"] = "vertice:telemetry"
    id: str = field(default_factory=lambda: _generate_id("vt"))
    status: ItemStatus = ItemStatus.COMPLETED
    latency_ms: int = 0
    cache_hit: bool = False
    model: str = ""
    provider: str = ""
    tokens_input: int = 0
    tokens_output: int = 0

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit,
            "model": self.model,
            "provider": self.provider,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
        }


@dataclass
class VerticeGovernanceItem:
    """
    Item de governança (extensão Vertice).

    Resultado de verificação de segurança/compliance.
    """

    type: Literal["vertice:governance"] = "vertice:governance"
    id: str = field(default_factory=lambda: _generate_id("vg"))
    status: ItemStatus = ItemStatus.COMPLETED
    allowed: bool = True
    reason: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    checked_at: Optional[str] = None  # ISO timestamp

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "id": self.id,
            "status": self.status.value,
            "allowed": self.allowed,
        }
        if self.reason:
            result["reason"] = self.reason
        if self.violations:
            result["violations"] = self.violations
        if self.checked_at:
            result["checked_at"] = self.checked_at
        return result


# =============================================================================
# TEXT FORMAT - Controle de formato de saída
# =============================================================================


@dataclass
class OutputTextContent:
    """
    Conteúdo de texto gerado pelo model.

    Spec: "Model content is intentionally narrower"
    """

    type: Literal["output_text"] = "output_text"
    text: str = ""
    annotations: List[Annotation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "annotations": [a.to_dict() for a in self.annotations] if self.annotations else [],
        }

    def add_citation(
        self, url: str, title: Optional[str] = None, start: int = 0, end: Optional[int] = None
    ) -> None:
        """Adiciona uma citação de URL."""
        self.annotations.append(
            UrlCitation(
                url=url,
                title=title,
                start_index=start,
                end_index=end or len(self.text),
            )
        )


@dataclass
class InputTextContent:
    """
    Conteúdo de texto do usuário.

    Spec: "User content captures what the model is being asked to process"
    """

    type: Literal["input_text"] = "input_text"
    text: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type, "text": self.text}


# =============================================================================
# ITEM TYPES - Unidades atômicas de contexto
# =============================================================================


def _generate_id(prefix: str) -> str:
    """Gera ID único com prefixo."""
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


@dataclass
class MessageItem:
    """
    Item de mensagem.

    Spec: "Items are polymorphic" + "Items are state machines"

    Exemplo:
    {
        "type": "message",
        "id": "msg_01A2B3C4D5E6F7G8H9I0J1K2L3",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": "Hello!"}]
    }
    """

    type: Literal["message"] = "message"
    id: str = field(default_factory=lambda: _generate_id("msg"))
    role: MessageRole = MessageRole.ASSISTANT
    status: ItemStatus = ItemStatus.IN_PROGRESS
    content: List[OutputTextContent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "role": self.role.value if isinstance(self.role, Enum) else self.role,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "content": [c.to_dict() for c in self.content],
        }

    def get_text(self) -> str:
        """Retorna todo o texto concatenado."""
        return "".join(c.text for c in self.content if hasattr(c, "text"))

    def append_text(self, delta: str) -> None:
        """Adiciona texto ao content."""
        if not self.content:
            self.content.append(OutputTextContent())
        self.content[-1].text += delta

    def add_citation(
        self,
        url: str,
        title: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> None:
        """Adiciona uma citação ao último content."""
        # Adicionar ao último content ou criar novo se não existir
        if not self.content:
            self.content.append(OutputTextContent())

        # Delegar para o método add_citation do OutputTextContent
        self.content[-1].add_citation(url, title, start_index or 0, end_index)

    @property
    def annotations(self) -> List[Annotation]:
        """Retorna todas as annotations do último content."""
        if not self.content:
            return []
        return self.content[-1].annotations


@dataclass
class FunctionCallItem:
    """
    Item de function call.

    Spec: "Tools - Externally-hosted tools"

    Exemplo:
    {
        "type": "function_call",
        "id": "fc_00123xyzabc9876def0gh1ij2klmno345",
        "call_id": "call_987zyx654wvu321",
        "name": "get_weather",
        "arguments": "{\"location\":\"San Francisco\"}",
        "status": "completed"
    }
    """

    type: Literal["function_call"] = "function_call"
    id: str = field(default_factory=lambda: _generate_id("fc"))
    call_id: str = field(default_factory=lambda: _generate_id("call"))
    name: str = ""
    arguments: str = ""  # JSON string
    status: ItemStatus = ItemStatus.IN_PROGRESS

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": self.arguments,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
        }


@dataclass
class SummaryTextContent:
    """
    Resumo do raciocínio seguro para mostrar ao usuário.

    Spec: "Summaries are designed to be safe to show to end users"
    """

    type: Literal["summary_text"] = "summary_text"
    text: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type, "text": self.text}


@dataclass
class UrlCitation:
    """
    Anotação de citação de URL.

    Spec: Annotations são metadados sobre o texto gerado.

    Exemplo:
    {
        "type": "url_citation",
        "url": "https://example.com/article",
        "title": "Article Title",
        "start_index": 0,
        "end_index": 50
    }
    """

    type: Literal["url_citation"] = "url_citation"
    url: str = ""
    title: Optional[str] = None
    start_index: int = 0
    end_index: int = 0

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "url": self.url,
            "start_index": self.start_index,
            "end_index": self.end_index,
        }
        if self.title:
            result["title"] = self.title
        return result


@dataclass
class FileCitation:
    """
    Anotação de citação de arquivo.

    Usado quando o modelo cita conteúdo de um arquivo fornecido.
    """

    type: Literal["file_citation"] = "file_citation"
    file_id: str = ""
    filename: Optional[str] = None
    quote: Optional[str] = None
    start_index: int = 0
    end_index: int = 0

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "file_id": self.file_id,
            "start_index": self.start_index,
            "end_index": self.end_index,
        }
        if self.filename:
            result["filename"] = self.filename
        if self.quote:
            result["quote"] = self.quote
        return result


# Type alias para Annotation union
Annotation = UrlCitation | FileCitation


@dataclass
class FunctionCallOutputItem:
    """
    Item de output de function call.

    Spec: "Developer envia resultado de volta"

    Exemplo:
    {
        "type": "function_call_output",
        "call_id": "call_987zyx654wvu321",
        "output": "{\"temperature\":14,\"condition\":\"cloudy\"}"
    }
    """

    type: Literal["function_call_output"] = "function_call_output"
    id: str = field(default_factory=lambda: _generate_id("fco"))
    call_id: str = ""  # Correlaciona com FunctionCallItem.call_id
    output: str = ""
    status: ItemStatus = ItemStatus.COMPLETED

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "call_id": self.call_id,
            "output": self.output,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
        }


@dataclass
class ReasoningItem:
    """
    Item de raciocínio (chain-of-thought).

    Spec: "Reasoning items expose the model's internal thought process"

    Campos:
    - content: Raciocínio raw (pode ser null/truncado por segurança)
    - summary: Resumo seguro para usuários
    - encrypted_content: Dados opacos para round-trip (provider-specific)

    Exemplo:
    {
        "type": "reasoning",
        "id": "rs_01A2B3C4D5E6F7G8H9I0J1K2L3",
        "status": "completed",
        "summary": [{"type": "summary_text", "text": "Analisei..."}],
        "content": [{"type": "output_text", "text": "Steps..."}],
        "encrypted_content": null
    }
    """

    type: Literal["reasoning"] = "reasoning"
    id: str = field(default_factory=lambda: _generate_id("rs"))
    status: ItemStatus = ItemStatus.IN_PROGRESS
    content: List[OutputTextContent] = field(default_factory=list)
    summary: List[SummaryTextContent] = field(default_factory=list)
    encrypted_content: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "id": self.id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "content": [c.to_dict() for c in self.content] if self.content else [],
            "summary": [s.to_dict() for s in self.summary] if self.summary else [],
        }
        if self.encrypted_content:
            result["encrypted_content"] = self.encrypted_content
        return result

    def get_reasoning_text(self) -> str:
        """Retorna todo o texto de raciocínio concatenado."""
        return "".join(c.text for c in self.content if isinstance(c, OutputTextContent))

    def get_summary_text(self) -> str:
        """Retorna todo o texto do resumo concatenado."""
        return "".join(s.text for s in self.summary)

    def append_content(self, text: str) -> None:
        """Adiciona texto ao content."""
        if self.content:
            self.content[0].text += text
        else:
            self.content.append(OutputTextContent(text=text))

    def set_summary(self, text: str) -> None:
        """Define o summary."""
        self.summary = [SummaryTextContent(text=text)]


# Union type para todos os items
Item = Union[MessageItem, FunctionCallItem, FunctionCallOutputItem, ReasoningItem]


# =============================================================================
# ERROR TYPE
# =============================================================================


@dataclass
class OpenResponsesError:
    """
    Estrutura de erro.

    Spec: "Errors"

    Exemplo:
    {
        "type": "invalid_request_error",
        "code": "model_not_found",
        "param": "model",
        "message": "The requested model does not exist."
    }
    """

    type: ErrorType = ErrorType.SERVER_ERROR
    code: str = "server_error"
    message: str = ""
    param: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "code": self.code,
            "message": self.message,
        }
        if self.param:
            result["param"] = self.param
        return result


# =============================================================================
# USAGE TYPE
# =============================================================================


@dataclass
class TokenUsage:
    """Estatísticas de uso de tokens."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


# =============================================================================
# RESPONSE TYPE - Container principal
# =============================================================================


@dataclass
class OpenResponse:
    """
    Response object principal.

    Spec: "Response is a state machine"

    Exemplo:
    {
        "id": "resp_abc123",
        "status": "completed",
        "model": "gemini-3-pro-preview",
        "output": [...items...],
        "usage": {...}
    }
    """

    id: str = field(default_factory=lambda: _generate_id("resp"))
    status: ItemStatus = ItemStatus.IN_PROGRESS
    model: str = ""
    output: List[Item] = field(default_factory=list)
    usage: Optional[TokenUsage] = None
    error: Optional[OpenResponsesError] = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "model": self.model,
            "output": [item.to_dict() for item in self.output],
        }
        if self.usage:
            result["usage"] = self.usage.to_dict()
        if self.error:
            result["error"] = self.error.to_dict()
        return result

    def add_message(self, role: MessageRole = MessageRole.ASSISTANT) -> MessageItem:
        """Adiciona novo MessageItem ao output."""
        item = MessageItem(role=role)
        self.output.append(item)
        return item

    def add_function_call(self, name: str, arguments: str = "") -> FunctionCallItem:
        """Adiciona novo FunctionCallItem ao output."""
        item = FunctionCallItem(name=name, arguments=arguments)
        self.output.append(item)
        return item

    def complete(self, usage: Optional[TokenUsage] = None) -> None:
        """Marca response como completo."""
        self.status = ItemStatus.COMPLETED
        for item in self.output:
            if hasattr(item, "status") and item.status == ItemStatus.IN_PROGRESS:
                item.status = ItemStatus.COMPLETED
        if usage:
            self.usage = usage

    def fail(self, error: OpenResponsesError) -> None:
        """Marca response como falho."""
        self.status = ItemStatus.FAILED
        self.error = error


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ItemStatus",
    "ItemType",
    "MessageRole",
    "FinishReason",
    "ErrorType",
    # Content
    "OutputTextContent",
    "InputTextContent",
    "SummaryTextContent",
    # Items
    "MessageItem",
    "FunctionCallItem",
    "FunctionCallOutputItem",
    "ReasoningItem",
    "Item",
    # Annotations
    "UrlCitation",
    "FileCitation",
    "Annotation",
    # Text Format
    "TextFormatType",
    "TextResponseFormat",
    "JsonObjectResponseFormat",
    "JsonSchemaResponseFormat",
    "TextFormat",
    # Error
    "OpenResponsesError",
    # Usage
    "TokenUsage",
    # Response
    "OpenResponse",
    # Extensions
    "VerticeTelemetryItem",
    "VerticeGovernanceItem",
]
