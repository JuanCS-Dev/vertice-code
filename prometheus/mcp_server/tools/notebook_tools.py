"""
Notebook Tools for MCP Server
Jupyter notebook operations toolkit

This module provides 2 essential notebook tools with
file format validation, cell operations, and safe file handling.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)


def validate_notebook_path(path: str) -> bool:
    """Validate that path points to a Jupyter notebook."""
    if not path:
        return False
    return Path(path).suffix.lower() == ".ipynb"


def notebook_read(file_path: str, cell_type: str = "all") -> ToolResult:
    """Read Jupyter notebook (.ipynb) files."""
    MAX_NOTEBOOK_SIZE = 50 * 1024 * 1024  # 50MB

    if not file_path:
        return ToolResult(success=False, error="file_path is required")

    if cell_type not in ("all", "code", "markdown", "raw"):
        cell_type = "all"

    path = Path(file_path)

    if not path.exists():
        return ToolResult(success=False, error=f"File not found: {file_path}")

    if not validate_notebook_path(str(path)):
        return ToolResult(success=False, error="File must be a .ipynb notebook")

    # Check file size
    try:
        file_size = path.stat().st_size
        if file_size > MAX_NOTEBOOK_SIZE:
            return ToolResult(
                success=False,
                error=f"Notebook too large ({file_size} bytes). Max: {MAX_NOTEBOOK_SIZE}",
            )
    except OSError as e:
        return ToolResult(success=False, error=f"Cannot access file: {e}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        # Validate notebook structure
        if not isinstance(notebook, dict):
            return ToolResult(success=False, error="Invalid notebook format")

        cells = notebook.get("cells", [])
        if not isinstance(cells, list):
            return ToolResult(success=False, error="Invalid notebook: missing cells")

        result_cells = []
        for idx, cell in enumerate(cells):
            if not isinstance(cell, dict):
                continue

            cell_type_actual = cell.get("cell_type", "unknown")

            # Apply filter
            if cell_type != "all" and cell_type_actual != cell_type:
                continue

            # Get source (can be string or list of strings)
            source = cell.get("source", [])
            if isinstance(source, list):
                source = "".join(source)

            cell_data = {
                "index": idx,
                "cell_id": cell.get("id", f"cell_{idx}"),
                "type": cell_type_actual,
                "source": source,
            }

            # Include outputs for code cells
            if cell_type_actual == "code":
                outputs = cell.get("outputs", [])
                cell_data["execution_count"] = cell.get("execution_count")
                cell_data["outputs"] = _parse_outputs(outputs)

            result_cells.append(cell_data)

        # Extract metadata
        metadata = notebook.get("metadata", {})
        kernel_info = metadata.get("kernelspec", {})
        nbformat = notebook.get("nbformat", 4)
        nbformat_minor = notebook.get("nbformat_minor", 0)

        return ToolResult(
            success=True,
            data={
                "cells": result_cells,
                "total_cells": len(cells),
                "filtered_cells": len(result_cells),
                "kernel": kernel_info.get("display_name", "Unknown"),
                "language": kernel_info.get("language", "unknown"),
            },
            metadata={
                "file": str(path),
                "filter": cell_type,
                "nbformat": f"{nbformat}.{nbformat_minor}",
                "file_size": file_size,
            },
        )

    except json.JSONDecodeError as e:
        return ToolResult(success=False, error=f"Invalid notebook JSON: {e}")
    except UnicodeDecodeError:
        return ToolResult(success=False, error="Notebook file is not valid UTF-8")
    except Exception as e:
        logger.error(f"NotebookRead error: {e}")
        return ToolResult(success=False, error=str(e))


def notebook_edit(
    notebook_path: str,
    cell_id: Optional[str] = None,
    edit_mode: str = "replace",
    cell_type: str = "code",
    new_source: str = "",
) -> ToolResult:
    """Edit Jupyter notebook (.ipynb) cells."""

    if not notebook_path:
        return ToolResult(success=False, error="notebook_path is required")

    if edit_mode not in ("replace", "insert", "delete"):
        return ToolResult(
            success=False, error=f"Invalid edit_mode: {edit_mode}. Use: replace, insert, delete"
        )

    if cell_type not in ("code", "markdown", "raw"):
        cell_type = "code"

    path = Path(notebook_path)

    if not path.exists():
        return ToolResult(success=False, error=f"File not found: {notebook_path}")

    if not validate_notebook_path(str(path)):
        return ToolResult(success=False, error="File must be a .ipynb notebook")

    try:
        # Read notebook
        with open(path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        if not isinstance(notebook, dict):
            return ToolResult(success=False, error="Invalid notebook format")

        cells = notebook.get("cells", [])
        if not isinstance(cells, list):
            return ToolResult(success=False, error="Invalid notebook: missing cells")

        # Execute edit operation
        if edit_mode == "delete":
            result = _delete_cell(cells, cell_id)
        elif edit_mode == "insert":
            result = _insert_cell(cells, cell_id, cell_type, new_source)
        else:  # replace
            result = _replace_cell(cells, cell_id, cell_type, new_source)

        if not result["success"]:
            return ToolResult(success=False, error=result["error"])

        notebook["cells"] = cells

        # Write back with consistent formatting
        with open(path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)

        return ToolResult(
            success=True,
            data={"action": result["action"], "total_cells": len(cells)},
            metadata={"file": str(path), "mode": edit_mode},
        )

    except json.JSONDecodeError as e:
        return ToolResult(success=False, error=f"Invalid notebook JSON: {e}")
    except PermissionError:
        return ToolResult(success=False, error=f"Permission denied: {notebook_path}")
    except Exception as e:
        logger.error(f"NotebookEdit error: {e}")
        return ToolResult(success=False, error=str(e))


def _parse_outputs(outputs: List[dict]) -> List[dict]:
    """Parse cell outputs to readable format."""
    if not isinstance(outputs, list):
        return []

    parsed = []
    for output in outputs:
        if not isinstance(output, dict):
            continue

        out_type = output.get("output_type", "unknown")

        if out_type == "stream":
            text = output.get("text", [])
            if isinstance(text, list):
                text = "".join(text)
            parsed.append(
                {
                    "type": "stream",
                    "name": output.get("name", "stdout"),
                    "text": text[:5000],  # Limit text length
                }
            )

        elif out_type == "execute_result":
            data = output.get("data", {})
            parsed.append(
                {
                    "type": "result",
                    "text": str(data.get("text/plain", ""))[:2000],
                    "html": data.get("text/html", "")[:1000] if data.get("text/html") else None,
                }
            )

        elif out_type == "error":
            parsed.append(
                {
                    "type": "error",
                    "ename": output.get("ename", "Error"),
                    "evalue": output.get("evalue", "")[:500],
                    "traceback": output.get("traceback", [])[:5],  # Limit traceback
                }
            )

        elif out_type == "display_data":
            data = output.get("data", {})
            parsed.append(
                {
                    "type": "display",
                    "has_image": "image/png" in data or "image/jpeg" in data,
                    "text": str(data.get("text/plain", ""))[:1000],
                }
            )

    return parsed


def _find_cell_index(cells: List[dict], cell_id: Optional[str]) -> Optional[int]:
    """Find cell index by ID or index string."""
    if cell_id is None:
        return None

    # Try as integer index first
    try:
        idx = int(cell_id)
        if 0 <= idx < len(cells):
            return idx
    except (ValueError, TypeError):
        pass

    # Try to find by cell id
    for i, cell in enumerate(cells):
        if cell.get("id") == cell_id:
            return i

    return None


def _create_cell(cell_type: str, source: str) -> dict:
    """Create a new notebook cell."""
    cell = {
        "id": str(uuid.uuid4())[:8],
        "cell_type": cell_type,
        "metadata": {},
        "source": source.split("\n") if source else [],
    }

    if cell_type == "code":
        cell["outputs"] = []
        cell["execution_count"] = None

    return cell


def _delete_cell(cells: List[dict], cell_id: Optional[str]) -> dict:
    """Delete a cell by ID or index."""
    idx = _find_cell_index(cells, cell_id)
    if idx is None:
        return {"success": False, "error": f"Cell not found: {cell_id}"}

    cells.pop(idx)
    return {"success": True, "action": f"Deleted cell {idx}"}


def _insert_cell(cells: List[dict], cell_id: Optional[str], cell_type: str, source: str) -> dict:
    """Insert a new cell after specified cell (or at beginning)."""
    new_cell = _create_cell(cell_type, source)

    if cell_id:
        idx = _find_cell_index(cells, cell_id)
        if idx is None:
            return {"success": False, "error": f"Cell not found: {cell_id}"}
        cells.insert(idx + 1, new_cell)
        return {"success": True, "action": f"Inserted new {cell_type} cell after index {idx}"}
    else:
        cells.insert(0, new_cell)
        return {"success": True, "action": f"Inserted new {cell_type} cell at beginning"}


def _replace_cell(
    cells: List[dict], cell_id: Optional[str], cell_type: Optional[str], source: str
) -> dict:
    """Replace cell content."""
    if cell_id is None:
        return {"success": False, "error": "cell_id required for replace"}

    idx = _find_cell_index(cells, cell_id)
    if idx is None:
        return {"success": False, "error": f"Cell not found: {cell_id}"}

    # Update source, preserve cell type if not specified
    if cell_type:
        cells[idx]["cell_type"] = cell_type

    cells[idx]["source"] = source.split("\n") if source else []

    # Clear outputs for code cells
    if cells[idx].get("cell_type") == "code":
        cells[idx]["outputs"] = []
        cells[idx]["execution_count"] = None

    return {"success": True, "action": f"Replaced cell {idx}"}


# Create and register all notebook tools
notebook_tools = [
    create_validated_tool(
        name="notebook_read",
        description="Read Jupyter notebook files (.ipynb) with cell content and outputs",
        category="file",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the .ipynb file",
                "required": True,
            },
            "cell_type": {
                "type": "string",
                "description": "Filter by cell type: 'code', 'markdown', 'raw', or 'all' (default)",
                "default": "all",
                "enum": ["all", "code", "markdown", "raw"],
            },
        },
        required_params=["file_path"],
        execute_func=notebook_read,
    ),
    create_validated_tool(
        name="notebook_edit",
        description="Edit Jupyter notebook cells (replace, insert, delete)",
        category="file",
        parameters={
            "notebook_path": {
                "type": "string",
                "description": "Path to the .ipynb file",
                "required": True,
            },
            "cell_id": {
                "type": "string",
                "description": "ID or index of the cell to edit (required for replace/delete)",
            },
            "edit_mode": {
                "type": "string",
                "description": "Edit mode: 'replace', 'insert', or 'delete'",
                "default": "replace",
                "enum": ["replace", "insert", "delete"],
            },
            "cell_type": {
                "type": "string",
                "description": "Cell type for new/edited cells: 'code' or 'markdown'",
                "default": "code",
                "enum": ["code", "markdown", "raw"],
            },
            "new_source": {
                "type": "string",
                "description": "New content for the cell",
                "required": True,
            },
        },
        required_params=["notebook_path", "new_source"],
        execute_func=notebook_edit,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in notebook_tools:
    register_tool(tool)
