"""
Code Chunker - Semantic Code Splitting.

Splits code into semantically meaningful chunks:
- Functions/methods
- Classes
- Module-level code
- Docstrings preserved

Inspired by Cursor's chunking strategy.

Phase 10: Refinement Sprint 1
"""

from __future__ import annotations

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Type of code chunk."""

    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"
    IMPORT = "import"
    CONSTANT = "constant"
    UNKNOWN = "unknown"


@dataclass
class CodeChunk:
    """A semantic chunk of code."""

    # Identity
    chunk_id: str
    filepath: str

    # Location
    start_line: int
    end_line: int

    # Content
    content: str
    chunk_type: ChunkType

    # Metadata
    name: str  # Function/class name
    docstring: Optional[str] = None
    parent: Optional[str] = None  # Parent class for methods
    signature: Optional[str] = None  # Function signature

    # For embeddings
    tokens: int = 0
    language: str = "python"

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate tokens and generate ID."""
        self.tokens = len(self.content) // 4  # ~4 chars per token
        if not self.chunk_id:
            self.chunk_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique chunk ID."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        return f"{Path(self.filepath).stem}:{self.name}:{content_hash}"

    def to_embedding_text(self) -> str:
        """
        Generate text optimized for embedding.

        Includes: filepath, name, docstring, signature, content
        Research shows embedding summaries often works better than raw code.
        """
        parts = []

        # File context
        parts.append(f"File: {self.filepath}")

        # Symbol info
        if self.chunk_type == ChunkType.METHOD and self.parent:
            parts.append(f"Method: {self.parent}.{self.name}")
        elif self.chunk_type == ChunkType.FUNCTION:
            parts.append(f"Function: {self.name}")
        elif self.chunk_type == ChunkType.CLASS:
            parts.append(f"Class: {self.name}")
        else:
            parts.append(f"Code: {self.name}")

        # Signature
        if self.signature:
            parts.append(f"Signature: {self.signature}")

        # Docstring (very important for semantic search)
        if self.docstring:
            parts.append(f"Description: {self.docstring}")

        # Actual code
        parts.append(f"Code:\n{self.content}")

        return "\n".join(parts)


