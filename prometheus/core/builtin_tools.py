"""
Prometheus Built-in Tools Implementation.

Contains the direct implementation of core filesystem and memory tools
used by the Orchestrator.

Phase 5 Refactoring - Modularization.
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

import os
import glob
import subprocess
import uuid
from typing import Any
import logging

logger = logging.getLogger(__name__)

class BuiltinTools:
    """Implementations for Prometheus internal tools."""

    def __init__(self, orchestrator: Any):
        self.orch = orchestrator

    async def read_file(self, path: str) -> str:
        """Read file contents."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return content[:10000]
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    async def write_file(self, path: str, content: str) -> str:
        """Write content to file."""
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    async def list_files(self, directory: str = ".", pattern: str = "*") -> str:
        """List files in directory."""
        try:
            files = glob.glob(os.path.join(directory, pattern))
            return "\n".join(files[:50])
        except Exception as e:
            return f"Error listing files: {e}"

    async def execute_python(self, code: str) -> str:
        """Execute Python code in sandbox."""
        result = await self.orch.sandbox.execute(code, timeout=30)
        if result.success:
            return result.stdout or "Code executed successfully (no output)"
        return f"Error: {result.stderr or result.error_message}"

    async def search_code(self, query: str, path: str = ".") -> str:
        """Search for code patterns."""
        try:
            result = subprocess.run(
                ["grep", "-r", "-n", query, path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout[:5000] or "No matches found"
        except Exception as e:
            return f"Search error: {e}"

    async def remember(self, key: str, value: str) -> str:
        """Store something in memory."""
        from .persistence import persistence
        self.orch.memory.learn_fact(key, value, source="tool_remember")
        try:
            await persistence.store_memory(
                memory_id=str(uuid.uuid4()),
                type="semantic",
                content=f"{key}: {value}",
                metadata={"source": "tool_remember", "key": key},
                importance=0.8
            )
            return f"Remembered and persisted: {key}"
        except Exception as e:
            return f"Remembered in session, but persistence failed: {e}"

    async def recall(self, query: str) -> str:
        """Recall from memory."""
        from .persistence import persistence
        session_results = self.orch.memory.search_knowledge(query, top_k=3)
        try:
            persistent_results = await persistence.retrieve_memories(type="semantic", limit=5)
            persistent_matches = [
                m for m in persistent_results if query.lower() in m["content"].lower()
            ]
        except Exception as e:
            logger.warning(f"Persistence recall failed: {e}")
            persistent_matches = []

        results = []
        if session_results:
            results.append("Session Memory:")
            results.extend([f"- {r['topic']}: {r['content']}" for r in session_results])
        if persistent_matches:
            results.append("\nLong-term Memory:")
            results.extend([f"- {r['content']}" for r in persistent_matches])
            
        return "\n".join(results) if results else "Nothing relevant found in memory"
