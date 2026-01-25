"""
Context Tools for MCP Server
Session and context management utilities

This module provides 5 essential context management tools with
file-based persistence, session tracking, and context operations.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# Tool 1: Save Context
async def save_context(context_id: str, data: Dict[str, Any], path: str = ".mcp_contexts") -> dict:
    """Save context data to file."""
    if not context_id:
        return {"success": False, "error": "context_id is required"}

    if not data:
        return {"success": False, "error": "data cannot be empty"}

    try:
        context_dir = Path(path)
        context_dir.mkdir(exist_ok=True)

        context_data = {
            "context_id": context_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        file_path = context_dir / f"{context_id}.json"
        with open(file_path, "w") as f:
            json.dump(context_data, f, indent=2)

        return {
            "success": True,
            "message": f"Context '{context_id}' saved successfully",
            "file_path": str(file_path),
            "timestamp": context_data["timestamp"],
        }

    except Exception as e:
        logger.error(f"Failed to save context {context_id}: {e}")
        return {"success": False, "error": str(e)}


# Tool 2: Load Context
async def load_context(context_id: str, path: str = ".mcp_contexts") -> dict:
    """Load context data from file."""
    if not context_id:
        return {"success": False, "error": "context_id is required"}

    try:
        context_dir = Path(path)
        file_path = context_dir / f"{context_id}.json"

        if not file_path.exists():
            return {"success": False, "error": f"Context '{context_id}' not found"}

        with open(file_path, "r") as f:
            context_data = json.load(f)

        return {
            "success": True,
            "context_id": context_data["context_id"],
            "timestamp": context_data["timestamp"],
            "data": context_data["data"],
        }

    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON in context file: {context_id}"}
    except Exception as e:
        logger.error(f"Failed to load context {context_id}: {e}")
        return {"success": False, "error": str(e)}


# Tool 3: Get Context
async def get_context(path: str = ".") -> dict:
    """Get current context information."""
    try:
        import os
        import subprocess

        # Get git branch if in repo
        try:
            result = subprocess.run(
                ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            git_branch = result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            git_branch = None

        # Get basic system info
        context = {
            "cwd": os.getcwd(),
            "git_branch": git_branch,
            "timestamp": datetime.now().isoformat(),
            "platform": os.uname().sysname if hasattr(os, "uname") else "unknown",
        }

        return {"success": True, "context": context}

    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        return {"success": False, "error": str(e)}


# Tool 4: Update Context
async def update_context(
    context_id: str, updates: Dict[str, Any], path: str = ".mcp_contexts"
) -> dict:
    """Update existing context data."""
    if not context_id:
        return {"success": False, "error": "context_id is required"}

    if not updates:
        return {"success": False, "error": "updates cannot be empty"}

    try:
        # First load existing context
        load_result = await load_context(context_id, path)
        if not load_result["success"]:
            return load_result

        # Merge updates
        existing_data = load_result["data"]
        existing_data.update(updates)

        # Save updated context
        save_result = await save_context(context_id, existing_data, path)

        if save_result["success"]:
            save_result["message"] = f"Context '{context_id}' updated successfully"

        return save_result

    except Exception as e:
        logger.error(f"Failed to update context {context_id}: {e}")
        return {"success": False, "error": str(e)}


# Tool 5: List Contexts
async def list_contexts(path: str = ".mcp_contexts") -> dict:
    """List all saved contexts."""
    try:
        context_dir = Path(path)

        if not context_dir.exists():
            return {
                "success": True,
                "contexts": [],
                "count": 0,
                "message": "No contexts directory found",
            }

        contexts = []
        for json_file in context_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                contexts.append(
                    {
                        "context_id": data["context_id"],
                        "timestamp": data["timestamp"],
                        "file_path": str(json_file),
                        "data_keys": list(data.get("data", {}).keys()),
                    }
                )

            except (json.JSONDecodeError, KeyError):
                # Skip invalid files
                logger.warning(f"Skipping invalid context file: {json_file}")
                continue

        # Sort by timestamp (newest first)
        contexts.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"success": True, "contexts": contexts, "count": len(contexts)}

    except Exception as e:
        logger.error(f"Failed to list contexts: {e}")
        return {"success": False, "error": str(e)}


# Create and register all context tools
context_tools = [
    create_validated_tool(
        name="save_context",
        description="Save context data to file for persistence",
        category="context",
        parameters={
            "context_id": {
                "type": "string",
                "description": "Unique identifier for the context",
                "required": True,
            },
            "data": {"type": "object", "description": "Context data to save", "required": True},
            "path": {
                "type": "string",
                "description": "Directory to save contexts",
                "default": ".mcp_contexts",
            },
        },
        required_params=["context_id", "data"],
        execute_func=save_context,
    ),
    create_validated_tool(
        name="load_context",
        description="Load context data from file",
        category="context",
        parameters={
            "context_id": {
                "type": "string",
                "description": "Context identifier to load",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "Directory where contexts are saved",
                "default": ".mcp_contexts",
            },
        },
        required_params=["context_id"],
        execute_func=load_context,
    ),
    create_validated_tool(
        name="get_context",
        description="Get current environment context (cwd, git branch, etc.)",
        category="context",
        parameters={
            "path": {"type": "string", "description": "Path to check for context", "default": "."}
        },
        required_params=[],
        execute_func=get_context,
    ),
    create_validated_tool(
        name="update_context",
        description="Update existing context data with new values",
        category="context",
        parameters={
            "context_id": {
                "type": "string",
                "description": "Context identifier to update",
                "required": True,
            },
            "updates": {"type": "object", "description": "Data updates to apply", "required": True},
            "path": {
                "type": "string",
                "description": "Directory where contexts are saved",
                "default": ".mcp_contexts",
            },
        },
        required_params=["context_id", "updates"],
        execute_func=update_context,
    ),
    create_validated_tool(
        name="list_contexts",
        description="List all saved contexts with metadata",
        category="context",
        parameters={
            "path": {
                "type": "string",
                "description": "Directory where contexts are saved",
                "default": ".mcp_contexts",
            }
        },
        required_params=[],
        execute_func=list_contexts,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in context_tools:
    register_tool(tool)
