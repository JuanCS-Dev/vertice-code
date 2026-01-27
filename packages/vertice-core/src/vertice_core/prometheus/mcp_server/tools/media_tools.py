"""
Media Tools for MCP Server
Image and PDF processing utilities

This module provides 3 essential media tools with
file format detection, metadata extraction, and content processing.
"""

import base64
import logging
import mimetypes
import struct
from pathlib import Path
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# Tool 1: PDF Extract
async def pdf_extract(file_path: str, pages: str = "all", max_chars: int = 50000) -> dict:
    """Extract text content from PDF files."""
    if not file_path:
        return {"success": False, "error": "file_path is required"}

    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    if path.suffix.lower() != ".pdf":
        return {"success": False, "error": "File must be a PDF"}

    size_bytes = path.stat().st_size

    try:
        # Try pypdf first
        try:
            import pypdf

            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                total_pages = len(reader.pages)
                metadata = reader.metadata or {}

                # Parse page range
                page_indices = _parse_page_range(pages, total_pages)

                # Extract text
                text_parts = []
                for page_num in page_indices:
                    if page_num < total_pages:
                        page = reader.pages[page_num]
                        text_parts.append(page.extract_text())

                text_content = "\n\n".join(text_parts)

                # Truncate if needed
                if len(text_content) > max_chars:
                    text_content = text_content[:max_chars] + "\n\n[CONTENT TRUNCATED]"
                    truncated = True
                else:
                    truncated = False

                return {
                    "success": True,
                    "file_path": file_path,
                    "total_pages": total_pages,
                    "extracted_pages": len(page_indices),
                    "text_content": text_content,
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "size_bytes": size_bytes,
                    "truncated": truncated,
                }

        except ImportError:
            # Fallback: basic PDF reading (limited)
            return {
                "success": False,
                "error": "pypdf library not available. Install with: pip install pypdf",
                "file_path": file_path,
                "size_bytes": size_bytes,
            }

    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return {"success": False, "error": str(e)}


# Tool 2: Image Describe
async def image_describe(
    file_path: str, include_base64: bool = False, max_size_mb: float = 10.0
) -> dict:
    """Extract metadata and optionally base64 data from image files."""
    if not file_path:
        return {"success": False, "error": "file_path is required"}

    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    # Check file extension
    supported_formats = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
    if path.suffix.lower() not in supported_formats:
        return {"success": False, "error": f"Unsupported image format: {path.suffix}"}

    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        return {"success": False, "error": f"File too large: {size_mb:.1f}MB (max {max_size_mb}MB)"}

    try:
        # Get basic info
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"

        # Get image dimensions (simplified)
        width, height = _get_image_dimensions(path)

        result = {
            "success": True,
            "file_path": file_path,
            "format": path.suffix[1:].upper(),  # Remove dot
            "width": width,
            "height": height,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "mime_type": mime_type,
        }

        # Include base64 if requested
        if include_base64:
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    result["base64_data"] = base64.b64encode(data).decode("utf-8")
                    result["data_url"] = f"data:{mime_type};base64,{result['base64_data']}"
            except Exception as e:
                logger.warning(f"Failed to encode image {file_path}: {e}")
                result["base64_error"] = str(e)

        return result

    except Exception as e:
        logger.error(f"Error reading image {file_path}: {e}")
        return {"success": False, "error": str(e)}


# Tool 3: Media Info
async def media_info(file_path: str) -> dict:
    """Get general information about media files."""
    if not file_path:
        return {"success": False, "error": "file_path is required"}

    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Detect file type
        mime_type, encoding = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"

        # Basic file info
        result = {
            "success": True,
            "file_path": file_path,
            "filename": path.name,
            "extension": path.suffix,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "mime_type": mime_type,
            "encoding": encoding,
        }

        # Specific handling for known types
        if mime_type and mime_type.startswith("image/"):
            result["type"] = "image"
            # Try to get dimensions
            try:
                width, height = _get_image_dimensions(path)
                result["width"] = width
                result["height"] = height
            except Exception as e:
                pass

        elif path.suffix.lower() == ".pdf":
            result["type"] = "pdf"
            # Try to get PDF info
            try:
                import pypdf

                with open(path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    result["pages"] = len(reader.pages)
                    metadata = reader.metadata or {}
                    result["title"] = metadata.get("/Title", "")
                    result["author"] = metadata.get("/Author", "")
            except ImportError:
                result["pages"] = "unknown (install pypdf)"
            except Exception as e:
                result["pages"] = "unknown"

        elif mime_type and mime_type.startswith("video/"):
            result["type"] = "video"

        elif mime_type and mime_type.startswith("audio/"):
            result["type"] = "audio"

        else:
            result["type"] = "unknown"

        return result

    except Exception as e:
        logger.error(f"Error getting media info for {file_path}: {e}")
        return {"success": False, "error": str(e)}


def _parse_page_range(pages_spec: str, total_pages: int) -> list:
    """Parse page range specification like '1-5' or 'all'."""
    if pages_spec.lower() == "all":
        return list(range(total_pages))

    try:
        if "-" in pages_spec:
            start, end = map(int, pages_spec.split("-"))
            start = max(0, start - 1)  # Convert to 0-based
            end = min(total_pages, end)  # Exclusive
            return list(range(start, end))
        else:
            page_num = int(pages_spec) - 1  # Convert to 0-based
            if 0 <= page_num < total_pages:
                return [page_num]
            return []
    except ValueError:
        return []


def _get_image_dimensions(path: Path) -> tuple[int, int]:
    """Get image dimensions from file header."""
    with open(path, "rb") as f:
        header = f.read(24)

    # PNG
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", header[16:24])
        return width, height

    # GIF
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        width, height = struct.unpack("<HH", header[6:10])
        return width, height

    # JPEG
    elif header.startswith(b"\xff\xd8"):
        # Find SOF marker
        f.seek(0)
        data = f.read()
        for i in range(len(data) - 1):
            if data[i] == 0xFF and data[i + 1] in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                return width, height

    # Default fallback
    return 0, 0


# Create and register all media tools
media_tools = [
    create_validated_tool(
        name="pdf_extract",
        description="Extract text content from PDF files",
        category="media",
        parameters={
            "file_path": {"type": "string", "description": "Path to PDF file", "required": True},
            "pages": {
                "type": "string",
                "description": "Page range (e.g., '1-5', 'all')",
                "default": "all",
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters to extract",
                "default": 50000,
                "minimum": 100,
                "maximum": 100000,
            },
        },
        required_params=["file_path"],
        execute_func=pdf_extract,
    ),
    create_validated_tool(
        name="image_describe",
        description="Extract metadata and optionally base64 data from image files",
        category="media",
        parameters={
            "file_path": {"type": "string", "description": "Path to image file", "required": True},
            "include_base64": {
                "type": "boolean",
                "description": "Include base64-encoded image data",
                "default": False,
            },
            "max_size_mb": {
                "type": "number",
                "description": "Maximum file size in MB",
                "default": 10.0,
                "minimum": 0.1,
                "maximum": 50.0,
            },
        },
        required_params=["file_path"],
        execute_func=image_describe,
    ),
    create_validated_tool(
        name="media_info",
        description="Get general information about media files (images, PDFs, etc.)",
        category="media",
        parameters={
            "file_path": {"type": "string", "description": "Path to media file", "required": True}
        },
        required_params=["file_path"],
        execute_func=media_info,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in media_tools:
    register_tool(tool)
