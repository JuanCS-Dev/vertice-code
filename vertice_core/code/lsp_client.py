"""
LSP Client - Unified Language Server Protocol Client.

Implements async LSP client following Claude Code v2.0.74 patterns:
- Multi-language support (Python, TypeScript, Go, Rust, etc.)
- JSON-RPC 2.0 over stdio
- Automatic server lifecycle management
- Connection pooling and health checks

Performance target: 50ms for go-to-definition (vs 45s grep)

References:
- Microsoft multilspy patterns
- LSP Specification 3.17
- Claude Code LSP integration (Dec 2025)

Phase 10: Sprint 3 - Code Intelligence

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

logger = logging.getLogger(__name__)

# Type aliases
JsonRpcId = Union[int, str]
T = TypeVar("T")


class DiagnosticSeverity(int, Enum):
    """LSP Diagnostic severity levels."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class SymbolKind(int, Enum):
    """LSP Symbol kinds."""

    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


@dataclass
class Position:
    """LSP Position (0-indexed)."""

    line: int
    character: int

    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Position":
        return cls(line=data["line"], character=data["character"])


@dataclass
class Range:
    """LSP Range."""

    start: Position
    end: Position

    def to_dict(self) -> Dict[str, Any]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Range":
        return cls(
            start=Position.from_dict(data["start"]),
            end=Position.from_dict(data["end"]),
        )


