"""
Tool Catalog - Unified Tool Registry Builder.
=============================================

Single source of truth for all tools in the system.
Replaces registry_helper.py and logic in tools_bridge.py.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Type

from vertice_cli.tools.base import ToolRegistry, BaseTool

# 1. File Operations (12 tools)
from vertice_cli.tools.file_ops import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from vertice_cli.tools.file_mgmt import (
    MoveFileTool,
    CopyFileTool,
    CreateDirectoryTool,
    ReadMultipleFilesTool,
    InsertLinesTool,
)

# 2. Terminal (9 tools)
from vertice_cli.tools.terminal import (
    CdTool,
    LsTool,
    PwdTool,
    MkdirTool,
    RmTool,
    CpTool,
    MvTool,
    TouchTool,
    CatTool,
)

# 3. Execution (1 tool)
from vertice_cli.tools.exec_hardened import BashCommandTool

# 4. Search (2 tools)
from vertice_cli.tools.search import SearchFilesTool, GetDirectoryTreeTool

# 5. Git (2 tools)
from vertice_cli.tools.git_ops import GitStatusTool, GitDiffTool

# 6. Context (3 tools)
from vertice_cli.tools.context import (
    GetContextTool,
    SaveSessionTool,
    RestoreBackupTool,
)

logger = logging.getLogger(__name__)


class ToolCatalog:
    """Builder for ToolRegistry with configurable categories."""

    def __init__(self):
        self.registry = ToolRegistry()
        self.load_errors: List[str] = []

    def add_defaults(self) -> "ToolCatalog":
        """Add standard file, terminal, execution, search, git, and context tools."""
        tools = [
            # File Ops
            ReadFileTool,
            WriteFileTool,
            EditFileTool,
            ListDirectoryTool,
            DeleteFileTool,
            MoveFileTool,
            CopyFileTool,
            CreateDirectoryTool,
            ReadMultipleFilesTool,
            InsertLinesTool,
            # Terminal
            CdTool,
            LsTool,
            PwdTool,
            MkdirTool,
            RmTool,
            CpTool,
            MvTool,
            TouchTool,
            CatTool,
            # Execution
            BashCommandTool,
            # Search
            SearchFilesTool,
            GetDirectoryTreeTool,
            # Git
            GitStatusTool,
            GitDiffTool,
            # Context
            GetContextTool,
            SaveSessionTool,
            RestoreBackupTool,
        ]
        self._register_batch("defaults", tools)
        return self

    def add_web_tools(self) -> "ToolCatalog":
        """Add web search and access tools."""
        try:
            from vertice_cli.tools.web_search import WebSearchTool, SearchDocumentationTool
            from vertice_cli.tools.web_access import (
                FetchURLTool,
                DownloadFileTool,
                HTTPRequestTool,
                PackageSearchTool,
            )

            tools = [
                WebSearchTool,
                SearchDocumentationTool,
                FetchURLTool,
                DownloadFileTool,
                HTTPRequestTool,
                PackageSearchTool,
            ]
            self._register_batch("web", tools)
        except ImportError as e:
            self.load_errors.append(f"web tools: {e}")
        return self

    def add_parity_tools(self) -> "ToolCatalog":
        """Add Claude Code parity tools."""
        try:
            from vertice_cli.tools.claude_parity_tools import get_claude_parity_tools

            for tool in get_claude_parity_tools():
                try:
                    self.registry.register(tool)
                except Exception as e:
                    self.load_errors.append(f"parity tool {tool.name}: {e}")
        except ImportError as e:
            self.load_errors.append(f"parity tools: {e}")
        return self

    def add_prometheus_tools(self, provider=None) -> "ToolCatalog":
        """Add Prometheus meta-agent tools."""
        try:
            if provider is None:
                # Try to auto-initialize if not provided
                from vertice_cli.core.providers.prometheus_provider import (
                    PrometheusProvider,
                )

                try:
                    provider = PrometheusProvider()
                except Exception as e:
                    # If provider init fails (e.g. no key), skip silently or log
                    logger.debug(f"PrometheusProvider auto-init failed: {e}")
                    return self

            from vertice_cli.tools.prometheus_tools import (
                PrometheusExecuteTool,
                PrometheusMemoryQueryTool,
                PrometheusSimulateTool,
                PrometheusEvolveTool,
                PrometheusReflectTool,
                PrometheusCreateToolTool,
                PrometheusGetStatusTool,
                PrometheusBenchmarkTool,
            )

            # These are instantiated with the provider
            tools = [
                PrometheusExecuteTool(provider),
                PrometheusMemoryQueryTool(provider),
                PrometheusSimulateTool(provider),
                PrometheusEvolveTool(provider),
                PrometheusReflectTool(provider),
                PrometheusCreateToolTool(provider),
                PrometheusGetStatusTool(provider),
                PrometheusBenchmarkTool(provider),
            ]

            for tool in tools:
                self.registry.register(tool)

        except ImportError as e:
            self.load_errors.append(f"prometheus tools: {e}")
        except Exception as e:
            self.load_errors.append(f"prometheus init: {e}")
        return self

    def add_git_mutation_tools(self) -> "ToolCatalog":
        """Add git mutation tools (commit, push, checkout, branch, pr)."""
        try:
            from vertice_cli.tools.git.mutate_tools import get_git_mutate_tools

            # get_git_mutate_tools returns instances, so we register directly
            for tool in get_git_mutate_tools():
                try:
                    self.registry.register(tool)
                except Exception as e:
                    self.load_errors.append(f"git_mutate/{tool.name}: {e}")

        except ImportError as e:
            self.load_errors.append(f"git mutation tools: {e}")
        return self

    def build(self) -> ToolRegistry:
        """Return the constructed registry."""
        if self.load_errors:
            logger.warning(f"ToolCatalog load errors: {self.load_errors}")
        return self.registry

    def _register_batch(self, category: str, tool_classes: List[Type[BaseTool]]) -> None:
        """Helper to register a batch of tool classes."""
        for tool_cls in tool_classes:
            try:
                self.registry.register(tool_cls())
            except Exception as e:
                self.load_errors.append(f"{category}/{tool_cls.__name__}: {e}")


def get_catalog(
    include_web: bool = False,
    include_parity: bool = False,
    include_prometheus: bool = False,
    include_git_mutate: bool = False,
    prometheus_provider: Optional[Any] = None,
) -> ToolRegistry:
    """Convenience factory function."""
    catalog = ToolCatalog().add_defaults()

    if include_web:
        catalog.add_web_tools()

    if include_parity:
        catalog.add_parity_tools()

    if include_git_mutate:
        catalog.add_git_mutation_tools()

    if include_prometheus:
        catalog.add_prometheus_tools(prometheus_provider)

    return catalog.build()
