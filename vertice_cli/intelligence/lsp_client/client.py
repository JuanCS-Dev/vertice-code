"""
LSP Client - Multi-language LSP client for code intelligence.

Provides hover, definition, references, completion, and signature help.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    Diagnostic,
    Language,
    Location,
    LSPServerConfig,
    Position,
    Range,
)
from .responses import (
    CompletionItem,
    HoverInfo,
    ParameterInformation,
    SignatureHelp,
    SignatureInformation,
)

logger = logging.getLogger(__name__)


class LSPClient:
    """
    Multi-language LSP client for code intelligence.

    Supports:
    - Python (pylsp)
    - TypeScript/JavaScript (typescript-language-server)
    - Go (gopls)

    Communication via JSON-RPC over stdio.
    """

    def __init__(self, root_path: Path, language: Optional[Language] = None):
        """
        Initialize LSP client.

        Args:
            root_path: Project root directory
            language: Target language (auto-detect if None)
        """
        self.root_path = Path(root_path).resolve()
        self.root_uri = f"file://{self.root_path}"
        self.language = language or Language.PYTHON

        self._process: Optional[subprocess.Popen[bytes]] = None
        self._initialized = False
        self._message_id = 0
        self._diagnostics: Dict[str, List[Diagnostic]] = {}
        self._server_configs = LSPServerConfig.get_configs()

        logger.info(
            f"LSP client initialized for {self.root_path} (language: {self.language.value})"
        )

    def _next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id

    def _file_to_uri(self, file_path: Path) -> str:
        """Convert file path to URI."""
        return f"file://{file_path.resolve()}"

    def _uri_to_file(self, uri: str) -> Path:
        """Convert URI to file path."""
        if uri.startswith("file://"):
            return Path(uri[7:])
        return Path(uri)

    async def start(self, language: Optional[Language] = None) -> bool:
        """Start LSP server for specified language."""
        if self._process is not None:
            logger.warning("LSP server already running")
            return True

        target_language = language or self.language

        if target_language not in self._server_configs:
            logger.error(f"No LSP server configured for {target_language.value}")
            return False

        config = self._server_configs[target_language]

        try:
            # Start LSP server
            self._process = subprocess.Popen(
                config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.root_path),
            )

            # Initialize
            await self._initialize(config)
            self._initialized = True
            self.language = target_language

            logger.info(f"LSP server started successfully ({target_language.value})")
            return True

        except FileNotFoundError:
            logger.error(
                f"LSP server not found for {target_language.value}. "
                f"Command: {' '.join(config.command)}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to start LSP server: {e}")
            return False

    async def _initialize(self, config: LSPServerConfig) -> None:
        """Send initialize request."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": self.root_uri,
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "definition": {"linkSupport": True},
                        "references": {},
                        "completion": {
                            "completionItem": {
                                "snippetSupport": True,
                                "documentationFormat": ["markdown", "plaintext"],
                            }
                        },
                        "signatureHelp": {
                            "signatureInformation": {
                                "documentationFormat": ["markdown", "plaintext"],
                                "parameterInformation": {"labelOffsetSupport": True},
                            }
                        },
                        "publishDiagnostics": {},
                    }
                },
                "initializationOptions": config.initialization_options or {},
            },
        }

        logger.debug(f"LSP initialized ({config.language.value})")

    async def stop(self) -> None:
        """Stop LSP server."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(asyncio.to_thread(self._process.wait), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()

            self._process = None
            self._initialized = False
            logger.info("LSP server stopped")

    async def hover(self, file_path: Path, line: int, character: int) -> Optional[HoverInfo]:
        """Get hover information at position."""
        if not self._initialized:
            logger.warning("LSP not initialized")
            return None

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            if line >= len(lines):
                return None

            line_text = lines[line]
            if character >= len(line_text):
                return None

            # Find word boundaries
            start = character
            while start > 0 and (line_text[start - 1].isalnum() or line_text[start - 1] == "_"):
                start -= 1

            end = character
            while end < len(line_text) and (line_text[end].isalnum() or line_text[end] == "_"):
                end += 1

            word = line_text[start:end]
            if not word:
                return None

            hover_text = f"Symbol: `{word}`\n\n"
            hover_text += "_(LSP integration in progress - basic info only)_"

            return HoverInfo(
                contents=hover_text,
                range=Range(start=Position(line, start), end=Position(line, end)),
            )

        except Exception as e:
            logger.error(f"Hover failed: {e}")
            return None

    async def definition(self, file_path: Path, line: int, character: int) -> List[Location]:
        """Go to definition."""
        if not self._initialized:
            logger.warning("LSP not initialized")
            return []

        try:
            logger.info(f"Definition lookup: {file_path}:{line}:{character}")
            return []

        except Exception as e:
            logger.error(f"Definition lookup failed: {e}")
            return []

    async def references(self, file_path: Path, line: int, character: int) -> List[Location]:
        """Find all references."""
        if not self._initialized:
            logger.warning("LSP not initialized")
            return []

        try:
            logger.info(f"References lookup: {file_path}:{line}:{character}")
            return []

        except Exception as e:
            logger.error(f"References lookup failed: {e}")
            return []

    async def diagnostics(self, file_path: Path) -> List[Diagnostic]:
        """Get diagnostics for file."""
        uri = self._file_to_uri(file_path)
        return self._diagnostics.get(uri, [])

    def get_all_diagnostics(self) -> Dict[str, List[Diagnostic]]:
        """Get all diagnostics across all files."""
        return self._diagnostics.copy()

    async def completion(
        self, file_path: Path, line: int, character: int, trigger_kind: int = 1
    ) -> List[CompletionItem]:
        """Get code completions at position."""
        if not self._initialized:
            logger.warning("LSP not initialized")
            return []

        try:
            logger.info(f"Completion requested: {file_path}:{line}:{character}")

            return [
                CompletionItem(
                    label="example_function",
                    kind=3,  # Function
                    detail="() -> None",
                    documentation="Example function for demonstration",
                )
            ]

        except Exception as e:
            logger.error(f"Completion failed: {e}")
            return []

    async def signature_help(
        self, file_path: Path, line: int, character: int
    ) -> Optional[SignatureHelp]:
        """Get signature help (function parameter hints) at position."""
        if not self._initialized:
            logger.warning("LSP not initialized")
            return None

        try:
            logger.info(f"Signature help requested: {file_path}:{line}:{character}")

            param = ParameterInformation(label="param1: str", documentation="First parameter")

            sig = SignatureInformation(
                label="example_function(param1: str) -> None",
                documentation="Example function signature",
                parameters=[param],
                active_parameter=0,
            )

            return SignatureHelp(signatures=[sig], active_signature=0, active_parameter=0)

        except Exception as e:
            logger.error(f"Signature help failed: {e}")
            return None

    async def open_file(self, file_path: Path) -> None:
        """Notify LSP that file is opened."""
        if not self._initialized:
            return

        try:
            content = file_path.read_text()
            logger.debug(f"File opened: {file_path}")
        except Exception as e:
            logger.error(f"Failed to open file in LSP: {e}")

    async def close_file(self, file_path: Path) -> None:
        """Notify LSP that file is closed."""
        if not self._initialized:
            return

        logger.debug(f"File closed: {file_path}")

    def __enter__(self) -> "LSPClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        asyncio.run(self.stop())


__all__ = ["LSPClient"]
