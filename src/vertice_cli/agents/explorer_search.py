"""
Search Module - Filesystem search utilities for explorer.

Provides ripgrep/grep content search and name-based file discovery.
Extracted from ExplorerAgent for modularity and maintainability.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

logger = logging.getLogger(__name__)


def search_by_name(
    keyword: str,
    project_root: Path,
    exclude_dirs: Set[str],
    code_extensions: Set[str],
) -> List[Dict[str, Any]]:
    """Search files/directories by name pattern.

    Args:
        keyword: Search keyword
        project_root: Project root directory
        exclude_dirs: Directories to exclude
        code_extensions: Valid code file extensions

    Returns:
        List of results with path, relevance, reason
    """
    results: List[Dict[str, Any]] = []

    try:
        for path in project_root.rglob(f"*{keyword}*"):
            if any(ex in str(path) for ex in exclude_dirs):
                continue

            rel_path = str(path.relative_to(project_root))

            if path.is_dir():
                results.append(
                    {
                        "path": f"{rel_path}/",
                        "relevance": "HIGH",
                        "reason": f"Diretório contém '{keyword}'",
                    }
                )
                # List some files from directory
                try:
                    for f in list(path.iterdir())[:5]:
                        if f.is_file() and f.suffix in code_extensions:
                            results.append(
                                {
                                    "path": str(f.relative_to(project_root)),
                                    "relevance": "MEDIUM",
                                    "reason": f"Em diretório '{keyword}'",
                                }
                            )
                except (PermissionError, OSError):
                    pass

            elif path.is_file() and path.suffix in code_extensions:
                results.append(
                    {
                        "path": rel_path,
                        "relevance": "HIGH",
                        "reason": f"Nome contém '{keyword}'",
                    }
                )
    except (OSError, PermissionError) as e:
        logger.warning(f"Search by name for '{keyword}' failed: {e}")

    return results


def search_content(
    keyword: str,
    project_root: Path,
    exclude_dirs: Set[str],
    extract_snippet: Callable[[Path], str],
) -> List[Dict[str, Any]]:
    """Search keyword in file contents using ripgrep.

    Args:
        keyword: Search keyword
        project_root: Project root directory
        exclude_dirs: Directories to exclude
        extract_snippet: Function to extract code snippet from file

    Returns:
        List of results with path, relevance, reason, snippet
    """
    results: List[Dict[str, Any]] = []

    try:
        # Build ripgrep command
        exclude_args = []
        for ex in exclude_dirs:
            exclude_args.extend(["-g", f"!{ex}/**"])

        cmd = ["rg", "-l", "-i", "--max-count=1"] + exclude_args + [keyword, str(project_root)]

        output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if output.stdout:
            for line in output.stdout.strip().split("\n")[:20]:
                if line:
                    try:
                        file_path = Path(line)
                        rel_path = str(file_path.relative_to(project_root))
                        snippet = extract_snippet(file_path)

                        results.append(
                            {
                                "path": rel_path,
                                "relevance": "MEDIUM",
                                "reason": f"Contém '{keyword}'",
                                "snippet": snippet,
                            }
                        )
                    except (ValueError, OSError):
                        pass

    except FileNotFoundError:
        # ripgrep not installed, use grep fallback
        results.extend(_search_content_grep(keyword, project_root, exclude_dirs, extract_snippet))
    except (subprocess.TimeoutExpired, OSError):
        pass

    return results


def _search_content_grep(
    keyword: str,
    project_root: Path,
    exclude_dirs: Set[str],
    extract_snippet: Callable[[Path], str],
) -> List[Dict[str, Any]]:
    """Fallback search using grep when ripgrep unavailable."""
    results: List[Dict[str, Any]] = []

    try:
        cmd = ["grep", "-rl", "-i", "--include=*.py", keyword, str(project_root)]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if output.stdout:
            for line in output.stdout.strip().split("\n")[:15]:
                if line and not any(ex in line for ex in exclude_dirs):
                    try:
                        file_path = Path(line)
                        rel_path = str(file_path.relative_to(project_root))
                        snippet = extract_snippet(file_path)

                        results.append(
                            {
                                "path": rel_path,
                                "relevance": "MEDIUM",
                                "reason": f"Contém '{keyword}'",
                                "snippet": snippet,
                            }
                        )
                    except (ValueError, OSError):
                        pass
    except (subprocess.TimeoutExpired, OSError):
        pass

    return results


def deep_search_imports(
    keyword: str,
    project_root: Path,
    exclude_dirs: Set[str],
) -> List[Dict[str, Any]]:
    """Deep search for imports and usages recursively.

    Args:
        keyword: Search keyword (typically module/class name)
        project_root: Project root directory
        exclude_dirs: Directories to exclude

    Returns:
        List of results with path, relevance, reason
    """
    results: List[Dict[str, Any]] = []

    patterns = [
        f"from .* import .*{keyword}",
        f"import .*{keyword}",
        f"{keyword}\\(",
        f"{keyword}\\.",
    ]

    for pattern in patterns[:2]:  # Focus on import patterns
        try:
            exclude_args = []
            for ex in exclude_dirs:
                exclude_args.extend(["-g", f"!{ex}/**"])

            cmd = ["rg", "-l", "-i", "--max-count=1"] + exclude_args + [pattern, str(project_root)]

            output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if output.stdout:
                for line in output.stdout.strip().split("\n")[:10]:
                    if line:
                        try:
                            file_path = Path(line)
                            rel_path = str(file_path.relative_to(project_root))

                            # Avoid duplicates
                            if not any(r["path"] == rel_path for r in results):
                                results.append(
                                    {
                                        "path": rel_path,
                                        "relevance": "HIGH",
                                        "reason": f"Importa ou usa '{keyword}'",
                                    }
                                )
                        except (ValueError, OSError):
                            pass
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    return results


__all__ = ["search_by_name", "search_content", "deep_search_imports"]
