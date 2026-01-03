"""
LSP Protocol - JSON-RPC 2.0 connection over stdio.

Handles low-level protocol communication with language servers.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Union

from .exceptions import JsonRpcError, LSPConnectionError, LSPTimeoutError

logger = logging.getLogger(__name__)

# Type alias
JsonRpcId = Union[int, str]


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
