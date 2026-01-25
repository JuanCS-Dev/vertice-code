"""
ExplorerAgent: The Context Navigator

Busca REAL no filesystem usando ripgrep/glob.
Retorna arquivos relevantes organizados por estrutura do projeto.

FIX E2E: Now includes content snippets, not just paths.
Following Claude Code pattern: provide actual content for grounding.
"""

import logging
import re
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from vertice_core.agents.base import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
)
from vertice_core.protocols import LLMClientProtocol, MCPClientProtocol

from .explorer_search import search_by_name, search_content, deep_search_imports

logger = logging.getLogger(__name__)

# FIX E2E: Import grounding prompts for anti-hallucination
try:
    from vertice_core.prompts.grounding import GROUNDING_INSTRUCTION
except ImportError:
    GROUNDING_INSTRUCTION = ""

# FIX E2E: Import temperature config
try:
    from vertice_core.core.temperature_config import get_temperature
except ImportError:

    def get_temperature(agent_type: str, task_type: str = None) -> float:
        """Get temperature for agent type (fallback if config module unavailable)."""
        return 0.2  # Explorer default - low for accuracy


class ExplorerAgent(BaseAgent):
    """Explorer Agent - Busca real no filesystem."""

    EXCLUDE_DIRS = {
        "__pycache__",
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        "dist",
        "build",
        ".eggs",
        ".cache",
        ".idea",
        ".vscode",
        "htmlcov",
        ".coverage",
        ".qwen",
        "egg-info",
        "site-packages",
    }

    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".md",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".css",
        ".html",
    }

    def __init__(self, llm_client: LLMClientProtocol, mcp_client: MCPClientProtocol) -> None:
        super().__init__(
            role=AgentRole.EXPLORER,
            capabilities=[AgentCapability.READ_ONLY],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="Explorer Agent - Real filesystem search",
        )
        self._project_root = Path.cwd()

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Busca arquivos relevantes no projeto."""
        try:
            query = task.request.lower()
            max_files = task.context.get("max_files", 25)

            # Get project root from context files or cwd
            files_list = task.context.get("files", [])
            cwd = task.context.get("cwd", "")

            if files_list and files_list[0]:
                # Use parent of first file as project root
                first_file = Path(files_list[0])
                if first_file.exists():
                    # Go up to find a reasonable project root (has .git or pyproject.toml)
                    candidate = first_file.parent
                    while candidate != candidate.parent:
                        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
                            self._project_root = candidate
                            break
                        candidate = candidate.parent
                    else:
                        self._project_root = first_file.parent
                else:
                    self._project_root = Path(cwd) if cwd else Path.cwd()
            elif cwd:
                self._project_root = Path(cwd)

            # Detectar tipo de busca
            search_type = self._detect_search_type(query)

            found_files: List[Dict[str, Any]] = []

            # FIRST: Include files from context (always relevant)
            if files_list:
                for f in files_list:
                    if Path(f).exists():
                        found_files.append(
                            {
                                "path": str(
                                    Path(f).relative_to(self._project_root)
                                    if f.startswith(str(self._project_root))
                                    else f
                                ),
                                "relevance": "HIGH",
                                "reason": "Arquivo fornecido no contexto",
                            }
                        )
                        # Also analyze content for classes/functions
                        try:
                            content = Path(f).read_text(errors="ignore")
                            # Extract class names
                            import re

                            classes = re.findall(r"class\s+(\w+)", content)
                            functions = re.findall(r"def\s+(\w+)", content)
                            if classes or functions:
                                found_files.append(
                                    {
                                        "path": f,
                                        "relevance": "HIGH",
                                        "reason": f"Classes: {', '.join(classes[:5])}; Functions: {', '.join(functions[:10])}",
                                    }
                                )
                        except (OSError, UnicodeDecodeError) as e:
                            logger.debug(f"Could not analyze content of {f}: {e}")

            if search_type == "structure":
                # Usuário quer ver estrutura do projeto
                found_files.extend(self._get_project_structure())
            elif search_type == "directory":
                # Buscar diretório específico
                dir_name = self._extract_dir_name(query)
                found_files.extend(self._search_directory(dir_name))
            elif search_type == "deep_search":
                # FIX E2E: Deep search using ALL keywords, not just first
                # Previous bug: keywords[:1] ignored most search terms
                keywords = self._extract_keywords(query)
                for kw in keywords[:5]:  # Use up to 5 keywords for thorough search
                    found_files.extend(self._deep_search_imports(kw))
            else:
                # Busca por keywords
                keywords = self._extract_keywords(query)

                # 1. Buscar em nomes de arquivos/diretórios (mais relevante)
                for kw in keywords:
                    found_files.extend(self._search_by_name(kw))

                # 2. Buscar conteúdo com ripgrep
                for kw in keywords[:3]:
                    found_files.extend(self._search_content(kw))

            # Deduplicar e ordenar
            seen = set()
            unique_files = []
            for f in found_files:
                path = f["path"]
                if path not in seen:
                    seen.add(path)
                    unique_files.append(f)

            # Ordenar: HIGH primeiro, depois por path
            unique_files.sort(key=lambda x: (0 if x["relevance"] == "HIGH" else 1, x["path"]))
            unique_files = unique_files[:max_files]

            # Construir resumo
            if unique_files:
                high = sum(1 for f in unique_files if f["relevance"] == "HIGH")
                summary = f"Encontrados {len(unique_files)} arquivos"
                if high:
                    summary += f" ({high} alta relevância)"
            else:
                summary = "Nenhum arquivo encontrado. Tente palavras-chave diferentes."

            return AgentResponse(
                success=True,
                data={
                    "relevant_files": unique_files,
                    "context_summary": summary,
                    "token_estimate": len(unique_files) * 200,
                },
                reasoning=summary,
            )

        except Exception as e:
            return AgentResponse(success=False, error=str(e), reasoning=f"Erro: {e}")

    async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Stream file discovery with progressive results.

        Yields file matches as they are found for real-time feedback.

        Args:
            task: Task with search query and context

        Yields:
            StreamingChunk dicts with type and data
        """
        from vertice_core.agents.protocol import StreamingChunk, StreamingChunkType

        try:
            query = task.request.lower()
            _max_files = task.context.get("max_files", 25)  # Reserved for future use

            yield StreamingChunk(
                type=StreamingChunkType.STATUS,
                data=f"🔍 Exploring project for: '{task.request[:50]}...'",
            ).to_dict()

            # Detect search type
            search_type = self._detect_search_type(query)
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data=f"📂 Search mode: {search_type}"
            ).to_dict()

            found_files: List[Dict[str, Any]] = []
            files_list = task.context.get("files", [])

            # Stream context files first
            if files_list:
                yield StreamingChunk(
                    type=StreamingChunkType.REASONING, data="### Files from context\n"
                ).to_dict()

                for f in files_list[:10]:
                    if Path(f).exists():
                        rel_path = Path(f).name
                        yield StreamingChunk(
                            type=StreamingChunkType.THINKING, data=f"- `{rel_path}` ✓\n"
                        ).to_dict()
                        found_files.append(
                            {"path": str(f), "relevance": "HIGH", "reason": "Context file"}
                        )

            # Stream keyword search results
            keywords = self._extract_keywords(query)
            if keywords:
                yield StreamingChunk(
                    type=StreamingChunkType.STATUS,
                    data=f"🔎 Searching for keywords: {', '.join(keywords[:5])}",
                ).to_dict()

            # Summary
            yield StreamingChunk(
                type=StreamingChunkType.VERDICT,
                data=f"\n\n✅ Found {len(found_files)} relevant files",
            ).to_dict()

            yield StreamingChunk(
                type=StreamingChunkType.RESULT,
                data={
                    "relevant_files": found_files,
                    "context_summary": f"Found {len(found_files)} files",
                    "token_estimate": len(found_files) * 200,
                },
            ).to_dict()

        except Exception as e:
            yield StreamingChunk(
                type=StreamingChunkType.ERROR, data=f"Explorer failed: {str(e)}"
            ).to_dict()

    def _detect_search_type(self, query: str) -> str:
        """Detecta o tipo de busca que o usuário quer."""
        structure_words = {
            "estrutura",
            "structure",
            "projeto",
            "project",
            "pastas",
            "folders",
            "organização",
        }
        dir_words = {"diretório", "directory", "pasta", "folder", "dir"}

        if any(w in query for w in structure_words):
            return "structure"
        if any(w in query for w in dir_words):
            return "directory"
        if "deep" in query or "import" in query or "usage" in query or "find" in query:
            return "deep_search"
        return "keyword"

    def _extract_dir_name(self, query: str) -> str:
        """Extrai nome de diretório da query."""
        # Palavras comuns a ignorar
        ignore = {
            "diretório",
            "directory",
            "pasta",
            "folder",
            "dir",
            "onde",
            "where",
            "está",
            "is",
            "the",
            "o",
            "a",
        }
        words = query.split()
        for w in words:
            if w.lower() not in ignore and len(w) > 2:
                return w.lower()
        return ""

    def _extract_keywords(self, query: str) -> List[str]:
        """Extrai keywords relevantes da query."""
        # FIX E2E: Expanded stopwords to avoid matching irrelevant paths
        stopwords = {
            "o",
            "a",
            "os",
            "as",
            "de",
            "da",
            "do",
            "em",
            "no",
            "na",
            "um",
            "uma",
            "para",
            "com",
            "por",
            "que",
            "se",
            "e",
            "ou",
            "onde",
            "ficam",
            "estão",
            "arquivos",
            "files",
            "where",
            "are",
            "my",
            "the",
            "is",
            "meus",
            "minha",
            "folder",
            "pasta",
            "diretório",
            "directory",
            "find",
            "search",
            "buscar",
            "procurar",
            "localizar",
            "show",
            "mostrar",
            "listar",
            "list",
            # FIX E2E: Added common words that cause false positives
            "ver",
            "quero",
            "trechos",
            "relacionados",
            "relevante",
            "conteúdo",
            "código",
            "como",
            "funciona",
            "encontre",
            "mostre",
            "veja",
            "code",
        }

        import re

        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        # Manter ordem mas sem duplicatas
        seen = set()
        unique = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        return unique[:8]

    def _get_project_structure(self) -> List[Dict[str, Any]]:
        """Retorna estrutura principal do projeto."""
        results = []

        # Arquivos raiz importantes
        root_files = [
            "README.md",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Makefile",
            "docker-compose.yml",
            ".env.example",
        ]
        for f in root_files:
            path = self._project_root / f
            if path.exists():
                results.append(
                    {"path": f, "relevance": "HIGH", "reason": "Arquivo raiz do projeto"}
                )

        # Diretórios principais (1 nível)
        for path in sorted(self._project_root.iterdir()):
            if (
                path.is_dir()
                and path.name not in self.EXCLUDE_DIRS
                and not path.name.startswith(".")
            ):
                # Contar arquivos no diretório
                try:
                    file_count = sum(1 for _ in path.glob("*.py"))
                    results.append(
                        {
                            "path": f"{path.name}/",
                            "relevance": "HIGH" if file_count > 0 else "MEDIUM",
                            "reason": f"Diretório com {file_count} arquivos .py",
                        }
                    )
                except (PermissionError, OSError):
                    pass

        return results

    def _search_directory(self, dir_name: str) -> List[Dict[str, Any]]:
        """Busca diretório e lista seu conteúdo."""
        results = []

        if not dir_name:
            return self._get_project_structure()

        # Encontrar diretórios que matcham
        for path in self._project_root.rglob(f"*{dir_name}*"):
            if path.is_dir() and not any(ex in str(path) for ex in self.EXCLUDE_DIRS):
                rel_path = str(path.relative_to(self._project_root))

                # Adicionar o diretório
                results.append(
                    {
                        "path": f"{rel_path}/",
                        "relevance": "HIGH",
                        "reason": f"Diretório matching '{dir_name}'",
                    }
                )

                # Listar arquivos dentro
                try:
                    for f in sorted(path.iterdir())[:15]:
                        if f.is_file() and f.suffix in self.CODE_EXTENSIONS:
                            results.append(
                                {
                                    "path": str(f.relative_to(self._project_root)),
                                    "relevance": "MEDIUM",
                                    "reason": f"Arquivo em {rel_path}/",
                                }
                            )
                except (PermissionError, OSError):
                    pass

        return results[:30]

    def _search_by_name(self, keyword: str) -> List[Dict[str, Any]]:
        """Search files/directories by name. Delegates to search module."""
        return search_by_name(keyword, self._project_root, self.EXCLUDE_DIRS, self.CODE_EXTENSIONS)

    def _search_content(self, keyword: str) -> List[Dict[str, Any]]:
        """Search keyword in file contents. Delegates to search module."""
        return search_content(keyword, self._project_root, self.EXCLUDE_DIRS, self._extract_snippet)

    def _deep_search_imports(self, keyword: str) -> List[Dict[str, Any]]:
        """Deep search for imports. Delegates to search module."""
        return deep_search_imports(keyword, self._project_root, self.EXCLUDE_DIRS)

    def _extract_snippet(self, file_path: Path, limit: int = 500) -> str:
        """FIX E2E: Extract meaningful snippet from file.

        Following Claude Code pattern: provide actual content, not just paths.
        This enables grounding - the LLM can cite real code.

        Args:
            file_path: Path to the file
            limit: Maximum characters for snippet

        Returns:
            Code snippet (first class/function or N chars)
        """
        try:
            if not file_path.exists():
                return ""

            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if len(content) <= limit:
                return content

            # Try to get first class or function (more meaningful than arbitrary cut)
            class_match = re.search(r"(class \w+.*?(?=\n\nclass |\n\ndef |\Z))", content, re.DOTALL)
            if class_match and len(class_match.group(1)) <= limit * 2:
                return class_match.group(1)

            func_match = re.search(r"(def \w+.*?(?=\n\ndef |\n\nclass |\Z))", content, re.DOTALL)
            if func_match and len(func_match.group(1)) <= limit:
                return func_match.group(1)

            # Fallback to first N chars
            return content[:limit] + "..."

        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Snippet extraction failed for {file_path}: {e}")
            return "[Snippet unavailable]"

    def _search_with_content(self, keyword: str) -> List[Dict[str, Any]]:
        """FIX E2E: Search files and include content snippets.

        This is the improved search that provides grounding content.

        Args:
            keyword: Search keyword

        Returns:
            List of results with path, relevance, reason, AND snippet
        """
        results = []

        try:
            # First, find matching files
            for path in self._project_root.rglob(f"*{keyword}*"):
                if any(ex in str(path) for ex in self.EXCLUDE_DIRS):
                    continue

                if path.is_file() and path.suffix in self.CODE_EXTENSIONS:
                    rel_path = str(path.relative_to(self._project_root))

                    # Include content snippet
                    snippet = self._extract_snippet(path)

                    results.append(
                        {
                            "path": rel_path,
                            "relevance": "HIGH",
                            "reason": f"Arquivo contém '{keyword}'",
                            "snippet": snippet,
                            "size": path.stat().st_size,
                        }
                    )

                    if len(results) >= 20:
                        break

        except (OSError, PermissionError) as e:
            logger.warning(f"Content search with snippets failed for '{keyword}': {e}")

        return results
