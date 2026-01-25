"""
Open Responses Multimodal Types for Vertice.

Este módulo implementa tipos para input multimodal (imagens, arquivos).
"""

from __future__ import annotations
from typing import Literal, Optional, List, Any
from dataclasses import dataclass
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

    Suportado por modelos como Gemini 3/2.0/3.0.
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
UserContent = InputImageContent | InputFileContent | InputVideoContent


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
        if hasattr(item, "type"):
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
