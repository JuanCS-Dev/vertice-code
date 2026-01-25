"""
DocumentationAgent - The Technical Writer: Documentation Excellence Specialist.

This agent generates comprehensive, maintainable documentation from codebases.
It supports multiple formats (Markdown, API Reference, Docstrings) and follows
best practices from Write the Docs and Google Style Guide.

Capabilities:
    - AST-based code analysis (functions, classes, modules)
    - Multi-format documentation generation (MD, RST, HTML)
    - Docstring validation and generation (Google, NumPy, Sphinx)
    - API reference extraction and formatting
    - README generation with usage examples

Architecture:
    DocumentationAgent extends BaseAgent with READ_ONLY + FILE_EDIT capabilities.
    It analyzes Python code structure using AST and generates structured docs.

Philosophy (Boris Cherny):
    "Code tells you how. Documentation tells you why."
"""

import ast
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from vertice_core.utils import MarkdownExtractor

from ..base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)

from .models import DocFormat, DocstringStyle, ModuleDoc
from .analyzers import analyze_module, analyze_class, analyze_function
from .generators import generate_markdown, generate_api_reference, generate_readme_content
from .validators import validate_docstrings
from .sync_api import DocumentationSyncAPI

# FIX E2E: Import grounding prompts for anti-hallucination
try:
    from vertice_core.prompts.grounding import GROUNDING_INSTRUCTION, INLINE_CODE_PRIORITY
except ImportError:
    GROUNDING_INSTRUCTION = ""
    INLINE_CODE_PRIORITY = ""

# FIX E2E: Import temperature config
try:
    from vertice_core.core.temperature_config import get_temperature
except ImportError:

    def get_temperature(agent_type: str, task_type: str = None) -> float:
        return 0.4  # Documentation default


logger = logging.getLogger(__name__)


