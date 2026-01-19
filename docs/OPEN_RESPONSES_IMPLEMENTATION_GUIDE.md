# 📚 OPEN RESPONSES - GUIA COMPLETO DE IMPLEMENTAÇÃO PARA VÉRTICE

**Versão**: 1.0
**Data**: 16 de Janeiro de 2026
**Autor**: Antigravity AI Assistant
**Para**: Desenvolvedor Sênior (Implementador Offline)

---

> **NOTA IMPORTANTE**: Este documento é **100% autocontido**. Toda a documentação, schemas,
> exemplos e especificações necessárias estão incluídos aqui. Você NÃO precisa de acesso à
> internet para implementar. Apenas leia, entenda e codifique.

---

## SUMÁRIO

1. [O Que é Open Responses](#1-o-que-é-open-responses)
2. [Conceitos Fundamentais](#2-conceitos-fundamentais)
3. [Especificação Completa de Items](#3-especificação-completa-de-items)
4. [Especificação Completa de Streaming](#4-especificação-completa-de-streaming)
5. [Especificação Completa de Tools](#5-especificação-completa-de-tools)
6. [Especificação Completa de Errors](#6-especificação-completa-de-errors)
7. [Mapeamento Vértice → Open Responses](#7-mapeamento-vértice--open-responses)
8. [Implementação Fase 1: Core Types](#8-implementação-fase-1-core-types)
9. [Implementação Fase 2: Streaming](#9-implementação-fase-2-streaming)
10. [Implementação Fase 3: Tools](#10-implementação-fase-3-tools)
11. [Implementação Fase 4: Providers](#11-implementação-fase-4-providers)
12. [Implementação Fase 5: Agents](#12-implementação-fase-5-agents)
13. [Testes e Verificação](#13-testes-e-verificação)

---

# 1. O QUE É OPEN RESPONSES

Open Responses é uma **especificação aberta** para APIs de LLM que define:

- **Schema unificado** para requests e responses
- **Protocolo de streaming** com eventos semânticos
- **Sistema de tools** para function calling
- **Agentic loop** para workflows multi-step

### Por que adotar?

| Problema no Vértice | Solução Open Responses |
|---------------------|------------------------|
| Cada provider tem formato diferente | Schema único para todos |
| Tool schemas quebram no Vertex AI | Formato padronizado que funciona |
| Streaming inconsistente (CLI vs WebApp) | Eventos semânticos unificados |
| Sem estado em respostas | State machine (in_progress → completed) |

---

# 2. CONCEITOS FUNDAMENTAIS

## 2.1 Items - A Unidade Básica

**Item** é a unidade atômica de contexto. Pode ser:

| Type | Descrição | Uso |
|------|-----------|-----|
| `message` | Mensagem de chat | User ou Assistant |
| `function_call` | Invocação de tool | Model chama function |
| `function_call_output` | Resultado de tool | Developer retorna resultado |
| `reasoning` | Pensamento do model | Chain of thought |

## 2.2 Items são Polimórficos

Items têm shapes diferentes baseado no campo `type`:

```json
// Message Item
{
    "type": "message",
    "id": "msg_01A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6",
    "role": "assistant",
    "status": "completed",
    "content": [
        {
            "type": "output_text",
            "text": "Hello! How can I assist you today?"
        }
    ]
}
```

```json
// Function Call Item
{
    "type": "function_call",
    "id": "fc_00123xyzabc9876def0gh1ij2klmno345",
    "name": "sendEmail",
    "call_id": "call_987zyx654wvu321",
    "arguments": "{\"recipient\":\"jane.doe@example.com\",\"subject\":\"Meeting Reminder\"}"
}
```

## 2.3 Items são State Machines

Todo item tem um **status** que segue este ciclo de vida:

```
┌─────────────────┐
│   in_progress   │  ← Model está gerando este item
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│    completed    │  ou │   incomplete    │  ← Token budget esgotado
└─────────────────┘     └─────────────────┘
```

**Estados:**
- `in_progress`: Model está emitindo tokens para este item
- `completed`: Item finalizado com sucesso. Estado TERMINAL.
- `incomplete`: Token budget esgotado antes de terminar. Estado TERMINAL.
- `failed`: Erro durante processamento. Estado TERMINAL.

## 2.4 Items são Streamable

Enquanto item muda de estado, eventos são emitidos:

```
1. response.output_item.added     → Item criado
2. response.content_part.added    → Content part criado
3. response.output_text.delta     → Texto sendo gerado (repetido N vezes)
4. response.output_text.done      → Texto completo
5. response.content_part.done     → Content part finalizado
6. response.output_item.done      → Item finalizado
```

## 2.5 Items são Extensíveis

Providers podem criar seus próprios types com prefixo:

```json
{
    "id": "ws_0df093a2d268",
    "type": "openai:web_search_call",
    "status": "completed",
    "action": {
        "type": "search",
        "query": "weather: San Francisco, CA"
    }
}
```

Para Vértice, usaremos prefixo `vertice:`:
- `vertice:mcp_tool_call`
- `vertice:code_execution`

---

# 3. ESPECIFICAÇÃO COMPLETA DE ITEMS

## 3.1 Message Item (Input)

### UserMessageItemParam
```json
{
    "type": "message",
    "role": "user",
    "content": [
        {
            "type": "input_text",
            "text": "What is the weather in San Francisco?"
        }
    ]
}
```

### SystemMessageItemParam
```json
{
    "type": "message",
    "role": "system",
    "content": [
        {
            "type": "input_text",
            "text": "You are a helpful assistant."
        }
    ]
}
```

## 3.2 Message Item (Output)

### AssistantMessageItem
```json
{
    "type": "message",
    "id": "msg_07315d23576898080068e95daa2e34819685fb0a98a0503f78",
    "role": "assistant",
    "status": "completed",
    "content": [
        {
            "type": "output_text",
            "text": "The weather in San Francisco is currently 58°F and cloudy.",
            "annotations": []
        }
    ]
}
```

**Campos Obrigatórios:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | `"message"` | Discriminador |
| `id` | `string` | ID único (prefixo `msg_`) |
| `role` | `"assistant"` | Role do message |
| `status` | `enum` | `in_progress`, `completed`, `incomplete`, `failed` |
| `content` | `array` | Lista de content parts |

## 3.3 Function Call Item

Quando model decide chamar uma tool:

```json
{
    "type": "function_call",
    "id": "fc_00123xyzabc9876def0gh1ij2klmno345",
    "call_id": "call_987zyx654wvu321",
    "name": "get_weather",
    "arguments": "{\"location\":\"San Francisco\",\"unit\":\"celsius\"}",
    "status": "completed"
}
```

## 3.4 Function Call Output Item

Developer envia resultado de volta:

```json
{
    "type": "function_call_output",
    "call_id": "call_987zyx654wvu321",
    "output": "{\"temperature\":14,\"condition\":\"cloudy\",\"humidity\":72}"
}
```

---

# 4. ESPECIFICAÇÃO COMPLETA DE STREAMING

## 4.1 Protocolo HTTP

### Headers de Response (Streaming)
```http
Content-Type: text/event-stream
```

### Formato SSE (Server-Sent Events)
```
event: response.output_text.delta
data: {"type":"response.output_text.delta","sequence_number":10,"item_id":"msg_07315d23","output_index":0,"content_index":0,"delta":" a"}

data: [DONE]
```

## 4.2 Eventos de State Machine

### response.created
```json
{
    "type": "response.created",
    "sequence_number": 1,
    "response": {
        "id": "resp_abc123",
        "status": "in_progress",
        "model": "gemini-3-pro-preview",
        "output": []
    }
}
```

### response.completed
```json
{
    "type": "response.completed",
    "sequence_number": 50,
    "response": {
        "id": "resp_abc123",
        "status": "completed",
        "usage": {
            "input_tokens": 150,
            "output_tokens": 89,
            "total_tokens": 239
        }
    }
}
```

## 4.3 Eventos Delta

### response.output_item.added
```json
{
    "type": "response.output_item.added",
    "sequence_number": 3,
    "output_index": 0,
    "item": {
        "id": "msg_07315d23",
        "type": "message",
        "status": "in_progress",
        "content": [],
        "role": "assistant"
    }
}
```

### response.output_text.delta
```json
{
    "type": "response.output_text.delta",
    "sequence_number": 5,
    "item_id": "msg_07315d23",
    "output_index": 0,
    "content_index": 0,
    "delta": "Hello"
}
```

---

# 5. ESPECIFICAÇÃO COMPLETA DE TOOLS

## 5.1 FunctionToolParam (Definição de Tool)

```json
{
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state, e.g., San Francisco, CA"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
            }
        },
        "required": ["location"]
    }
}
```

**IMPORTANTE**: `required` DEVE ser array no nível TOP do parameters, NÃO dentro de cada property!

## 5.2 tool_choice

| Valor | Comportamento |
|-------|---------------|
| `"auto"` | Model decide se chama tool ou responde direto |
| `"required"` | Model DEVE chamar pelo menos uma tool |
| `"none"` | Model NÃO pode chamar tools |

---

# 6. ESPECIFICAÇÃO COMPLETA DE ERRORS

## 6.1 Estrutura de Erro

```json
{
    "error": {
        "type": "invalid_request_error",
        "code": "model_not_found",
        "param": "model",
        "message": "The requested model 'fake-model' does not exist."
    }
}
```

## 6.2 Error Types

| Type | HTTP Status |
|------|-------------|
| `server_error` | 500 |
| `model_error` | 500 |
| `invalid_request` | 400 |
| `not_found` | 404 |
| `too_many_requests` | 429 |

---

# 7. MAPEAMENTO VÉRTICE → OPEN RESPONSES

## 7.1 Arquivos a Modificar/Criar

| Arquivo | Ação |
|---------|------|
| `src/vertice_core/openresponses_types.py` | CRIAR |
| `src/vertice_core/openresponses_stream.py` | CRIAR |
| `src/vertice_cli/tools/base.py` | MODIFICAR |
| `src/vertice_cli/core/providers/vertex_ai.py` | MODIFICAR |
| `src/vertice_cli/core/providers/vertice_router.py` | MODIFICAR |

---

*Continua na Parte 2 com código completo de implementação...*


---

# 8. IMPLEMENTAÇÃO FASE 1: CORE TYPES

## 8.1 Criar arquivo: `src/vertice_core/openresponses_types.py`

```python
"""
Open Responses Type Definitions for Vertice.

Este módulo implementa os tipos core da especificação Open Responses.
Todos os types seguem o padrão de discriminated unions via campo 'type'.

Referência: Open Responses Specification (Janeiro 2026)
"""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Union, Literal, Any
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
# CONTENT TYPES - Partes de conteúdo dentro de Items
# =============================================================================

@dataclass
class OutputTextContent:
    """
    Conteúdo de texto gerado pelo model.

    Spec: "Model content is intentionally narrower"
    """
    type: Literal["output_text"] = "output_text"
    text: str = ""
    annotations: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "annotations": self.annotations
        }


@dataclass
class InputTextContent:
    """
    Conteúdo de texto do usuário.

    Spec: "User content captures what the model is being asked to process"
    """
    type: Literal["input_text"] = "input_text"
    text: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "text": self.text
        }


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
            "content": [c.to_dict() for c in self.content]
        }

    def get_text(self) -> str:
        """Retorna todo o texto concatenado."""
        return "".join(c.text for c in self.content if hasattr(c, 'text'))

    def append_text(self, delta: str) -> None:
        """Adiciona texto ao content."""
        if not self.content:
            self.content.append(OutputTextContent())
        self.content[-1].text += delta


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
            "status": self.status.value if isinstance(self.status, Enum) else self.status
        }

    def get_arguments_dict(self) -> dict:
        """Parse arguments JSON."""
        import json
        try:
            return json.loads(self.arguments) if self.arguments else {}
        except json.JSONDecodeError:
            return {}


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
            "status": self.status.value if isinstance(self.status, Enum) else self.status
        }


@dataclass
class ReasoningItem:
    """
    Item de reasoning (chain-of-thought).

    Spec: "Reasoning - Reasoning items expose the model's internal thought process"
    """
    type: Literal["reasoning"] = "reasoning"
    id: str = field(default_factory=lambda: _generate_id("rs"))
    status: ItemStatus = ItemStatus.IN_PROGRESS
    summary: List[dict] = field(default_factory=list)
    content: List[OutputTextContent] = field(default_factory=list)
    encrypted_content: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "summary": self.summary,
            "content": [c.to_dict() for c in self.content],
            "encrypted_content": self.encrypted_content
        }


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
            "message": self.message
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
            "total_tokens": self.total_tokens
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
            "output": [item.to_dict() for item in self.output]
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
            if hasattr(item, 'status') and item.status == ItemStatus.IN_PROGRESS:
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
    # Items
    "MessageItem",
    "FunctionCallItem",
    "FunctionCallOutputItem",
    "ReasoningItem",
    "Item",
    # Error
    "OpenResponsesError",
    # Usage
    "TokenUsage",
    # Response
    "OpenResponse",
]
```



---

# 9. IMPLEMENTAÇÃO FASE 2: STREAMING

## 9.1 Criar arquivo: `src/vertice_core/openresponses_stream.py`

```python
"""
Open Responses Streaming Protocol for Vertice.

Este módulo implementa o protocolo de streaming com eventos semânticos.
Cada evento segue o formato SSE (Server-Sent Events).

Referência: Open Responses Specification - Streaming
"""

from __future__ import annotations
import json
from typing import Optional, Generator, Any
from dataclasses import dataclass, field

from .openresponses_types import (
    ItemStatus,
    MessageItem,
    FunctionCallItem,
    OpenResponse,
    TokenUsage,
    OpenResponsesError
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
    type: str
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
            "response": self.response
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
            "response": self.response
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
            "response": self.response
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
            "error": self.error
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
            "item": self.item
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
            "part": self.part
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
            "delta": self.delta
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
            "text": self.text
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
            "part": self.part
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
            "item": self.item
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
            "delta": self.delta
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
        self._events.append(ResponseCreatedEvent(
            sequence_number=self._next_seq(),
            response=self.response.to_dict()
        ))
        self._events.append(ResponseInProgressEvent(
            sequence_number=self._next_seq(),
            response={"id": self.response.id, "status": "in_progress"}
        ))
        return self

    def add_message(self) -> MessageItem:
        """
        Adiciona MessageItem e emite output_item.added.

        Retorna o item para uso posterior.
        """
        item = self.response.add_message()
        output_index = len(self.response.output) - 1

        self._events.append(OutputItemAddedEvent(
            sequence_number=self._next_seq(),
            output_index=output_index,
            item=item.to_dict()
        ))

        # Adiciona content_part.added para o texto
        self._events.append(ContentPartAddedEvent(
            sequence_number=self._next_seq(),
            item_id=item.id,
            output_index=output_index,
            content_index=0,
            part={"type": "output_text", "annotations": [], "text": ""}
        ))

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

        self._events.append(OutputTextDeltaEvent(
            sequence_number=self._next_seq(),
            item_id=item.id,
            output_index=output_index,
            content_index=0,
            delta=delta
        ))
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
                self._events.append(OutputTextDoneEvent(
                    sequence_number=self._next_seq(),
                    item_id=item.id,
                    output_index=idx,
                    content_index=0,
                    text=item.get_text()
                ))
                # content_part.done
                if item.content:
                    self._events.append(ContentPartDoneEvent(
                        sequence_number=self._next_seq(),
                        item_id=item.id,
                        output_index=idx,
                        content_index=0,
                        part=item.content[0].to_dict()
                    ))

            # output_item.done
            item.status = ItemStatus.COMPLETED
            self._events.append(OutputItemDoneEvent(
                sequence_number=self._next_seq(),
                output_index=idx,
                item=item.to_dict()
            ))

        # Finaliza response
        self.response.complete(usage)
        self._events.append(ResponseCompletedEvent(
            sequence_number=self._next_seq(),
            response=self.response.to_dict()
        ))

        return self

    def fail(self, error: OpenResponsesError) -> "OpenResponsesStreamBuilder":
        """
        Finaliza response com erro.
        """
        self.response.fail(error)
        self._events.append(ResponseFailedEvent(
            sequence_number=self._next_seq(),
            response=self.response.to_dict(),
            error=error.to_dict()
        ))
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
    # Builder
    "OpenResponsesStreamBuilder",
]
```



---

# 10. IMPLEMENTAÇÃO FASE 3: TOOLS

## 10.1 Modificar arquivo: `src/vertice_cli/tools/base.py`

Localizar o método `get_schema` e substituir por:

```python
def get_schema(self) -> Dict[str, Any]:
    """
    Get tool schema for LLM tool use.

    IMPORTANTE: Segue formato Open Responses FunctionToolParam.
    - 'required' DEVE estar no nível TOP do parameters, não dentro de properties
    """
    # Remove 'required' de dentro de cada property
    clean_properties = {}
    for k, v in self.parameters.items():
        prop_copy = {key: val for key, val in v.items() if key != 'required'}
        clean_properties[k] = prop_copy

    return {
        "name": self.name,
        "description": self.description,
        "parameters": {
            "type": "object",
            "properties": clean_properties,
            "required": [
                k for k, v in self.parameters.items()
                if v.get('required', False)
            ]
        }
    }

def to_function_tool_param(self) -> Dict[str, Any]:
    """
    Get Open Responses FunctionToolParam format.

    Retorna:
    {
        "type": "function",
        "name": "tool_name",
        "description": "...",
        "parameters": {...}
    }
    """
    schema = self.get_schema()
    return {
        "type": "function",
        "name": schema["name"],
        "description": schema["description"],
        "parameters": schema["parameters"]
    }
```

### Exemplo de Tool Correta

```python
class WriteFileTool(BaseTool):
    """Ferramenta para escrever arquivos."""

    name = "write_file"
    description = "Write content to a file at the specified path."
    parameters = {
        "path": {
            "type": "string",
            "description": "The file path to write to",
            "required": True  # Será movido para required[] no schema
        },
        "content": {
            "type": "string",
            "description": "The content to write",
            "required": True
        },
        "mode": {
            "type": "string",
            "enum": ["write", "append"],
            "description": "Write mode",
            "required": False  # Opcional
        }
    }

    async def execute(self, path: str, content: str, mode: str = "write") -> ToolResult:
        ...
```

### Schema Gerado (Correto para Open Responses)

```json
{
    "type": "function",
    "name": "write_file",
    "description": "Write content to a file at the specified path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to write to"
            },
            "content": {
                "type": "string",
                "description": "The content to write"
            },
            "mode": {
                "type": "string",
                "enum": ["write", "append"],
                "description": "Write mode"
            }
        },
        "required": ["path", "content"]
    }
}
```

---

# 11. IMPLEMENTAÇÃO FASE 4: PROVIDERS

## 11.1 Modificar arquivo: `src/vertice_cli/core/providers/vertex_ai.py`

Adicionar imports no topo:

```python
from vertice_core.openresponses_types import (
    OpenResponse,
    MessageItem,
    ItemStatus,
    TokenUsage,
    OpenResponsesError,
    ErrorType
)
from vertice_core.openresponses_stream import OpenResponsesStreamBuilder
```

Adicionar método na classe `VertexAIProvider`:

```python
async def stream_open_responses(
    self,
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 0.7,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Stream usando protocolo Open Responses.

    Emite eventos SSE seguindo a especificação Open Responses.

    Yields:
        str: Eventos SSE formatados

    Exemplo de uso:
        async for event in provider.stream_open_responses(messages):
            print(event)  # event: response.output_text.delta\ndata: {...}\n\n
    """
    # Cria builder com nome do modelo
    builder = OpenResponsesStreamBuilder(model=self.model_id)

    try:
        # Emite eventos iniciais
        builder.start()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Cria MessageItem
        message_item = builder.add_message()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Stream do conteúdo
        token_count = 0
        async for chunk in self.stream_chat(
            messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            token_count += len(chunk.split())  # Estimativa simples
            builder.text_delta(message_item, chunk)
            yield builder.get_last_event_sse()
            builder.clear_events()

        # Finaliza com sucesso
        usage = TokenUsage(
            input_tokens=sum(len(m.get("content", "")) // 4 for m in messages),
            output_tokens=token_count,
            total_tokens=0  # Será calculado
        )
        usage.total_tokens = usage.input_tokens + usage.output_tokens

        builder.complete(usage)
        for event in builder.get_events():
            yield event.to_sse()

        # Evento terminal
        yield builder.done()

    except Exception as e:
        # Emite erro
        error = OpenResponsesError(
            type=ErrorType.MODEL_ERROR,
            code="generation_failed",
            message=str(e)
        )
        builder.fail(error)
        for event in builder.get_events():
            yield event.to_sse()
        yield builder.done()
```

## 11.2 Modificar arquivo: `src/vertice_cli/core/providers/vertice_router.py`

Adicionar imports no topo:

```python
from vertice_core.openresponses_stream import OpenResponsesStreamBuilder
from vertice_core.openresponses_types import ItemStatus, TokenUsage, OpenResponsesError, ErrorType
```

Adicionar método na classe `VerticeRouter`:

```python
async def stream_open_responses(
    self,
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    complexity: TaskComplexity = TaskComplexity.MODERATE,
    speed: SpeedRequirement = SpeedRequirement.NORMAL,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Stream usando Open Responses com routing automático.

    Rota para o provider apropriado e converte output para
    formato Open Responses se necessário.
    """
    decision = self.route(complexity=complexity, speed=speed)
    provider = self._providers[decision.provider_name]
    status = self._status[decision.provider_name]

    # Verifica se provider suporta Open Responses nativamente
    if hasattr(provider, 'stream_open_responses'):
        try:
            async for event in provider.stream_open_responses(
                messages, system_prompt=system_prompt, **kwargs
            ):
                yield event
            status.record_request()
            return
        except Exception as e:
            status.record_error(str(e))
            # Continua para fallback

    # Fallback: Wrap legacy stream em Open Responses
    builder = OpenResponsesStreamBuilder(model=decision.model_name)

    try:
        # Eventos iniciais
        builder.start()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Message item
        message_item = builder.add_message()
        for event in builder.get_events():
            yield event.to_sse()
        builder.clear_events()

        # Stream legacy
        async for chunk in provider.stream_chat(
            messages, system_prompt=system_prompt, **kwargs
        ):
            builder.text_delta(message_item, chunk)
            yield builder.get_last_event_sse()
            builder.clear_events()

        # Finaliza
        builder.complete()
        for event in builder.get_events():
            yield event.to_sse()
        yield builder.done()

        status.record_request()

    except Exception as e:
        status.record_error(str(e))
        error = OpenResponsesError(
            type=ErrorType.SERVER_ERROR,
            code="provider_failed",
            message=f"{decision.provider_name}: {str(e)}"
        )
        builder.fail(error)
        for event in builder.get_events():
            yield event.to_sse()
        yield builder.done()
```

---

# 12. IMPLEMENTAÇÃO FASE 5: AGENTS

## 12.1 Modificar arquivo: `src/vertice_cli/agents/base.py`

Adicionar imports no topo:

```python
from vertice_core.openresponses_types import (
    OpenResponse,
    MessageItem,
    ItemStatus,
    MessageRole,
    OutputTextContent,
    OpenResponsesError,
    ErrorType
)
```

Adicionar método na classe `BaseAgent`:

```python
async def execute_open_responses(
    self,
    task: AgentTask,
    previous_response_id: Optional[str] = None
) -> OpenResponse:
    """
    Executa task retornando formato Open Responses.

    Args:
        task: Task a executar
        previous_response_id: ID do response anterior para continuação

    Returns:
        OpenResponse com resultado da execução
    """
    response = OpenResponse(model=self._get_model_name())

    try:
        # Execução padrão
        agent_response = await self.execute(task)

        # Converte para Open Responses
        message_item = MessageItem(
            role=MessageRole.ASSISTANT,
            status=ItemStatus.COMPLETED,
            content=[OutputTextContent(text=agent_response.content)]
        )
        response.output.append(message_item)
        response.status = ItemStatus.COMPLETED

        self.logger.info(f"Open Responses execution completed: {response.id}")

    except CapabilityViolationError as e:
        response.status = ItemStatus.FAILED
        response.error = OpenResponsesError(
            type=ErrorType.INVALID_REQUEST,
            code="capability_violation",
            message=str(e)
        )
        self.logger.error(f"Capability violation: {e}")

    except Exception as e:
        response.status = ItemStatus.FAILED
        response.error = OpenResponsesError(
            type=ErrorType.SERVER_ERROR,
            code="execution_failed",
            message=str(e)
        )
        self.logger.error(f"Execution failed: {e}", exc_info=True)

    return response

def _get_model_name(self) -> str:
    """Obtém nome do modelo do LLM client."""
    if hasattr(self.llm_client, 'get_model_info'):
        info = self.llm_client.get_model_info()
        return info.get('model', 'unknown')
    if hasattr(self.llm_client, 'model_id'):
        return self.llm_client.model_id
    return 'unknown'
```



---

# 13. TESTES E VERIFICAÇÃO

## 13.1 Teste Unitário dos Types

Criar arquivo: `tests/unit/test_openresponses_types.py`

```python
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
    ErrorType
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

    def test_get_arguments_dict(self):
        item = FunctionCallItem(arguments='{"location":"SF","unit":"celsius"}')
        args = item.get_arguments_dict()
        assert args == {"location": "SF", "unit": "celsius"}

    def test_get_arguments_dict_invalid(self):
        item = FunctionCallItem(arguments='not json')
        assert item.get_arguments_dict() == {}


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
        assert isinstance(msg, MessageItem)

    def test_add_function_call(self):
        resp = OpenResponse()
        fc = resp.add_function_call("my_tool", '{"arg": 1}')
        assert len(resp.output) == 1
        assert isinstance(fc, FunctionCallItem)
        assert fc.name == "my_tool"

    def test_complete(self):
        resp = OpenResponse()
        msg = resp.add_message()
        usage = TokenUsage(input_tokens=10, output_tokens=20, total_tokens=30)
        resp.complete(usage)

        assert resp.status == ItemStatus.COMPLETED
        assert msg.status == ItemStatus.COMPLETED
        assert resp.usage == usage

    def test_fail(self):
        resp = OpenResponse()
        error = OpenResponsesError(
            type=ErrorType.MODEL_ERROR,
            code="test_error",
            message="Test failed"
        )
        resp.fail(error)

        assert resp.status == ItemStatus.FAILED
        assert resp.error == error

    def test_to_dict(self):
        resp = OpenResponse(model="test-model")
        msg = resp.add_message()
        msg.append_text("Hello")
        resp.complete()

        d = resp.to_dict()
        assert d["id"].startswith("resp_")
        assert d["status"] == "completed"
        assert d["model"] == "test-model"
        assert len(d["output"]) == 1
        assert d["output"][0]["type"] == "message"
```

## 13.2 Teste de Streaming

Criar arquivo: `tests/unit/test_openresponses_stream.py`

```python
"""Testes para Open Responses Streaming."""
import pytest
import json
from vertice_core.openresponses_stream import (
    OpenResponsesStreamBuilder,
    ResponseCreatedEvent,
    OutputTextDeltaEvent
)
from vertice_core.openresponses_types import TokenUsage


class TestStreamBuilder:
    """Testes para OpenResponsesStreamBuilder."""

    def test_creation(self):
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")
        assert builder.response.model == "gemini-3-pro"
        assert builder._sequence == 0

    def test_start(self):
        builder = OpenResponsesStreamBuilder(model="test")
        builder.start()

        events = builder.get_events()
        assert len(events) == 2
        assert events[0].type == "response.created"
        assert events[1].type == "response.in_progress"

    def test_add_message(self):
        builder = OpenResponsesStreamBuilder(model="test")
        builder.start()
        builder.clear_events()

        msg = builder.add_message()

        events = builder.get_events()
        assert len(events) == 2  # output_item.added + content_part.added
        assert events[0].type == "response.output_item.added"
        assert events[1].type == "response.content_part.added"

    def test_text_delta(self):
        builder = OpenResponsesStreamBuilder(model="test")
        builder.start()
        msg = builder.add_message()
        builder.clear_events()

        builder.text_delta(msg, "Hello")

        events = builder.get_events()
        assert len(events) == 1
        assert events[0].type == "response.output_text.delta"
        assert events[0].delta == "Hello"

    def test_complete(self):
        builder = OpenResponsesStreamBuilder(model="test")
        builder.start()
        msg = builder.add_message()
        builder.text_delta(msg, "Hello World")
        builder.clear_events()

        usage = TokenUsage(input_tokens=5, output_tokens=10, total_tokens=15)
        builder.complete(usage)

        events = builder.get_events()
        # output_text.done, content_part.done, output_item.done, response.completed
        assert events[-1].type == "response.completed"

    def test_done(self):
        done = OpenResponsesStreamBuilder.done()
        assert done == "data: [DONE]\n\n"

    def test_sse_format(self):
        event = OutputTextDeltaEvent(
            sequence_number=5,
            item_id="msg_123",
            output_index=0,
            content_index=0,
            delta="Test"
        )

        sse = event.to_sse()
        assert "event: response.output_text.delta" in sse
        assert "data:" in sse

        # Parse data
        lines = sse.strip().split("\n")
        data_line = [l for l in lines if l.startswith("data:")][0]
        data = json.loads(data_line[5:].strip())

        assert data["type"] == "response.output_text.delta"
        assert data["sequence_number"] == 5
        assert data["delta"] == "Test"


class TestFullStream:
    """Teste de stream completo."""

    def test_full_stream_sequence(self):
        builder = OpenResponsesStreamBuilder(model="gemini-3-pro")

        # Coleta todos os eventos SSE
        all_sse = []

        builder.start()
        all_sse.extend([e.to_sse() for e in builder.get_events()])
        builder.clear_events()

        msg = builder.add_message()
        all_sse.extend([e.to_sse() for e in builder.get_events()])
        builder.clear_events()

        for chunk in ["Hello", " ", "World", "!"]:
            builder.text_delta(msg, chunk)
            all_sse.append(builder.get_last_event_sse())
            builder.clear_events()

        builder.complete()
        all_sse.extend([e.to_sse() for e in builder.get_events()])
        all_sse.append(builder.done())

        # Verifica sequência
        assert "response.created" in all_sse[0]
        assert "response.in_progress" in all_sse[1]
        assert "output_item.added" in all_sse[2]
        assert "[DONE]" in all_sse[-1]

        # Verifica que msg tem texto completo
        assert msg.get_text() == "Hello World!"
```

## 13.3 Teste E2E

Criar arquivo: `tests/e2e/test_open_responses_flow.py`

```python
"""Teste E2E do fluxo Open Responses."""
import pytest
import asyncio
from vertice_core.openresponses_types import OpenResponse, ItemStatus
from vertice_core.openresponses_stream import OpenResponsesStreamBuilder


@pytest.mark.asyncio
async def test_provider_stream_open_responses():
    """Testa streaming via provider."""
    # Importa apenas se disponível
    try:
        from vertice_cli.core.providers.vertex_ai import VertexAIProvider
    except ImportError:
        pytest.skip("VertexAIProvider not available")

    provider = VertexAIProvider(model_name="flash")

    if not provider.is_available():
        pytest.skip("Vertex AI not configured")

    messages = [{"role": "user", "content": "Say hello in one word."}]

    events = []
    async for event in provider.stream_open_responses(messages):
        events.append(event)

    # Verifica eventos básicos
    assert any("response.created" in e for e in events)
    assert any("response.output_text.delta" in e for e in events)
    assert any("response.completed" in e for e in events)
    assert events[-1] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_router_stream_open_responses():
    """Testa streaming via router."""
    try:
        from vertice_cli.core.providers.vertice_router import VerticeRouter
    except ImportError:
        pytest.skip("VerticeRouter not available")

    router = VerticeRouter()

    available = router.get_available_providers()
    if not available:
        pytest.skip("No providers available")

    messages = [{"role": "user", "content": "Count to 3."}]

    events = []
    async for event in router.stream_open_responses(messages):
        events.append(event)

    assert len(events) > 0
    assert "[DONE]" in events[-1]
```

## 13.4 Comandos de Execução

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio

# Rodar testes unitários
pytest tests/unit/test_openresponses_types.py -v
pytest tests/unit/test_openresponses_stream.py -v

# Rodar teste E2E (requer providers configurados)
pytest tests/e2e/test_open_responses_flow.py -v

# Rodar todos os testes
pytest tests/ -v --tb=short

# Verificar cobertura
pytest tests/ --cov=vertice_core --cov-report=html
```

---

# APÊNDICE A: REQUEST/RESPONSE COMPLETO

## Request Exemplo

```json
{
    "model": "gemini-3-pro-preview",
    "input": [
        {
            "type": "message",
            "role": "system",
            "content": [
                {"type": "input_text", "text": "You are a helpful assistant."}
            ]
        },
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "What is the weather in San Francisco?"}
            ]
        }
    ],
    "tools": [
        {
            "type": "function",
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state"
                    }
                },
                "required": ["location"]
            }
        }
    ],
    "tool_choice": "auto",
    "stream": true
}
```

## Response Exemplo (Final)

```json
{
    "id": "resp_07315d23576898080068efe9b45d748191a5239d49c2971a65",
    "status": "completed",
    "model": "gemini-3-pro-preview",
    "output": [
        {
            "type": "function_call",
            "id": "fc_00123xyzabc9876def0gh1ij2klmno345",
            "call_id": "call_987zyx654wvu321",
            "name": "get_weather",
            "arguments": "{\"location\":\"San Francisco, CA\"}",
            "status": "completed"
        }
    ],
    "usage": {
        "input_tokens": 85,
        "output_tokens": 23,
        "total_tokens": 108
    }
}
```

---

# APÊNDICE B: CHECKLIST DE IMPLEMENTAÇÃO

## Fase 1: Core Types
- [ ] Criar `src/vertice_core/openresponses_types.py`
- [ ] Implementar ItemStatus, ItemType, MessageRole enums
- [ ] Implementar MessageItem, FunctionCallItem, FunctionCallOutputItem
- [ ] Implementar OpenResponse
- [ ] Implementar OpenResponsesError
- [ ] Escrever testes unitários

## Fase 2: Streaming
- [ ] Criar `src/vertice_core/openresponses_stream.py`
- [ ] Implementar todos os StreamEvent types
- [ ] Implementar OpenResponsesStreamBuilder
- [ ] Escrever testes de streaming

## Fase 3: Tools
- [ ] Modificar `BaseTool.get_schema()` para formato correto
- [ ] Adicionar `BaseTool.to_function_tool_param()`
- [ ] Verificar todas as tools existentes

## Fase 4: Providers
- [ ] Adicionar `stream_open_responses` em VertexAIProvider
- [ ] Adicionar `stream_open_responses` em VerticeRouter
- [ ] Testar com diferentes providers

## Fase 5: Agents
- [ ] Adicionar `execute_open_responses` em BaseAgent
- [ ] Testar integração completa

## Verificação Final
- [ ] Rodar todos os testes
- [ ] Verificar cobertura > 80%
- [ ] Testar E2E com WebApp
- [ ] Testar E2E com TUI

---

**FIM DO DOCUMENTO**

Autor: Antigravity AI Assistant
Data: 16 de Janeiro de 2026
Versão: 1.0


---

# 14. ADENDOS - GAPS IDENTIFICADOS NA VALIDAÇÃO

## 14.1 Fase 6: Protocol Updates

### Modificar arquivo: `src/vertice_core/protocols.py`

Adicionar após `LLMClientWithChatProtocol` (linha ~92):

```python
@runtime_checkable
class LLMClientWithOpenResponsesProtocol(LLMClientWithChatProtocol, Protocol):
    """Extended protocol with Open Responses streaming support."""

    async def stream_open_responses(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream using Open Responses protocol.

        Yields SSE-formatted events:
        - event: response.created
        - event: response.output_text.delta
        - event: response.completed
        - data: [DONE]
        """
        ...
```

Adicionar após `StreamingAgentProtocol` (linha ~188):

```python
@runtime_checkable
class OpenResponsesAgentProtocol(AgentProtocol, Protocol):
    """Protocol for agents supporting Open Responses format."""

    async def execute_open_responses(
        self,
        task: AgentTask,
        previous_response_id: Optional[str] = None,
    ) -> Any:  # Returns OpenResponse
        """
        Execute task returning Open Responses format.

        Args:
            task: Task to execute
            previous_response_id: ID of previous response for context resumption

        Returns:
            OpenResponse object
        """
        ...
```

---

## 14.2 Integração WebApp chat.py

### Modificar arquivo: `vertice-chat-webapp/backend/app/api/v1/chat.py`

Adicionar imports no topo:

```python
import uuid
from app.core.config import settings
```

Adicionar após `stream_vertex_response` function (~linha 250):

```python
async def stream_vertex_response_open_responses(
    request: ChatRequest,
    session_id: Optional[str] = None
):
    """
    Stream Vertex AI response using Open Responses protocol.

    Alternative to Vercel AI SDK protocol for Open Responses compatibility.

    Events emitted:
    - response.created
    - response.in_progress
    - response.output_item.added
    - response.output_text.delta (repeated)
    - response.output_text.done
    - response.output_item.done
    - response.completed
    - [DONE]
    """
    from app.core.stream_protocol import (
        format_response_created,
        format_response_in_progress,
        format_output_item_added,
        format_output_text_delta,
        format_output_text_done,
        format_output_item_done,
        format_response_completed,
    )

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "global")

    # Initialize
    vertexai.init(project=project_id, location=location)
    model_name = request.model or DEFAULT_MODEL

    # Generate IDs
    response_id = f"resp_{uuid.uuid4().hex[:24]}"
    message_id = f"msg_{uuid.uuid4().hex[:24]}"
    sequence = 0

    def next_seq():
        nonlocal sequence
        sequence += 1
        return sequence

    try:
        model = GenerativeModel(model_name)
        history = convert_messages_to_vertex(request.messages[:-1])
        user_message = request.messages[-1].get("content", "")

        # Emit initial events
        yield format_response_created(response_id, model_name, next_seq())
        yield format_response_in_progress(response_id, next_seq())
        yield format_output_item_added(message_id, "assistant", 0, next_seq())

        # Stream content
        chat = model.start_chat(history=history)
        response = await chat.send_message_async(
            user_message,
            stream=True,
        )

        full_text = ""
        async for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield format_output_text_delta(message_id, chunk.text, 0, 0, next_seq())

        # Finalize
        yield format_output_text_done(message_id, full_text, 0, 0, next_seq())
        yield format_output_item_done(message_id, "message", "assistant", full_text, 0, next_seq())

        usage = {
            "input_tokens": sum(len(m.get("content", "")) // 4 for m in request.messages),
            "output_tokens": len(full_text) // 4,
        }
        yield format_response_completed(response_id, usage, next_seq())
        yield "data: [DONE]\n\n"

    except Exception as e:
        from app.core.stream_protocol import format_response_failed
        yield format_response_failed(response_id, str(e), next_seq())
        yield "data: [DONE]\n\n"
```

Modificar `chat_endpoint` para usar feature flag:

```python
@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    # ... authentication code ...

    # Choose stream protocol based on feature flag
    if settings.USE_OPEN_RESPONSES:
        stream_generator = stream_vertex_response_open_responses(request, session_id)
        content_type = "text/event-stream"
        headers = {
            "Content-Type": content_type,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Vertice-Protocol": "open-responses",
        }
    else:
        stream_generator = stream_vertex_response(request, session_id)
        content_type = "text/plain; charset=utf-8"
        headers = {
            "X-Vercel-AI-Data-Stream": "v1",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
        }

    return StreamingResponse(
        stream_generator,
        media_type=content_type,
        headers=headers,
    )
```

---

## 14.3 Feature Flag Implementation

### Criar/Modificar arquivo: `vertice-chat-webapp/backend/app/core/config.py`

```python
"""
Application configuration with feature flags.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vertice.db")

    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    VERTEX_AI_LOCATION: str = os.getenv("VERTEX_AI_LOCATION", "global")

    # Feature Flags
    USE_OPEN_RESPONSES: bool = os.getenv(
        "VERTICE_USE_OPEN_RESPONSES", "false"
    ).lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()
```

### Adicionar funções de formatting ao stream_protocol.py

```python
# Adicionar ao final de stream_protocol.py

def format_response_created(response_id: str, model: str, seq: int) -> str:
    """Format response.created event."""
    return format_open_responses_event("response.created", {
        "type": "response.created",
        "sequence_number": seq,
        "response": {
            "id": response_id,
            "status": "in_progress",
            "model": model,
            "output": []
        }
    })


def format_response_in_progress(response_id: str, seq: int) -> str:
    """Format response.in_progress event."""
    return format_open_responses_event("response.in_progress", {
        "type": "response.in_progress",
        "sequence_number": seq,
        "response": {"id": response_id, "status": "in_progress"}
    })


def format_output_item_added(item_id: str, role: str, output_index: int, seq: int) -> str:
    """Format response.output_item.added event."""
    return format_open_responses_event("response.output_item.added", {
        "type": "response.output_item.added",
        "sequence_number": seq,
        "output_index": output_index,
        "item": {
            "id": item_id,
            "type": "message",
            "role": role,
            "status": "in_progress",
            "content": []
        }
    })


def format_output_text_delta(item_id: str, delta: str, output_index: int, content_index: int, seq: int) -> str:
    """Format response.output_text.delta event."""
    return format_open_responses_event("response.output_text.delta", {
        "type": "response.output_text.delta",
        "sequence_number": seq,
        "item_id": item_id,
        "output_index": output_index,
        "content_index": content_index,
        "delta": delta
    })


def format_output_text_done(item_id: str, text: str, output_index: int, content_index: int, seq: int) -> str:
    """Format response.output_text.done event."""
    return format_open_responses_event("response.output_text.done", {
        "type": "response.output_text.done",
        "sequence_number": seq,
        "item_id": item_id,
        "output_index": output_index,
        "content_index": content_index,
        "text": text
    })


def format_output_item_done(item_id: str, item_type: str, role: str, text: str, output_index: int, seq: int) -> str:
    """Format response.output_item.done event."""
    return format_open_responses_event("response.output_item.done", {
        "type": "response.output_item.done",
        "sequence_number": seq,
        "output_index": output_index,
        "item": {
            "id": item_id,
            "type": item_type,
            "role": role,
            "status": "completed",
            "content": [{"type": "output_text", "text": text}]
        }
    })


def format_response_completed(response_id: str, usage: dict, seq: int) -> str:
    """Format response.completed event."""
    return format_open_responses_event("response.completed", {
        "type": "response.completed",
        "sequence_number": seq,
        "response": {
            "id": response_id,
            "status": "completed",
            "usage": usage
        }
    })


def format_response_failed(response_id: str, error_message: str, seq: int) -> str:
    """Format response.failed event."""
    return format_open_responses_event("response.failed", {
        "type": "response.failed",
        "sequence_number": seq,
        "response": {"id": response_id, "status": "failed"},
        "error": {
            "type": "server_error",
            "message": error_message
        }
    })


def format_open_responses_event(event_type: str, data: dict) -> str:
    """Format an Open Responses SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
```

---

## 14.4 Integração TUI

### Modificar arquivo: `src/vertice_tui/core/llm_client.py`

Adicionar método para consumir Open Responses stream:

```python
import json
from typing import AsyncIterator, Dict, Any
from dataclasses import dataclass


@dataclass
class OpenResponsesEvent:
    """Parsed Open Responses streaming event."""
    event_type: str
    sequence_number: int
    data: Dict[str, Any]

    @property
    def is_text_delta(self) -> bool:
        return self.event_type == "response.output_text.delta"

    @property
    def delta_text(self) -> str:
        if self.is_text_delta:
            return self.data.get("delta", "")
        return ""

    @property
    def is_done(self) -> bool:
        return self.event_type == "response.completed"


class LLMClient:
    # ... existing code ...

    async def stream_open_responses(
        self,
        messages: list,
        **kwargs
    ) -> AsyncIterator[OpenResponsesEvent]:
        """
        Stream with Open Responses protocol parsing.

        Parses SSE events and yields structured OpenResponsesEvent objects.

        Usage:
            async for event in client.stream_open_responses(messages):
                if event.is_text_delta:
                    print(event.delta_text, end="", flush=True)
                elif event.is_done:
                    print("\\nCompleted!")
        """
        current_event_type = None

        async for line in self._stream_raw_sse(messages, **kwargs):
            line = line.strip()

            if not line:
                continue

            if line.startswith("event:"):
                current_event_type = line[7:].strip()

            elif line.startswith("data:"):
                data_str = line[5:].strip()

                # Terminal event
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    yield OpenResponsesEvent(
                        event_type=current_event_type or data.get("type", "unknown"),
                        sequence_number=data.get("sequence_number", 0),
                        data=data
                    )
                except json.JSONDecodeError:
                    continue

    async def _stream_raw_sse(self, messages: list, **kwargs) -> AsyncIterator[str]:
        """
        Raw SSE line streaming. Override in subclasses.

        Should yield individual lines from the SSE stream.
        """
        # Implementation depends on the underlying HTTP client
        # Example with httpx:
        async with self.http_client.stream("POST", self.endpoint, json={
            "messages": messages,
            **kwargs
        }) as response:
            async for line in response.aiter_lines():
                yield line
```

### Modificar widget de resposta para suportar Open Responses

```python
# Em src/vertice_tui/widgets/response_view.py

from vertice_tui.core.llm_client import OpenResponsesEvent

class ResponseView:
    # ... existing code ...

    async def stream_response_open_responses(self, messages: list):
        """Stream response using Open Responses protocol."""
        self.clear()

        async for event in self.llm_client.stream_open_responses(messages):
            if event.is_text_delta:
                self.append_text(event.delta_text)
            elif event.event_type == "response.output_item.added":
                # New item starting
                pass
            elif event.is_done:
                # Show completion indicator
                self.set_status("completed")
```

---

## 14.5 Atualização de Testes E2E

### Modificar: `tests/e2e/test_chat_e2e_vertex.py`

```python
import pytest
import os


@pytest.fixture(params=["vercel_ai_sdk", "open_responses"])
def stream_protocol(request):
    """Fixture to test both streaming protocols."""
    protocol = request.param

    # Set environment variable for each test
    if protocol == "open_responses":
        os.environ["VERTICE_USE_OPEN_RESPONSES"] = "true"
    else:
        os.environ["VERTICE_USE_OPEN_RESPONSES"] = "false"

    yield protocol

    # Cleanup
    os.environ.pop("VERTICE_USE_OPEN_RESPONSES", None)


@pytest.mark.asyncio
async def test_chat_streaming(stream_protocol, async_client):
    """Test chat streaming with both protocols."""
    response = await async_client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Say hello"}], "stream": True}
    )

    assert response.status_code == 200

    content = await response.aread()

    if stream_protocol == "open_responses":
        # Verify Open Responses format
        assert b"event: response.created" in content
        assert b"event: response.output_text.delta" in content
        assert b"event: response.completed" in content
        assert b"[DONE]" in content
        assert response.headers.get("x-vertice-protocol") == "open-responses"
    else:
        # Verify Vercel AI SDK format
        assert b'0:"' in content  # Text chunk format
        assert b'd:{"finishReason"' in content
        assert response.headers.get("x-vercel-ai-data-stream") == "v1"


@pytest.mark.asyncio
async def test_open_responses_event_sequence():
    """Verify correct event sequence in Open Responses stream."""
    os.environ["VERTICE_USE_OPEN_RESPONSES"] = "true"

    # ... test code ...

    events = parse_sse_events(content)

    # Verify sequence
    event_types = [e["type"] for e in events]

    assert event_types[0] == "response.created"
    assert event_types[1] == "response.in_progress"
    assert "response.output_item.added" in event_types
    assert "response.output_text.delta" in event_types
    assert event_types[-1] == "response.completed"

    # Verify sequence numbers are monotonically increasing
    seq_numbers = [e["sequence_number"] for e in events]
    assert seq_numbers == sorted(seq_numbers)
    assert len(seq_numbers) == len(set(seq_numbers))  # No duplicates
```

---

## 📋 CHECKLIST COMPLETO FINAL

### Fase 1: Core Types
- [ ] Criar `src/vertice_core/openresponses_types.py`
- [ ] Verificar compatibilidade com types existentes

### Fase 2: Streaming
- [ ] Criar `src/vertice_core/openresponses_stream.py`
- [ ] Testar builder

### Fase 3: Tools
- [ ] Modificar `BaseTool.get_schema()`
- [ ] Testar com Vertex AI

### Fase 4: Providers CLI
- [ ] Adicionar `stream_open_responses` em `VertexAIProvider`
- [ ] Adicionar `stream_open_responses` em `VerticeRouter`

### Fase 5: Agents
- [ ] Adicionar `execute_open_responses` em `BaseAgent`

### Fase 6: Protocols (ADICIONADO)
- [ ] Atualizar `vertice_core/protocols.py`
- [ ] Adicionar `LLMClientWithOpenResponsesProtocol`
- [ ] Adicionar `OpenResponsesAgentProtocol`

### Fase 7: WebApp (ADICIONADO)
- [ ] Criar `config.py` com feature flag
- [ ] Adicionar funções Open Responses em `stream_protocol.py`
- [ ] Adicionar `stream_vertex_response_open_responses` em `chat.py`
- [ ] Modificar endpoint para usar feature flag

### Fase 8: TUI (ADICIONADO)
- [ ] Adicionar `OpenResponsesEvent` class
- [ ] Adicionar `stream_open_responses` method
- [ ] Atualizar `ResponseView` widget

### Fase 9: Testes (ADICIONADO)
- [ ] Adicionar fixture `stream_protocol`
- [ ] Testar ambos os protocolos
- [ ] Verificar sequence numbers
- [ ] Verificar event sequence

---

**GUIA ATUALIZADO COM GAPS IDENTIFICADOS**

Data: 16 de Janeiro de 2026
Versão: 1.1
