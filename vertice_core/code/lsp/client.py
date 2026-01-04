"""
LSP Client - Unified Language Server Protocol Client.

High-level API for LSP operations:
- goto_definition: Find symbol definition
- find_references: Find all references
- hover: Get hover information
- document_symbols: Get file symbols
- diagnostics: Get file diagnostics
- completion: Get completions at position
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    CompletionItem,
    Diagnostic,
    DocumentSymbol,
    HoverInfo,
    Location,
    Position,
)
from .config import LanguageServerConfig, DEFAULT_LANGUAGE_SERVERS
from .exceptions import LSPConnectionError
from .protocol import JsonRpcConnection

logger = logging.getLogger(__name__)


class LSPClient:
    """
    Unified LSP client for multiple languages.

    Usage:
        async with LSPClient(workspace_root) as client:
            location = await client.goto_definition("file.py", 10, 5)
    """

    def __init__(
        self,
        workspace_root: str,
        language_configs: Optional[Dict[str, LanguageServerConfig]] = None,
    ):
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
        return self

    async def __aexit__(self, *args) -> None:
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
            raise LSPConnectionError(f"Language server not installed: {config.command[0]}")

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
        await connection.request(
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
                "workspaceFolders": [{"uri": self.workspace_uri, "name": self.workspace_root.name}],
            },
        )

        await connection.notify("initialized", {})

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
        diagnostics = [Diagnostic.from_dict(d) for d in params.get("diagnostics", [])]
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

            path = Path(filepath)
            if not path.is_absolute():
                path = self.workspace_root / path

            if not path.exists():
                raise FileNotFoundError(f"File not found: {filepath}")

            content = path.read_text(encoding="utf-8", errors="replace")

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
        """Go to definition of symbol at position."""
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
        """Find all references to symbol at position."""
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
        """Get hover information at position."""
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

    async def document_symbols(self, filepath: str) -> List[DocumentSymbol]:
        """Get all symbols in document."""
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
        """Get diagnostics for file."""
        self._stats["requests"] += 1

        language = self._get_language(filepath)
        if not language:
            return []

        try:
            uri = await self._ensure_document_open(filepath, language)
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
        """Get completions at position."""
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

            items = result.get("items", result) if isinstance(result, dict) else result
            return [CompletionItem.from_dict(item) for item in items[:50]]

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"completion error: {e}")
            return []

    async def notify_change(self, filepath: str, content: str) -> None:
        """Notify server of document change."""
        language = self._get_language(filepath)
        if not language:
            return

        uri = self._file_uri(filepath)

        if uri not in self._open_documents:
            await self._ensure_document_open(filepath, language)

        connection = await self._get_connection(language)

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
        return [lang for lang, config in self.configs.items() if config.is_installed()]

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