class CodeChunker:
    """
    Splits code files into semantic chunks.

    Strategies:
    - Python: AST-based (functions, classes, methods)
    - Other languages: Regex-based fallback

    Usage:
        chunker = CodeChunker()
        chunks = chunker.chunk_file("src/main.py")
    """

    # Supported languages with AST parsing
    AST_LANGUAGES = {"python"}

    # Max chunk size in tokens
    MAX_CHUNK_TOKENS = 1024
    MIN_CHUNK_TOKENS = 10  # Include small functions

    def __init__(
        self,
        max_chunk_tokens: int = MAX_CHUNK_TOKENS,
        min_chunk_tokens: int = MIN_CHUNK_TOKENS,
    ):
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens

    def chunk_file(self, filepath: str) -> List[CodeChunk]:
        """
        Chunk a single file into semantic pieces.

        Args:
            filepath: Path to the file

        Returns:
            List of CodeChunk objects
        """
        path = Path(filepath)

        if not path.exists():
            return []

        if not path.is_file():
            return []

        # Read content
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError) as e:
            logger.warning(f"Could not read file {path}: {e}")
            return []

        # Detect language
        language = self._detect_language(path.suffix)

        # Choose chunking strategy
        if language == "python":
            return self._chunk_python(str(path), content)
        else:
            return self._chunk_generic(str(path), content, language)

    def chunk_directory(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[CodeChunk]:
        """
        Chunk all files in a directory.

        Args:
            directory: Directory path
            extensions: File extensions to include (e.g., [".py", ".js"])
            exclude_patterns: Patterns to exclude (e.g., ["__pycache__", "node_modules"])

        Returns:
            List of all chunks
        """
        path = Path(directory)
        if not path.is_dir():
            return []

        # Default extensions
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java"]

        # Default excludes
        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__",
                "node_modules",
                ".git",
                ".venv",
                "venv",
                "dist",
                "build",
                ".egg-info",
                ".pytest_cache",
                ".mypy_cache",
            ]

        chunks = []

        for file_path in path.rglob("*"):
            # Skip directories
            if not file_path.is_file():
                continue

            # Check extension
            if file_path.suffix not in extensions:
                continue

            # Check excludes
            if any(excl in str(file_path) for excl in exclude_patterns):
                continue

            # Chunk file
            file_chunks = self.chunk_file(str(file_path))
            chunks.extend(file_chunks)

        return chunks

    def _chunk_python(self, filepath: str, content: str) -> List[CodeChunk]:
        """Chunk Python code using AST."""
        chunks = []
        lines = content.splitlines(keepends=True)

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to generic chunking
            return self._chunk_generic(filepath, content, "python")

        # Extract top-level functions and classes only (not nested ones)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Module-level function
                chunk = self._extract_function_chunk(node, filepath, lines)
                if chunk and chunk.tokens >= self.min_chunk_tokens:
                    chunks.append(chunk)

            elif isinstance(node, ast.ClassDef):
                # Add class-level chunk
                chunk = self._extract_class_chunk(node, filepath, lines)
                if chunk and chunk.tokens >= self.min_chunk_tokens:
                    chunks.append(chunk)

                # Also add method chunks
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_chunk = self._extract_function_chunk(
                            item, filepath, lines, parent_class=node.name
                        )
                        if method_chunk and method_chunk.tokens >= self.min_chunk_tokens:
                            chunks.append(method_chunk)

        # If no chunks found, treat whole file as one chunk
        if not chunks:
            chunks.append(
                CodeChunk(
                    chunk_id="",
                    filepath=filepath,
                    start_line=1,
                    end_line=len(lines),
                    content=content,
                    chunk_type=ChunkType.MODULE,
                    name=Path(filepath).stem,
                    language="python",
                )
            )

        return chunks

    def _extract_function_chunk(
        self,
        node: ast.FunctionDef,
        filepath: str,
        lines: List[str],
        parent_class: Optional[str] = None,
    ) -> Optional[CodeChunk]:
        """Extract a function/method as a chunk."""
        try:
            start = node.lineno - 1
            end = node.end_lineno or node.lineno

            content = "".join(lines[start:end])

            # Get docstring
            docstring = ast.get_docstring(node)

            # Build signature
            args = []
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    try:
                        arg_str += f": {ast.unparse(arg.annotation)}"
                    except (AttributeError, ValueError):
                        pass
                args.append(arg_str)

            returns = ""
            if node.returns:
                try:
                    returns = f" -> {ast.unparse(node.returns)}"
                except (AttributeError, ValueError):
                    pass

            signature = f"def {node.name}({', '.join(args)}){returns}"

            chunk_type = ChunkType.METHOD if parent_class else ChunkType.FUNCTION

            return CodeChunk(
                chunk_id="",
                filepath=filepath,
                start_line=start + 1,
                end_line=end,
                content=content,
                chunk_type=chunk_type,
                name=node.name,
                docstring=docstring,
                parent=parent_class,
                signature=signature,
                language="python",
            )
        except (AttributeError, ValueError, TypeError):
            return None

    def _extract_class_chunk(
        self,
        node: ast.ClassDef,
        filepath: str,
        lines: List[str],
    ) -> Optional[CodeChunk]:
        """Extract a class definition as a chunk (without method bodies)."""
        try:
            start = node.lineno - 1

            # Find where the class signature ends (before first method)
            end = start + 1
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end = item.lineno - 1
                    break
                else:
                    end = getattr(item, "end_lineno", item.lineno)

            # Ensure we at least capture docstring
            docstring = ast.get_docstring(node)
            if docstring:
                # Find where docstring ends
                for i, item in enumerate(node.body):
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant):
                        end = max(end, item.end_lineno or item.lineno)
                        break

            content = "".join(lines[start:end])

            # Build signature with bases
            bases = []
            for base in node.bases:
                try:
                    bases.append(ast.unparse(base))
                except (AttributeError, ValueError):
                    bases.append("?")

            base_str = f"({', '.join(bases)})" if bases else ""
            signature = f"class {node.name}{base_str}"

            return CodeChunk(
                chunk_id="",
                filepath=filepath,
                start_line=start + 1,
                end_line=end,
                content=content,
                chunk_type=ChunkType.CLASS,
                name=node.name,
                docstring=docstring,
                signature=signature,
                language="python",
            )
        except (AttributeError, ValueError, TypeError):
            return None

    def _chunk_generic(
        self,
        filepath: str,
        content: str,
        language: str,
    ) -> List[CodeChunk]:
        """
        Generic chunking for non-Python languages.

        Uses regex patterns to identify functions and classes.
        Falls back to fixed-size chunks if patterns don't match.
        """
        chunks = []
        lines = content.splitlines(keepends=True)

        # Language-specific patterns
        patterns = self._get_language_patterns(language)

        if patterns:
            # Try pattern-based chunking
            for pattern, chunk_type in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    start_pos = match.start()
                    # Find start line
                    start_line = content[:start_pos].count("\n") + 1

                    # Find end (next blank line or pattern match)
                    end_pos = self._find_chunk_end(content, match.end(), language)
                    end_line = content[:end_pos].count("\n") + 1

                    chunk_content = content[start_pos:end_pos]
                    name = match.group(1) if match.groups() else f"chunk_{start_line}"

                    chunk = CodeChunk(
                        chunk_id="",
                        filepath=filepath,
                        start_line=start_line,
                        end_line=end_line,
                        content=chunk_content,
                        chunk_type=chunk_type,
                        name=name,
                        language=language,
                    )

                    if chunk.tokens >= self.min_chunk_tokens:
                        chunks.append(chunk)

        # If no chunks found, use fixed-size chunking
        if not chunks:
            chunks = self._fixed_size_chunk(filepath, content, language)

        return chunks

    def _get_language_patterns(self, language: str) -> List[tuple]:
        """Get regex patterns for language."""
        patterns = {
            "javascript": [
                (r"(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{", ChunkType.FUNCTION),
                (
                    r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                    ChunkType.FUNCTION,
                ),
                (r"class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{", ChunkType.CLASS),
            ],
            "typescript": [
                (r"(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)", ChunkType.FUNCTION),
                (
                    r"(?:const|let|var)\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                    ChunkType.FUNCTION,
                ),
                (r"class\s+(\w+)(?:<[^>]*>)?(?:\s+extends\s+\w+)?\s*\{", ChunkType.CLASS),
                (r"interface\s+(\w+)(?:<[^>]*>)?\s*\{", ChunkType.CLASS),
            ],
            "go": [
                (r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\([^)]*\)", ChunkType.FUNCTION),
                (r"type\s+(\w+)\s+struct\s*\{", ChunkType.CLASS),
                (r"type\s+(\w+)\s+interface\s*\{", ChunkType.CLASS),
            ],
            "rust": [
                (
                    r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)",
                    ChunkType.FUNCTION,
                ),
                (r"(?:pub\s+)?struct\s+(\w+)(?:<[^>]*>)?\s*\{", ChunkType.CLASS),
                (r"(?:pub\s+)?enum\s+(\w+)(?:<[^>]*>)?\s*\{", ChunkType.CLASS),
                (r"impl(?:<[^>]*>)?\s+(\w+)", ChunkType.CLASS),
            ],
            "java": [
                (
                    r"(?:public|private|protected)?\s*(?:static)?\s*(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+)?\s*\{",
                    ChunkType.FUNCTION,
                ),
                (r"(?:public|private|protected)?\s*class\s+(\w+)", ChunkType.CLASS),
                (r"(?:public|private|protected)?\s*interface\s+(\w+)", ChunkType.CLASS),
            ],
        }
        return patterns.get(language, [])

    def _find_chunk_end(self, content: str, start: int, language: str) -> int:
        """Find where a chunk ends (matching braces for C-like languages)."""
        brace_langs = {"javascript", "typescript", "go", "rust", "java", "c", "cpp"}

        if language in brace_langs:
            # Count braces
            depth = 0
            in_string = False
            string_char = None
            i = start

            while i < len(content):
                char = content[i]

                # Handle strings
                if char in "\"'`" and (i == 0 or content[i - 1] != "\\"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False

                if not in_string:
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth <= 0:
                            return i + 1

                i += 1

        # Default: find next blank line or EOF
        next_blank = content.find("\n\n", start)
        if next_blank != -1:
            return next_blank
        return len(content)

    def _fixed_size_chunk(
        self,
        filepath: str,
        content: str,
        language: str,
    ) -> List[CodeChunk]:
        """Split into fixed-size chunks when patterns don't work."""
        chunks = []
        lines = content.splitlines(keepends=True)

        # Approximate lines per chunk based on max tokens
        lines_per_chunk = max(20, self.max_chunk_tokens // 10)

        for i in range(0, len(lines), lines_per_chunk):
            chunk_lines = lines[i : i + lines_per_chunk]
            chunk_content = "".join(chunk_lines)

            chunk = CodeChunk(
                chunk_id="",
                filepath=filepath,
                start_line=i + 1,
                end_line=min(i + lines_per_chunk, len(lines)),
                content=chunk_content,
                chunk_type=ChunkType.UNKNOWN,
                name=f"chunk_{i // lines_per_chunk + 1}",
                language=language,
            )

            if chunk.tokens >= self.min_chunk_tokens:
                chunks.append(chunk)

        return chunks

    def _detect_language(self, suffix: str) -> str:
        """Detect language from file extension."""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
        }
        return lang_map.get(suffix.lower(), "unknown")


__all__ = [
    "ChunkType",
    "CodeChunk",
    "CodeChunker",
]