@dataclass
class Location:
    """LSP Location."""

    uri: str
    range: Range

    @property
    def filepath(self) -> str:
        """Convert URI to filepath."""
        if self.uri.startswith("file://"):
            return self.uri[7:]
        return self.uri

    @property
    def line(self) -> int:
        """1-indexed line number."""
        return self.range.start.line + 1

    @property
    def column(self) -> int:
        """1-indexed column number."""
        return self.range.start.character + 1

    def to_dict(self) -> Dict[str, Any]:
        return {"uri": self.uri, "range": self.range.to_dict()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(uri=data["uri"], range=Range.from_dict(data["range"]))


@dataclass
class Diagnostic:
    """LSP Diagnostic."""

    range: Range
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None
    source: Optional[str] = None

    @property
    def is_error(self) -> bool:
        return self.severity == DiagnosticSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == DiagnosticSeverity.WARNING

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagnostic":
        return cls(
            range=Range.from_dict(data["range"]),
            message=data.get("message", ""),
            severity=DiagnosticSeverity(data.get("severity", 1)),
            code=str(data.get("code")) if data.get("code") else None,
            source=data.get("source"),
        )


@dataclass
class DocumentSymbol:
    """LSP Document Symbol."""

    name: str
    kind: SymbolKind
    range: Range
    selection_range: Range
    detail: Optional[str] = None
    children: List["DocumentSymbol"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSymbol":
        children = [cls.from_dict(c) for c in data.get("children", [])]
        return cls(
            name=data["name"],
            kind=SymbolKind(data.get("kind", 1)),
            range=Range.from_dict(data["range"]),
            selection_range=Range.from_dict(data.get("selectionRange", data["range"])),
            detail=data.get("detail"),
            children=children,
        )


@dataclass
class HoverInfo:
    """LSP Hover information."""

    contents: str
    range: Optional[Range] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoverInfo":
        contents = data.get("contents", "")
        if isinstance(contents, dict):
            contents = contents.get("value", str(contents))
        elif isinstance(contents, list):
            contents = "\n".join(
                c.get("value", str(c)) if isinstance(c, dict) else str(c)
                for c in contents
            )

        range_data = data.get("range")
        return cls(
            contents=contents,
            range=Range.from_dict(range_data) if range_data else None,
        )


@dataclass
class CompletionItem:
    """LSP Completion item."""

    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletionItem":
        doc = data.get("documentation", "")
        if isinstance(doc, dict):
            doc = doc.get("value", "")

        return cls(
            label=data["label"],
            kind=data.get("kind"),
            detail=data.get("detail"),
            documentation=doc,
            insert_text=data.get("insertText"),
        )


@dataclass
class LanguageServerConfig:
    """Configuration for a language server."""

    language: str
    command: List[str]
    file_extensions: List[str]
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    root_markers: List[str] = field(default_factory=list)

    def is_installed(self) -> bool:
        """Check if the language server is installed."""
        if not self.command:
            return False
        return shutil.which(self.command[0]) is not None


# Default language server configurations
DEFAULT_LANGUAGE_SERVERS: Dict[str, LanguageServerConfig] = {
    "python": LanguageServerConfig(
        language="python",
        command=["pylsp"],
        file_extensions=[".py", ".pyi"],
        root_markers=["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
        settings={
            "pylsp": {
                "plugins": {
                    "pycodestyle": {"enabled": False},
                    "mccabe": {"enabled": False},
                    "pyflakes": {"enabled": True},
                    "rope_autoimport": {"enabled": True},
                }
            }
        },
    ),
    "typescript": LanguageServerConfig(
        language="typescript",
        command=["typescript-language-server", "--stdio"],
        file_extensions=[".ts", ".tsx", ".js", ".jsx"],
        root_markers=["tsconfig.json", "jsconfig.json", "package.json"],
    ),
    "javascript": LanguageServerConfig(
        language="javascript",
        command=["typescript-language-server", "--stdio"],
        file_extensions=[".js", ".jsx", ".mjs"],
        root_markers=["package.json", "jsconfig.json"],
    ),
    "go": LanguageServerConfig(
        language="go",
        command=["gopls"],
        file_extensions=[".go"],
        root_markers=["go.mod", "go.sum"],
    ),
    "rust": LanguageServerConfig(
        language="rust",
        command=["rust-analyzer"],
        file_extensions=[".rs"],
        root_markers=["Cargo.toml"],
    ),
    "java": LanguageServerConfig(
        language="java",
        command=["jdtls"],
        file_extensions=[".java"],
        root_markers=["pom.xml", "build.gradle", "build.gradle.kts"],
    ),
    "c": LanguageServerConfig(
        language="c",
        command=["clangd"],
        file_extensions=[".c", ".h"],
        root_markers=["compile_commands.json", "CMakeLists.txt", "Makefile"],
    ),
    "cpp": LanguageServerConfig(
        language="cpp",
        command=["clangd"],
        file_extensions=[".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
        root_markers=["compile_commands.json", "CMakeLists.txt", "Makefile"],
    ),
}


class JsonRpcError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")


class LSPConnectionError(Exception):
    """LSP connection error."""

    pass


class LSPTimeoutError(Exception):
    """LSP request timeout."""

    pass


class JsonRpcConnection:
    """
    JSON-RPC 2.0 connection over stdio.

    Handles the low-level protocol communication with language servers.
    """

    def __init__(
        self,
        process: asyncio.subprocess.Process,
        timeout: float = 30.0,
    ):
        self.process = process
        self.timeout = timeout
        self._request_id = 0
        self._pending_requests: Dict[JsonRpcId, asyncio.Future] = {}
        self._notification_handlers: Dict[str, Callable] = {}
        self._reader_task: Optional[asyncio.Task] = None
        self._closed = False

    async def start(self) -> None:
        """Start the reader task."""
        self._reader_task = asyncio.create_task(self._read_loop())

    async def close(self) -> None:
        """Close the connection."""
        self._closed = True

        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()

        # Terminate process
        if self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _read_loop(self) -> None:
        """Read and dispatch messages from the server."""
        reader = self.process.stdout
        if not reader:
            return

        try:
            while not self._closed:
                # Read headers
                headers = {}
                while True:
                    line = await reader.readline()
                    if not line:
                        return  # EOF
                    line = line.decode("utf-8").strip()
                    if not line:
                        break
                    if ":" in line:
                        key, value = line.split(":", 1)
                        headers[key.strip().lower()] = value.strip()

                # Read content
                content_length = int(headers.get("content-length", 0))
                if content_length == 0:
                    continue

                content = await reader.readexactly(content_length)
                message = json.loads(content.decode("utf-8"))

                # Dispatch
                await self._dispatch(message)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"LSP read error: {e}")

    async def _dispatch(self, message: Dict[str, Any]) -> None:
        """Dispatch a received message."""
        if "id" in message:
            # Response
            request_id = message["id"]
            if request_id in self._pending_requests:
                future = self._pending_requests.pop(request_id)
                if "error" in message:
                    error = message["error"]
                    future.set_exception(
                        JsonRpcError(
                            error.get("code", -1),
                            error.get("message", "Unknown error"),
                            error.get("data"),
                        )
                    )
                else:
                    future.set_result(message.get("result"))
        elif "method" in message:
            # Notification or request from server
            method = message["method"]
            if method in self._notification_handlers:
                try:
                    await self._notification_handlers[method](message.get("params"))
                except Exception as e:
                    logger.error(f"Notification handler error: {e}")

    async def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Send a request and wait for response."""
        if self._closed:
            raise LSPConnectionError("Connection closed")

        request_id = self._next_id()
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        # Send request
        await self._send(message)

        # Wait for response
        try:
            return await asyncio.wait_for(future, timeout=timeout or self.timeout)
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise LSPTimeoutError(f"Request {method} timed out")

    async def notify(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a notification (no response expected)."""
        if self._closed:
            raise LSPConnectionError("Connection closed")

        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            message["params"] = params

        await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> None:
        """Send a message to the server."""
        writer = self.process.stdin
        if not writer:
            raise LSPConnectionError("No stdin available")

        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"

        writer.write(header.encode("utf-8"))
        writer.write(content.encode("utf-8"))
        await writer.drain()

    def on_notification(self, method: str, handler: Callable) -> None:
        """Register a notification handler."""
        self._notification_handlers[method] = handler


class LSPClient:
    """
    Unified LSP client for multiple languages.

    Provides high-level API for LSP operations:
    - goto_definition: Find symbol definition
    - find_references: Find all references
    - hover: Get hover information
    - document_symbols: Get file symbols
    - diagnostics: Get file diagnostics
    - completion: Get completions at position

    Usage:
        async with LSPClient(workspace_root) as client:
            location = await client.goto_definition("file.py", 10, 5)
    """

    def __init__(
        self,
        workspace_root: str,
        language_configs: Optional[Dict[str, LanguageServerConfig]] = None,
    ):
        """
        Initialize LSP client.

        Args:
            workspace_root: Root directory of the workspace
            language_configs: Custom language server configurations
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_uri = f"file://{self.workspace_root}"
        self.configs = language_configs or DEFAULT_LANGUAGE_SERVERS.copy()

        # Active connections per language
        self._connections: Dict[str, JsonRpcConnection] = {}
        self._initialized: Dict[str, bool] = {}

        # Document state tracking
        self._open_documents: Dict[str, int] = {}  # uri -> version
        self._document_diagnostics: Dict[str, List[Diagnostic]] = {}

        # Stats
        self._stats = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
        }

    async def __aenter__(self) -> "LSPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close all connections."""
        for connection in self._connections.values():
            await connection.close()
        self._connections.clear()
        self._initialized.clear()

    def _get_language(self, filepath: str) -> Optional[str]:
        """Detect language from file path."""
        ext = Path(filepath).suffix.lower()
        for lang, config in self.configs.items():
            if ext in config.file_extensions:
                return lang
        return None

    def _file_uri(self, filepath: str) -> str:
        """Convert filepath to file URI."""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.workspace_root / path
        return f"file://{path.resolve()}"

    async def _get_connection(self, language: str) -> JsonRpcConnection:
        """Get or create connection for language."""
        if language in self._connections and self._initialized.get(language):
            return self._connections[language]

        config = self.configs.get(language)
        if not config:
            raise ValueError(f"No configuration for language: {language}")

        if not config.is_installed():
            raise LSPConnectionError(
                f"Language server not installed: {config.command[0]}"
            )

        # Start server process
        process = await asyncio.create_subprocess_exec(
            *config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace_root),
        )

        connection = JsonRpcConnection(process)
        await connection.start()

        # Register notification handlers
        connection.on_notification(
            "textDocument/publishDiagnostics",
            self._handle_diagnostics,
        )

        self._connections[language] = connection

        # Initialize
        await self._initialize(language, connection, config)

        return connection

    async def _initialize(
        self,
        language: str,
        connection: JsonRpcConnection,
        config: LanguageServerConfig,
    ) -> None:
        """Initialize the language server."""
        # Send initialize request
        result = await connection.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": self.workspace_uri,
                "rootPath": str(self.workspace_root),
                "capabilities": {
                    "textDocument": {
                        "synchronization": {
                            "didOpen": True,
                            "didChange": True,
                            "didClose": True,
                        },
                        "completion": {
                            "completionItem": {
                                "snippetSupport": False,
                                "documentationFormat": ["plaintext", "markdown"],
                            }
                        },
                        "hover": {
                            "contentFormat": ["plaintext", "markdown"],
                        },
                        "definition": {"linkSupport": True},
                        "references": {},
                        "documentSymbol": {
                            "hierarchicalDocumentSymbolSupport": True,
                        },
                        "publishDiagnostics": {
                            "relatedInformation": True,
                        },
                    },
                    "workspace": {
                        "workspaceFolders": True,
                        "configuration": True,
                    },
                },
                "initializationOptions": config.initialization_options,
                "workspaceFolders": [
                    {"uri": self.workspace_uri, "name": self.workspace_root.name}
                ],
            },
        )

        # Send initialized notification
        await connection.notify("initialized", {})

        # Apply settings if any
        if config.settings:
            await connection.notify(
                "workspace/didChangeConfiguration",
                {"settings": config.settings},
            )

        self._initialized[language] = True
        logger.info(f"LSP initialized for {language}")

    async def _handle_diagnostics(self, params: Dict[str, Any]) -> None:
        """Handle diagnostics notification."""
        uri = params.get("uri", "")
        diagnostics = [
            Diagnostic.from_dict(d) for d in params.get("diagnostics", [])
        ]
        self._document_diagnostics[uri] = diagnostics

    async def _ensure_document_open(
        self,
        filepath: str,
        language: str,
    ) -> str:
        """Ensure document is open in the server."""
        uri = self._file_uri(filepath)

        if uri not in self._open_documents:
            connection = await self._get_connection(language)

            # Read file content
            path = Path(filepath)
            if not path.is_absolute():
                path = self.workspace_root / path

            if not path.exists():
                raise FileNotFoundError(f"File not found: {filepath}")

            content = path.read_text(encoding="utf-8", errors="replace")

            # Open document
            await connection.notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": language,
                        "version": 1,
                        "text": content,
                    }
                },
            )

            self._open_documents[uri] = 1

        return uri

    # =========================================================================
    # Public API
    # =========================================================================

    async def goto_definition(
        self,
        filepath: str,
        line: int,
        column: int,
    ) -> Optional[Location]:
        """
        Go to definition of symbol at position.

        Args:
            filepath: Path to file
            line: 1-indexed line number
            column: 1-indexed column number

        Returns:
            Location of definition or None
        """
        self._stats["requests"] += 1
        start_time = time.time()

        language = self._get_language(filepath)
        if not language:
            return None

        try:
            uri = await self._ensure_document_open(filepath, language)
            connection = await self._get_connection(language)

            result = await connection.request(
                "textDocument/definition",
                {
                    "textDocument": {"uri": uri},
                    "position": Position(line - 1, column - 1).to_dict(),
                },
            )

            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"goto_definition completed in {elapsed:.1f}ms")

            if not result:
                return None

            # Handle array or single location
            if isinstance(result, list):
                result = result[0] if result else None

            if result:
                return Location.from_dict(result)

            return None

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"goto_definition error: {e}")
            return None

    async def find_references(
        self,
        filepath: str,
        line: int,
        column: int,
        include_declaration: bool = True,
    ) -> List[Location]:
        """
        Find all references to symbol at position.

        Args:
            filepath: Path to file
            line: 1-indexed line number
            column: 1-indexed column number
            include_declaration: Include the declaration itself

        Returns:
            List of reference locations
        """
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return []

        try:
            uri = await self._ensure_document_open(filepath, language)
            connection = await self._get_connection(language)

            result = await connection.request(
                "textDocument/references",
                {
                    "textDocument": {"uri": uri},
                    "position": Position(line - 1, column - 1).to_dict(),
                    "context": {"includeDeclaration": include_declaration},
                },
            )

            if not result:
                return []

            return [Location.from_dict(loc) for loc in result]

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"find_references error: {e}")
            return []

    async def hover(
        self,
        filepath: str,
        line: int,
        column: int,
    ) -> Optional[HoverInfo]:
        """
        Get hover information at position.

        Args:
            filepath: Path to file
            line: 1-indexed line number
            column: 1-indexed column number

        Returns:
            Hover information or None
        """
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return None

        try:
            uri = await self._ensure_document_open(filepath, language)
            connection = await self._get_connection(language)

            result = await connection.request(
                "textDocument/hover",
                {
                    "textDocument": {"uri": uri},
                    "position": Position(line - 1, column - 1).to_dict(),
                },
            )

            if not result:
                return None

            return HoverInfo.from_dict(result)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"hover error: {e}")
            return None

    async def document_symbols(
        self,
        filepath: str,
    ) -> List[DocumentSymbol]:
        """
        Get all symbols in document.

        Args:
            filepath: Path to file

        Returns:
            List of document symbols
        """
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return []

        try:
            uri = await self._ensure_document_open(filepath, language)
            connection = await self._get_connection(language)

            result = await connection.request(
                "textDocument/documentSymbol",
                {"textDocument": {"uri": uri}},
            )

            if not result:
                return []

            return [DocumentSymbol.from_dict(s) for s in result]

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"document_symbols error: {e}")
            return []

    async def diagnostics(
        self,
        filepath: str,
        wait_ms: int = 500,
    ) -> List[Diagnostic]:
        """
        Get diagnostics for file.

        Args:
            filepath: Path to file
            wait_ms: Time to wait for diagnostics to arrive

        Returns:
            List of diagnostics
        """
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return []

        try:
            uri = await self._ensure_document_open(filepath, language)

            # Wait for diagnostics to be published
            await asyncio.sleep(wait_ms / 1000)

            return self._document_diagnostics.get(uri, [])

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"diagnostics error: {e}")
            return []

    async def completion(
        self,
        filepath: str,
        line: int,
        column: int,
    ) -> List[CompletionItem]:
        """
        Get completions at position.

        Args:
            filepath: Path to file
            line: 1-indexed line number
            column: 1-indexed column number

        Returns:
            List of completion items
        """
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return []

        try:
            uri = await self._ensure_document_open(filepath, language)
            connection = await self._get_connection(language)

            result = await connection.request(
                "textDocument/completion",
                {
                    "textDocument": {"uri": uri},
                    "position": Position(line - 1, column - 1).to_dict(),
                },
            )

            if not result:
                return []

            # Handle CompletionList or array
            items = result.get("items", result) if isinstance(result, dict) else result

            return [CompletionItem.from_dict(item) for item in items[:50]]

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"completion error: {e}")
            return []

    async def notify_change(
        self,
        filepath: str,
        content: str,
    ) -> None:
        """
        Notify server of document change.

        Args:
            filepath: Path to file
            content: New file content
        """
        language = self._get_language(filepath)
        if not language:
            return

        uri = self._file_uri(filepath)

        if uri not in self._open_documents:
            await self._ensure_document_open(filepath, language)

        connection = await self._get_connection(language)

        # Increment version
        version = self._open_documents.get(uri, 0) + 1
        self._open_documents[uri] = version

        await connection.notify(
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": version},
                "contentChanges": [{"text": content}],
            },
        )

    async def close_document(self, filepath: str) -> None:
        """Close a document in the server."""
        language = self._get_language(filepath)
        if not language:
            return

        uri = self._file_uri(filepath)

        if uri in self._open_documents:
            connection = await self._get_connection(language)
            await connection.notify(
                "textDocument/didClose",
                {"textDocument": {"uri": uri}},
            )
            del self._open_documents[uri]

    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported."""
        return language in self.configs

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.configs.keys())

    def get_available_languages(self) -> List[str]:
        """Get list of languages with installed servers."""
        return [
            lang for lang, config in self.configs.items()
            if config.is_installed()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "active_connections": len(self._connections),
            "open_documents": len(self._open_documents),
            "languages_available": self.get_available_languages(),
        }


# Singleton instance
_lsp_client: Optional[LSPClient] = None


def get_lsp_client(workspace_root: Optional[str] = None) -> LSPClient:
    """Get or create singleton LSP client."""
    global _lsp_client
    if _lsp_client is None:
        root = workspace_root or os.getcwd()
        _lsp_client = LSPClient(root)
    return _lsp_client


async def close_lsp_client() -> None:
    """Close the singleton LSP client."""
    global _lsp_client
    if _lsp_client:
        await _lsp_client.close()
        _lsp_client = None


__all__ = [
    # Types
    "DiagnosticSeverity",
    "SymbolKind",
    "Position",
    "Range",
    "Location",
    "Diagnostic",
    "DocumentSymbol",
    "HoverInfo",
    "CompletionItem",
    "LanguageServerConfig",
    # Exceptions
    "JsonRpcError",
    "LSPConnectionError",
    "LSPTimeoutError",
    # Client
    "LSPClient",
    "get_lsp_client",
    "close_lsp_client",
    # Configs
    "DEFAULT_LANGUAGE_SERVERS",
]
