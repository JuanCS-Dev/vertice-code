"""
LSP Exceptions - Error types for LSP operations.

Contains:
- JsonRpcError: JSON-RPC protocol error
- LSPConnectionError: Connection error
- LSPTimeoutError: Request timeout
"""

from typing import Any


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
