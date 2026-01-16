# 📚 OPEN RESPONSES - FASE 2: ENHANCEMENTS

**Versão**: 2.0  
**Data**: 16 de Janeiro de 2026  
**Autor**: Antigravity AI Assistant  
**Para**: Desenvolvedor Sênior (Implementador Offline)  
**Pré-requisito**: Fase 1 já implementada (Types, Streaming, Tools, Providers, Agents, Protocols, WebApp, TUI)

---

> **NOTA IMPORTANTE**: Este documento é **100% autocontido**. Toda a documentação,
> schemas, exemplos e especificações necessárias estão incluídos aqui. Você NÃO 
> precisa de acesso à internet para implementar.

---

## SUMÁRIO

1. [Visão Geral](#1-visão-geral)
2. [Reasoning Items](#2-reasoning-items)
3. [Input Multimodal](#3-input-multimodal)
4. [Annotations e Citations](#4-annotations-e-citations)
5. [Structured Output](#5-structured-output)
6. [Extensões Vertice](#6-extensões-vertice)
7. [Verificação](#7-verificação)

---

# 1. VISÃO GERAL

## 1.1 O que estamos adicionando

Esta fase adiciona features avançadas que complementam a implementação base:

| Feature | Descrição | Prioridade |
|---------|-----------|------------|
| **Reasoning Items** | Chain-of-thought com content/summary/encrypted | ALTA |
| **Input Multimodal** | Imagens e arquivos no input | MÉDIA |
| **Annotations** | Citações e links em texto gerado | MÉDIA |
| **Structured Output** | JSON Schema para respostas estruturadas | ALTA |
| **Extensões Vertice** | Tipos customizados com prefixo `vertice:` | BAIXA |

## 1.2 Arquivos a modificar/criar

```
src/vertice_core/
├── openresponses_types.py       # [MODIFY] Adicionar ReasoningItem, InputImage, etc.
├── openresponses_stream.py      # [MODIFY] Adicionar eventos de reasoning
└── openresponses_multimodal.py  # [NEW] Tipos multimodais

vertice-chat-webapp/backend/app/
└── core/stream_protocol.py      # [MODIFY] Eventos de reasoning
```

---

# 2. REASONING ITEMS

## 2.1 Especificação Oficial

Reasoning items expõem o processo de pensamento interno do modelo. Campos:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `type` | `"reasoning"` | Sim | Discriminador |
| `id` | `string` | Sim | ID único (prefixo `rs_`) |
| `status` | `ItemStatus` | Sim | Estado da máquina |
| `content` | `OutputTextContent[]` | Não | Raciocínio raw (pode ser truncado) |
| `summary` | `SummaryTextContent[]` | Não | Resumo seguro para usuários |
| `encrypted_content` | `string` | Não | Conteúdo criptografado (opaco) |

## 2.2 Exemplo JSON

```json
{
  "type": "reasoning",
  "id": "rs_01A2B3C4D5E6F7G8H9I0J1K2L3",
  "status": "completed",
  "summary": [
    {
      "type": "summary_text",
      "text": "Analisei o pedido do usuário, identifiquei que é uma pergunta sobre restaurantes, filtrei por localização e rating."
    }
  ],
  "content": [
    {
      "type": "output_text",
      "text": "User asked: \"Onde jantar em SP?\"\n\n1. Interpretei como busca de restaurantes\n2. Filtrei por região central\n3. Ordenei por rating > 4.5\n4. Selecionei 3 opções"
    }
  ],
  "encrypted_content": null
}
```

## 2.3 Implementação Python

Adicionar ao arquivo `src/vertice_core/openresponses_types.py`:

```python
# Após FunctionCallOutputItem (~linha 250)

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
            "status": self.status.value,
            "content": [c.to_dict() for c in self.content] if self.content else [],
            "summary": [s.to_dict() for s in self.summary] if self.summary else [],
        }
        if self.encrypted_content:
            result["encrypted_content"] = self.encrypted_content
        return result
    
    def get_reasoning_text(self) -> str:
        """Retorna todo o texto de raciocínio concatenado."""
        return "".join(c.text for c in self.content if hasattr(c, 'text'))
    
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
```

## 2.4 Streaming Events para Reasoning

Adicionar ao arquivo `src/vertice_core/openresponses_stream.py`:

```python
# Após FunctionCallArgumentsDeltaEvent (~linha 333)

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
```

## 2.5 Adicionar ao StreamBuilder

```python
# Em OpenResponsesStreamBuilder, adicionar método:

def add_reasoning(self) -> ReasoningItem:
    """
    Adiciona ReasoningItem e emite output_item.added.
    
    Retorna o item para uso posterior.
    """
    from .openresponses_types import ReasoningItem
    
    item = ReasoningItem(status=ItemStatus.IN_PROGRESS)
    self.response.output.append(item)
    output_index = len(self.response.output) - 1
    
    self._events.append(
        OutputItemAddedEvent(
            sequence_number=self._next_seq(),
            output_index=output_index,
            item=item.to_dict()
        )
    )
    
    return item


def reasoning_delta(self, item: "ReasoningItem", delta: str) -> "OpenResponsesStreamBuilder":
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
```

---

# 3. INPUT MULTIMODAL

## 3.1 Especificação Oficial

User Content pode incluir múltiplas modalidades:

| Tipo | Campo | Descrição |
|------|-------|-----------|
| `input_text` | `text` | Texto do usuário |
| `input_image` | `image_url` ou `image_base64` | Imagem |
| `input_file` | `file_data` | Arquivo binário |

## 3.2 Exemplo JSON

```json
{
  "type": "message",
  "role": "user",
  "content": [
    {
      "type": "input_text",
      "text": "O que há nesta imagem?"
    },
    {
      "type": "input_image",
      "image_url": "https://example.com/cat.jpg",
      "detail": "auto"
    }
  ]
}
```

## 3.3 Implementação Python

Criar arquivo `src/vertice_core/openresponses_multimodal.py`:

```python
"""
Open Responses Multimodal Types for Vertice.

Este módulo implementa tipos para input multimodal (imagens, arquivos).
"""

from __future__ import annotations
from typing import Literal, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum


class ImageDetail(str, Enum):
    """Nível de detalhe para processamento de imagem."""
    
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"


@dataclass
class InputImageContent:
    """
    Conteúdo de imagem no input do usuário.
    
    Spec: "User inputs can include multiple modalities (e.g. text, images)"
    
    Suporta dois modos:
    - image_url: URL pública da imagem
    - image_base64: Dados codificados em base64
    
    Exemplo:
    {
        "type": "input_image",
        "image_url": "https://example.com/image.png",
        "detail": "auto"
    }
    """
    
    type: Literal["input_image"] = "input_image"
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    media_type: Optional[str] = None  # e.g., "image/png"
    detail: ImageDetail = ImageDetail.AUTO
    
    def to_dict(self) -> dict:
        result = {"type": self.type, "detail": self.detail.value}
        if self.image_url:
            result["image_url"] = self.image_url
        if self.image_base64:
            result["image_base64"] = self.image_base64
            if self.media_type:
                result["media_type"] = self.media_type
        return result
    
    def to_vertex_part(self):
        """
        Converte para formato Vertex AI Part.
        
        Vertex AI usa um formato específico para imagens.
        """
        from vertexai.generative_models import Part
        import base64
        
        if self.image_url:
            # Para URLs, Vertex AI pode usar diretamente
            return Part.from_uri(self.image_url, mime_type=self.media_type or "image/jpeg")
        elif self.image_base64:
            # Para base64, decodificar e criar Part
            image_bytes = base64.b64decode(self.image_base64)
            return Part.from_data(image_bytes, mime_type=self.media_type or "image/jpeg")
        
        raise ValueError("InputImageContent must have image_url or image_base64")


@dataclass
class InputFileContent:
    """
    Conteúdo de arquivo no input do usuário.
    
    Spec: "User content must support multiple data types"
    
    Exemplo:
    {
        "type": "input_file",
        "file_data": "SGVsbG8gV29ybGQ=",
        "media_type": "application/pdf",
        "filename": "document.pdf"
    }
    """
    
    type: Literal["input_file"] = "input_file"
    file_data: str = ""  # Base64 encoded
    media_type: str = "application/octet-stream"
    filename: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "file_data": self.file_data,
            "media_type": self.media_type,
        }
        if self.filename:
            result["filename"] = self.filename
        return result


@dataclass
class InputVideoContent:
    """
    Conteúdo de vídeo no input do usuário.
    
    Suportado por modelos como Gemini 1.5/2.0/3.0.
    """
    
    type: Literal["input_video"] = "input_video"
    video_url: Optional[str] = None
    video_base64: Optional[str] = None
    media_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"type": self.type}
        if self.video_url:
            result["video_url"] = self.video_url
        if self.video_base64:
            result["video_base64"] = self.video_base64
            if self.media_type:
                result["media_type"] = self.media_type
        return result


# Type alias para User Content union
UserContent = InputTextContent | InputImageContent | InputFileContent | InputVideoContent


def convert_user_content_to_vertex(content: List[Any]) -> List:
    """
    Converte lista de UserContent para formato Vertex AI.
    
    Args:
        content: Lista de InputText, InputImage, etc.
        
    Returns:
        Lista de Vertex AI Parts
    """
    from vertexai.generative_models import Part
    
    parts = []
    for item in content:
        if hasattr(item, 'type'):
            if item.type == "input_text":
                parts.append(Part.from_text(item.text))
            elif item.type == "input_image":
                parts.append(item.to_vertex_part())
            elif item.type == "input_file":
                import base64
                data = base64.b64decode(item.file_data)
                parts.append(Part.from_data(data, mime_type=item.media_type))
        elif isinstance(item, str):
            parts.append(Part.from_text(item))
        elif isinstance(item, dict):
            if item.get("type") == "input_text":
                parts.append(Part.from_text(item.get("text", "")))
            elif item.get("type") == "input_image":
                if "image_url" in item:
                    parts.append(Part.from_uri(item["image_url"], mime_type="image/jpeg"))
    
    return parts


__all__ = [
    "ImageDetail",
    "InputImageContent",
    "InputFileContent",
    "InputVideoContent",
    "UserContent",
    "convert_user_content_to_vertex",
]
```

---

# 4. ANNOTATIONS E CITATIONS

## 4.1 Especificação Oficial

Annotations são metadados anexados ao texto gerado:

| Tipo | Campos | Descrição |
|------|--------|-----------|
| `url_citation` | `url`, `title`, `start_index`, `end_index` | Citação de URL |

## 4.2 Exemplo JSON

```json
{
  "type": "output_text",
  "text": "Python foi criado por Guido van Rossum em 1991.",
  "annotations": [
    {
      "type": "url_citation",
      "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
      "title": "Python - Wikipedia",
      "start_index": 0,
      "end_index": 47
    }
  ]
}
```

## 4.3 Implementação Python

Adicionar ao arquivo `src/vertice_core/openresponses_types.py`:

```python
# Após OutputTextContent (~linha 106)

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
```

## 4.4 Modificar OutputTextContent

```python
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
    
    def add_citation(self, url: str, title: str = None, start: int = 0, end: int = None) -> None:
        """Adiciona uma citação de URL."""
        self.annotations.append(UrlCitation(
            url=url,
            title=title,
            start_index=start,
            end_index=end or len(self.text),
        ))
```

---

# 5. STRUCTURED OUTPUT

## 5.1 Especificação Oficial

Structured Output permite forçar o modelo a retornar JSON válido:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | `"json_schema"` | Modo JSON Schema |
| `json_schema` | `object` | Schema JSON válido |
| `strict` | `boolean` | Se true, validação estrita |

## 5.2 Exemplo de Request

```json
{
  "model": "gemini-3-pro",
  "input": [...],
  "text": {
    "format": {
      "type": "json_schema",
      "json_schema": {
        "name": "user_info",
        "strict": true,
        "schema": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"}
          },
          "required": ["name", "age"]
        }
      }
    }
  }
}
```

## 5.3 Implementação Python

Adicionar ao arquivo `src/vertice_core/openresponses_types.py`:

```python
# Nova seção após ErrorType (~linha 85)

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
            }
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
```

## 5.4 Usar com Vertex AI

```python
# Em vertex_ai.py, adicionar suporte a response_schema:

async def stream_chat_structured(
    self,
    messages: List[Dict[str, str]],
    response_format: JsonSchemaResponseFormat,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Stream com structured output (JSON Schema).
    """
    from google.genai.types import GenerateContentConfig
    
    config = GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_format.schema,
    )
    
    async for chunk in self.stream_chat(
        messages,
        generation_config=config,
        **kwargs,
    ):
        yield chunk
```

---

# 6. EXTENSÕES VERTICE

## 6.1 Especificação Oficial

Extensões devem usar prefixo do implementador:

> "New item types that are not part of this specification MUST be prefixed 
> with the implementor slug (for example, `acme:search_result`)"

## 6.2 Prefixo Vertice

Usar `vertice:` para tipos customizados:

| Tipo | Descrição |
|------|-----------|
| `vertice:telemetry` | Métricas de latência e cache |
| `vertice:governance` | Resultado de verificação de segurança |
| `vertice:tool_preview` | Preview de execução de tool |

## 6.3 Implementação Python

Adicionar ao arquivo `src/vertice_core/openresponses_types.py`:

```python
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
```

---

# 7. VERIFICAÇÃO

## 7.1 Testes Unitários

Criar arquivo `tests/unit/test_openresponses_phase2.py`:

```python
"""Testes para Open Responses Fase 2."""

import pytest
from vertice_core.openresponses_types import (
    ReasoningItem,
    SummaryTextContent,
    UrlCitation,
    JsonSchemaResponseFormat,
    VerticeTelemetryItem,
    ItemStatus,
)


class TestReasoningItem:
    """Testes para ReasoningItem."""
    
    def test_creation(self):
        item = ReasoningItem()
        assert item.type == "reasoning"
        assert item.id.startswith("rs_")
        assert item.status == ItemStatus.IN_PROGRESS
        assert item.content == []
        assert item.summary == []
        assert item.encrypted_content is None
    
    def test_append_content(self):
        item = ReasoningItem()
        item.append_content("Step 1: Analyze")
        item.append_content(" Step 2: Process")
        assert item.get_reasoning_text() == "Step 1: Analyze Step 2: Process"
    
    def test_set_summary(self):
        item = ReasoningItem()
        item.set_summary("Analyzed user request and found solution.")
        assert len(item.summary) == 1
        assert item.get_summary_text() == "Analyzed user request and found solution."
    
    def test_to_dict(self):
        item = ReasoningItem()
        item.append_content("Thinking...")
        item.set_summary("Short summary")
        item.status = ItemStatus.COMPLETED
        
        d = item.to_dict()
        assert d["type"] == "reasoning"
        assert d["status"] == "completed"
        assert len(d["content"]) == 1
        assert len(d["summary"]) == 1


class TestUrlCitation:
    """Testes para UrlCitation."""
    
    def test_creation(self):
        citation = UrlCitation(
            url="https://example.com",
            title="Example",
            start_index=0,
            end_index=50,
        )
        assert citation.type == "url_citation"
        assert citation.url == "https://example.com"
    
    def test_to_dict(self):
        citation = UrlCitation(url="https://example.com", start_index=10, end_index=20)
        d = citation.to_dict()
        assert d["url"] == "https://example.com"
        assert d["start_index"] == 10
        assert d["end_index"] == 20


class TestJsonSchemaResponseFormat:
    """Testes para JsonSchemaResponseFormat."""
    
    def test_creation(self):
        schema_format = JsonSchemaResponseFormat(
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
        assert schema_format.type == "json_schema"
        assert schema_format.name == "user_info"
        assert schema_format.strict is True
    
    def test_to_dict(self):
        schema_format = JsonSchemaResponseFormat(name="test", schema={"type": "object"})
        d = schema_format.to_dict()
        assert d["type"] == "json_schema"
        assert d["json_schema"]["name"] == "test"
        assert d["json_schema"]["strict"] is True


class TestVerticeExtensions:
    """Testes para extensões Vertice."""
    
    def test_telemetry_item(self):
        item = VerticeTelemetryItem(
            latency_ms=142,
            cache_hit=False,
            model="gemini-3-pro",
            provider="vertex-ai",
        )
        assert item.type == "vertice:telemetry"
        assert item.id.startswith("vt_")
        
        d = item.to_dict()
        assert d["latency_ms"] == 142
        assert d["model"] == "gemini-3-pro"
```

## 7.2 Comandos de Execução

```bash
# Rodar testes Fase 2
pytest tests/unit/test_openresponses_phase2.py -v

# Rodar todos os testes Open Responses
pytest tests/unit/test_openresponses*.py -v

# Verificar imports
python -c "
from vertice_core.openresponses_types import (
    ReasoningItem, SummaryTextContent,
    UrlCitation, FileCitation,
    JsonSchemaResponseFormat,
    VerticeTelemetryItem, VerticeGovernanceItem,
)
print('✅ All Phase 2 types imported successfully!')
"
```

---

# CHECKLIST DE IMPLEMENTAÇÃO

## Reasoning Items
- [ ] Adicionar `SummaryTextContent` em `openresponses_types.py`
- [ ] Adicionar `ReasoningItem` em `openresponses_types.py`
- [ ] Adicionar eventos de streaming para reasoning
- [ ] Adicionar método `add_reasoning()` no StreamBuilder
- [ ] Atualizar `__all__` exports

## Input Multimodal
- [ ] Criar `openresponses_multimodal.py`
- [ ] Implementar `InputImageContent`
- [ ] Implementar `InputFileContent`
- [ ] Implementar `InputVideoContent`
- [ ] Adicionar conversão para Vertex AI

## Annotations
- [ ] Adicionar `UrlCitation` em `openresponses_types.py`
- [ ] Adicionar `FileCitation` em `openresponses_types.py`
- [ ] Modificar `OutputTextContent` para aceitar annotations
- [ ] Adicionar método `add_citation()`

## Structured Output
- [ ] Adicionar `TextResponseFormat`
- [ ] Adicionar `JsonObjectResponseFormat`
- [ ] Adicionar `JsonSchemaResponseFormat`
- [ ] Adicionar `from_pydantic_model()` helper
- [ ] Adicionar suporte em `VertexAIProvider`

## Extensões Vertice
- [ ] Adicionar `VerticeTelemetryItem`
- [ ] Adicionar `VerticeGovernanceItem`
- [ ] Documentar formato de prefixo `vertice:`

## Testes
- [ ] Criar `tests/unit/test_openresponses_phase2.py`
- [ ] Testar ReasoningItem
- [ ] Testar UrlCitation
- [ ] Testar JsonSchemaResponseFormat
- [ ] Testar extensões Vertice

---

**FIM DO DOCUMENTO**

Autor: Antigravity AI Assistant  
Data: 16 de Janeiro de 2026  
Versão: 2.0
