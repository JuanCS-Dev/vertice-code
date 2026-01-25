"""
JSON-RPC 2.0 Helpers

Utility functions for A2A JSON-RPC message formatting.

Reference:
- JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification
- A2A Protocol: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional


# Standard JSON-RPC 2.0 error codes
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


def create_jsonrpc_request(
    method: str,
    params: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 request."""
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": request_id or str(uuid.uuid4()),
    }


def create_jsonrpc_response(
    result: Any,
    request_id: str,
) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 success response."""
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id,
    }


def create_jsonrpc_error(
    code: int,
    message: str,
    request_id: Optional[str] = None,
    data: Optional[Any] = None,
) -> Dict[str, Any]:
    """Create a JSON-RPC 2.0 error response."""
    error: Dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if data:
        error["data"] = data

    return {
        "jsonrpc": "2.0",
        "error": error,
        "id": request_id,
    }