class DocumentationAgent(BaseAgent):
    """The Technical Writer - Documentation Excellence Specialist.

    This agent analyzes code structure and generates professional documentation
    in multiple formats. It validates existing docstrings, suggests improvements,
    and creates new documentation from scratch.

    Capabilities:
        - READ_ONLY: Analyze code structure
        - FILE_EDIT: Generate documentation files

    Attributes:
        role: AgentRole.DOCUMENTATION (custom extension)
        capabilities: READ_ONLY + FILE_EDIT
    """

    def __init__(self, llm_client: Optional[Any] = None, mcp_client: Optional[Any] = None):
        """Initialize DocumentationAgent.

        Args:
            llm_client: LLM provider client (e.g., Anthropic, OpenAI)
            mcp_client: MCP client for tool execution

        Raises:
            ValueError: If clients are None
        """
        if llm_client is None:
            raise ValueError("llm_client is required for DocumentationAgent")
        if mcp_client is None:
            raise ValueError("mcp_client is required for DocumentationAgent")

        super().__init__(
            role=AgentRole.DOCUMENTATION,
            capabilities=[AgentCapability.READ_ONLY, AgentCapability.FILE_EDIT],
            llm_client=llm_client,
            mcp_client=mcp_client,
        )

        # Sync API wrapper for testing
        self._sync_api = DocumentationSyncAPI(llm_client)

    def _extract_code_blocks(self, text: str) -> str:
        """Extract code from markdown code blocks or inline in user message.

        Following Claude Code pattern: check inline content FIRST before using tools.
        Uses unified MarkdownExtractor from vertice_core.utils.

        Args:
            text: User message or context text that may contain code

        Returns:
            Extracted code as string, empty if no code found
        """
        if not text:
            return ""

        extractor = MarkdownExtractor(deduplicate=True)
        blocks = extractor.extract_code_blocks(text)

        return "\n\n".join(block.content for block in blocks)

    async def _document_inline_code(self, code: str, style: DocstringStyle) -> AgentResponse:
        """Document inline code provided in user message.

        Args:
            code: Inline code to document
            style: Docstring style to use

        Returns:
            AgentResponse with generated documentation
        """
        try:
            tree = ast.parse(code)

            module_doc = ModuleDoc(
                name="inline_code",
                docstring=None,
                classes=[],
                functions=[],
                imports=[],
                file_path="<inline>",
            )

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    module_doc.classes.append(analyze_class(node))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    module_doc.functions.append(analyze_function(node))

            documentation = generate_markdown(module_doc, style)

            return AgentResponse(
                success=True,
                data={
                    "documentation": documentation,
                    "source": "inline_code",
                    "classes": len(module_doc.classes),
                    "functions": len(module_doc.functions),
                    "code_analyzed": code[:500],
                },
                reasoning=f"Analyzed inline code: {len(module_doc.classes)} classes, "
                f"{len(module_doc.functions)} functions",
            )
        except SyntaxError:
            return AgentResponse(
                success=True,
                data={
                    "documentation": f"# Code Documentation\n\n```python\n{code}\n```\n\n"
                    "*Note: Code contains syntax errors, showing raw content.*",
                    "source": "inline_code_raw",
                    "code_analyzed": code[:500],
                },
                reasoning="Code contains syntax errors, documented as raw content",
            )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute documentation generation task.

        Priority order for code sources (Claude Code pattern):
            1. HIGHEST: Inline code in user_message
            2. HIGH: files_list in context
            3. MEDIUM: file_path in context
            4. LOWEST: target_path for directory scan

        Args:
            task: Task containing request and context

        Returns:
            AgentResponse with documentation results
        """
        try:
            style = task.context.get("style", DocstringStyle.GOOGLE)

            # PRIORITY 1: Check for inline code in user message
            user_message = task.context.get("user_message", "")
            inline_code = self._extract_code_blocks(user_message)

            if inline_code:
                return await self._document_inline_code(inline_code, style)

            # PRIORITY 2: Check files_list in context
            files_list = task.context.get("files_list", []) or task.context.get("files", [])

            # PRIORITY 3: Check file_path in context
            single_file_path = task.context.get("file_path", "")
            if single_file_path and not files_list:
                files_list = [single_file_path]

            # PRIORITY 4: Fall back to target_path for scan
            target_path_str = task.context.get("target_path", "")

            if files_list and not target_path_str:
                first_file = Path(files_list[0])
                target_path = first_file.parent if first_file.exists() else Path(".")
            else:
                target_path = Path(target_path_str) if target_path_str else Path(".")

            doc_format = task.context.get("format", DocFormat.MARKDOWN)
            output_path = task.context.get("output_path")

            # Route to appropriate handler
            request_lower = task.request.lower()
            if any(kw in request_lower for kw in ["generate_docs", "documentation", "docstring"]):
                return await self._generate_docs(
                    target_path, doc_format, style, output_path, files_list
                )
            elif "validate" in request_lower:
                return await self._validate_docstrings(target_path, style)
            elif "readme" in request_lower:
                return await self._create_readme(target_path, output_path)
            else:
                return await self._generate_docs(
                    target_path, doc_format, style, output_path, files_list
                )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Documentation generation failed: {str(e)}",
                reasoning="Unexpected error during execution",
            )

    async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Stream documentation generation with progressive updates.

        Yields status updates as documentation is generated.

        Args:
            task: Task containing request and context

        Yields:
            StreamingChunk dicts with progress updates
        """
        from vertice_core.agents.protocol import StreamingChunk, StreamingChunkType

        try:
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="📝 DocumentationAgent starting..."
            ).to_dict()

            style = task.context.get("style", DocstringStyle.GOOGLE)

            # Check for inline code
            user_message = task.context.get("user_message", "")
            inline_code = self._extract_code_blocks(user_message)

            if inline_code:
                yield StreamingChunk(
                    type=StreamingChunkType.STATUS, data="📋 Found inline code, analyzing..."
                ).to_dict()

                result = await self._document_inline_code(inline_code, style)
                yield StreamingChunk(type=StreamingChunkType.RESULT, data=result.data).to_dict()
                return

            # Get files to document
            files_list = task.context.get("files_list", []) or task.context.get("files", [])
            target_path_str = task.context.get("target_path", "")

            if files_list:
                target_path = (
                    Path(files_list[0]).parent if Path(files_list[0]).exists() else Path(".")
                )
            else:
                target_path = Path(target_path_str) if target_path_str else Path(".")

            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data=f"📁 Scanning {target_path}..."
            ).to_dict()

            # Find Python files
            if files_list:
                python_files = [
                    Path(f) for f in files_list if f.endswith(".py") and Path(f).exists()
                ]
            elif target_path.is_file():
                python_files = [target_path]
            else:
                python_files = list(target_path.rglob("*.py"))[:20]

            yield StreamingChunk(
                type=StreamingChunkType.THINKING, data=f"Found {len(python_files)} Python files\n"
            ).to_dict()

            # Analyze each file
            modules: List[ModuleDoc] = []
            for i, py_file in enumerate(python_files[:10]):
                if "__pycache__" in str(py_file):
                    continue

                yield StreamingChunk(
                    type=StreamingChunkType.THINKING, data=f"  - Analyzing `{py_file.name}`...\n"
                ).to_dict()

                try:
                    module_doc = analyze_module(py_file)
                    modules.append(module_doc)
                except (SyntaxError, OSError):
                    continue

            # Generate docs
            yield StreamingChunk(
                type=StreamingChunkType.STATUS, data="✨ Generating documentation..."
            ).to_dict()

            yield StreamingChunk(
                type=StreamingChunkType.VERDICT, data=f"\n\n✅ Documented {len(modules)} modules"
            ).to_dict()

            yield StreamingChunk(
                type=StreamingChunkType.RESULT,
                data={"modules_analyzed": len(modules), "files_found": len(python_files)},
            ).to_dict()

        except Exception as e:
            yield StreamingChunk(
                type=StreamingChunkType.ERROR, data=f"Documentation failed: {str(e)}"
            ).to_dict()

    async def _generate_docs(
        self,
        target_path: Path,
        doc_format: DocFormat,
        style: DocstringStyle,
        output_path: Optional[str],
        files_list: Optional[List[str]] = None,
    ) -> AgentResponse:
        """Generate documentation for target path."""
        modules: List[ModuleDoc] = []
        files_created: List[str] = []

        # Find all Python files
        if files_list:
            python_files = [Path(f) for f in files_list if f.endswith(".py") and Path(f).exists()]
        elif target_path.is_file():
            python_files = [target_path]
        else:
            python_files = list(target_path.rglob("*.py"))

        # Analyze each module
        for py_file in python_files:
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            try:
                module_doc = analyze_module(py_file)
                modules.append(module_doc)
            except (SyntaxError, OSError) as e:
                logger.debug(f"Skipping {py_file} due to error: {e}")
                continue

        # Fallback for syntax errors
        if not modules and python_files:
            for py_file in python_files[:5]:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    modules.append(
                        ModuleDoc(
                            name=py_file.stem,
                            classes=[],
                            functions=[],
                            imports=[],
                            file_path=str(py_file),
                            docstring=f"**Raw Content Preview**:\n\n```python\n{content[:2000]}\n```",
                        )
                    )
                except OSError as e:
                    logger.debug(f"Could not read {py_file}: {e}")

        # Generate documentation files
        if output_path:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            if doc_format == DocFormat.MARKDOWN:
                for module_doc in modules:
                    md_content = generate_markdown(module_doc, style)
                    md_file = output_dir / f"{module_doc.name}.md"
                    await self._execute_tool(
                        "write_file",
                        {"path": str(md_file), "content": md_content},
                    )
                    files_created.append(str(md_file))

            elif doc_format == DocFormat.API_REFERENCE:
                api_ref = generate_api_reference(modules)
                api_file = output_dir / "API_REFERENCE.md"
                await self._execute_tool(
                    "write_file",
                    {"path": str(api_file), "content": api_ref},
                )
                files_created.append(str(api_file))

        # Generate documentation content for display
        doc_content_parts = []
        for module_doc in modules[:5]:
            md_content = generate_markdown(module_doc, style)
            doc_content_parts.append(md_content)

        documentation = "\n\n---\n\n".join(doc_content_parts)

        return AgentResponse(
            success=True,
            data={
                "documentation": documentation,
                "modules": [
                    {
                        "name": m.name,
                        "classes": len(m.classes),
                        "functions": len(m.functions),
                        "docstring": m.docstring[:200] if m.docstring else None,
                    }
                    for m in modules
                ],
                "files_created": files_created,
                "total_modules": len(modules),
            },
            reasoning=f"Analyzed {len(modules)} modules, generated documentation",
        )

    async def _validate_docstrings(self, target_path: Path, style: DocstringStyle) -> AgentResponse:
        """Validate existing docstrings against style guide."""
        result = validate_docstrings(target_path, style)

        return AgentResponse(
            success=True,
            data=result,
            reasoning=f"Found {result['total_issues']} docstring issues",
        )

    async def _create_readme(self, target_path: Path, output_path: Optional[str]) -> AgentResponse:
        """Generate README.md for project/module."""
        modules = []
        python_files = list(target_path.rglob("*.py"))

        for py_file in python_files[:10]:
            if "__pycache__" not in str(py_file):
                try:
                    modules.append(analyze_module(py_file))
                except (SyntaxError, OSError) as e:
                    logger.debug(f"Could not analyze {py_file}: {e}")
                    continue

        readme_content = generate_readme_content(target_path, modules)

        readme_file = Path(output_path) if output_path else target_path / "README.md"
        await self._execute_tool(
            "write_file",
            {"path": str(readme_file), "content": readme_content},
        )

        return AgentResponse(
            success=True,
            data={"readme_path": str(readme_file), "modules_analyzed": len(modules)},
            reasoning=f"Generated README.md with {len(modules)} modules documented",
        )

    # Sync API delegation methods
    def generate_documentation(
        self, code: str, doc_type: str = "function", style: str = "google"
    ) -> Dict[str, Any]:
        """Generate documentation for code snippet (SYNC wrapper)."""
        return self._sync_api.generate_documentation(code, doc_type, style)

    def generate_api_docs(self, code: str, api_type: str = "rest") -> Dict[str, Any]:
        """Generate API documentation (SYNC wrapper)."""
        return self._sync_api.generate_api_docs(code, api_type)

    def generate_readme(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate README for project (SYNC wrapper)."""
        return self._sync_api.generate_readme(project_info)


def create_documentation_agent(
    llm_client: Any,
    mcp_client: Any,
) -> DocumentationAgent:
    """Factory function to create DocumentationAgent.

    Args:
        llm_client: LLM provider client
        mcp_client: MCP client for tools

    Returns:
        Configured DocumentationAgent instance
    """
    return DocumentationAgent(llm_client=llm_client, mcp_client=mcp_client)


__all__ = [
    "DocumentationAgent",
    "create_documentation_agent",
]
