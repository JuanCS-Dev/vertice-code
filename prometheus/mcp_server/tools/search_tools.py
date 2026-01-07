"""
Search Tools for MCP Server
Text and file search toolkit

This module provides 4 essential search tools with
fast text search, semantic search, directory trees, and file matching.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# Tool 1: Search Files
async def search_files(
    pattern: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    max_results: int = 50,
    ignore_case: bool = False,
    semantic: bool = False,
) -> dict:
    """Search for text pattern in files using ripgrep or grep."""
    try:
        # For now, skip semantic search (would need indexer integration)
        if semantic:
            logger.info("Semantic search not implemented, falling back to text search")

        # Try ripgrep first
        cmd = ["rg", "--line-number", "--with-filename", "--no-heading"]

        if ignore_case:
            cmd.append("-i")

        if file_pattern:
            cmd.extend(["--glob", file_pattern])

        cmd.extend([pattern, path])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[:max_results]

                matches = []
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            matches.append(
                                {
                                    "file": parts[0],
                                    "line": int(parts[1]),
                                    "text": parts[2].strip(),
                                }
                            )

                return {
                    "success": True,
                    "matches": matches,
                    "count": len(matches),
                    "tool": "ripgrep",
                }
        except FileNotFoundError:
            logger.debug("ripgrep not available, falling back to grep")

        # Fallback to grep
        cmd = ["grep", "-rn"]
        if ignore_case:
            cmd.append("-i")
        cmd.extend([pattern, path])
        if file_pattern:
            cmd.extend(["--include", file_pattern])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        lines = result.stdout.strip().split("\n")[:max_results]

        matches = []
        for line in lines:
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    matches.append(
                        {"file": parts[0], "line": int(parts[1]), "text": parts[2].strip()}
                    )

        return {"success": True, "matches": matches, "count": len(matches), "tool": "grep"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool 2: Get Directory Tree
async def get_directory_tree(path: str = ".", max_depth: int = 3) -> dict:
    """Get hierarchical file tree structure."""
    try:
        dir_path = Path(path)

        if not dir_path.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        def build_tree(dir_path: Path, prefix: str = "", depth: int = 0) -> List[str]:
            """Recursively build tree structure."""
            if depth > max_depth:
                return []

            lines = []
            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

                # Skip hidden and common ignored directories
                items = [
                    x
                    for x in items
                    if not x.name.startswith(".")
                    and x.name not in ["__pycache__", "node_modules", "venv"]
                ]

                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "

                    lines.append(
                        f"{prefix}{current_prefix}{item.name}{'/' if item.is_dir() else ''}"
                    )

                    if item.is_dir():
                        lines.extend(build_tree(item, prefix + next_prefix, depth + 1))
            except PermissionError:
                logger.debug("Permission denied in directory tree")

            return lines

        tree_lines = [f"{dir_path.name}/"]
        tree_lines.extend(build_tree(dir_path))
        tree_str = "\n".join(tree_lines)

        return {"success": True, "tree": tree_str, "path": str(dir_path), "max_depth": max_depth}

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool 3: Glob
async def glob_files(pattern: str, path: str = ".", max_results: int = 100) -> dict:
    """Fast file pattern matching using glob patterns."""
    try:
        root = Path(path).resolve()
        if not root.exists():
            return {"success": False, "error": f"Path does not exist: {path}"}

        if not root.is_dir():
            return {"success": False, "error": f"Path is not a directory: {path}"}

        # Use pathlib glob for recursive patterns
        matches = []
        for match in root.glob(pattern):
            if match.is_file():
                try:
                    rel_path = str(match.relative_to(root))
                    mtime = match.stat().st_mtime
                    matches.append((mtime, rel_path))
                except (ValueError, OSError):
                    continue

        # Sort by modification time (newest first)
        matches.sort(key=lambda x: x[0], reverse=True)

        # Return just the paths, limited to max_results
        result_paths = [p for _, p in matches[:max_results]]

        return {
            "success": True,
            "files": result_paths,
            "pattern": pattern,
            "path": str(root),
            "total_matches": len(matches),
            "returned": len(result_paths),
            "truncated": len(matches) > max_results,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool 4: LS (List Directory)
async def list_directory(
    path: str = ".", all_files: bool = False, ignore: Optional[List[str]] = None
) -> dict:
    """List directory contents with file details."""
    ignore_patterns = ignore or []

    try:
        dir_path = Path(path).resolve()

        if not dir_path.exists():
            return {"success": False, "error": f"Path does not exist: {path}"}

        if not dir_path.is_dir():
            return {"success": False, "error": f"Path is not a directory: {path}"}

        entries = []
        try:
            dir_contents = sorted(
                dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError:
            return {"success": False, "error": f"Permission denied reading: {path}"}

        import fnmatch

        for entry in dir_contents:
            name = entry.name

            # Skip hidden files unless requested
            if not all_files and name.startswith("."):
                continue

            # Skip ignored patterns
            if any(fnmatch.fnmatch(name, pat) for pat in ignore_patterns):
                continue

            try:
                stat = entry.stat()
                entries.append(
                    {
                        "name": name,
                        "type": "directory" if entry.is_dir() else "file",
                        "size": stat.st_size if entry.is_file() else None,
                        "modified": stat.st_mtime,
                    }
                )
            except OSError:
                entries.append({"name": name, "type": "unknown", "size": None, "modified": None})

        return {
            "success": True,
            "entries": entries,
            "path": str(dir_path),
            "count": len(entries),
            "show_hidden": all_files,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Create and register all search tools
search_tools = [
    create_validated_tool(
        name="search_files",
        description="Search for text pattern in files (uses ripgrep if available)",
        category="search",
        parameters={
            "pattern": {
                "type": "string",
                "description": "Text pattern to search for",
                "required": True,
            },
            "path": {"type": "string", "description": "Directory to search in", "default": "."},
            "file_pattern": {
                "type": "string",
                "description": "File pattern to include (e.g., '*.py')",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 50,
                "minimum": 1,
                "maximum": 1000,
            },
            "ignore_case": {
                "type": "boolean",
                "description": "Case insensitive search",
                "default": False,
            },
            "semantic": {
                "type": "boolean",
                "description": "Use semantic search (code symbols)",
                "default": False,
            },
        },
        required_params=["pattern"],
        execute_func=search_files,
    ),
    create_validated_tool(
        name="get_directory_tree",
        description="Get hierarchical file tree structure",
        category="search",
        parameters={
            "path": {"type": "string", "description": "Directory path", "default": "."},
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth to traverse",
                "default": 3,
                "minimum": 1,
                "maximum": 10,
            },
        },
        required_params=[],
        execute_func=get_directory_tree,
    ),
    create_validated_tool(
        name="glob",
        description="Fast file pattern matching using glob patterns like **/*.py",
        category="search",
        parameters={
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match files",
                "required": True,
            },
            "path": {"type": "string", "description": "Directory to search in", "default": "."},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 100,
                "minimum": 1,
                "maximum": 10000,
            },
        },
        required_params=["pattern"],
        execute_func=glob_files,
    ),
    create_validated_tool(
        name="ls",
        description="List directory contents with details (size, type, modified)",
        category="search",
        parameters={
            "path": {"type": "string", "description": "Directory path to list", "default": "."},
            "all": {"type": "boolean", "description": "Include hidden files", "default": False},
            "ignore": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Patterns to ignore",
            },
        },
        required_params=[],
        execute_func=list_directory,
    ),
]
