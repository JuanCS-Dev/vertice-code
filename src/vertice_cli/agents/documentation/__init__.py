"""
Documentation Module - Technical Writing Excellence.

This module provides comprehensive documentation generation capabilities:
- AST-based code analysis
- Multi-format documentation (Markdown, API Reference, README)
- Docstring validation (Google, NumPy, Sphinx styles)
- Inline code documentation

Architecture:
    - models.py: Type-safe data structures
    - analyzers.py: AST-based code analysis
    - generators.py: Multi-format documentation generators
    - validators.py: Docstring style validation
    - sync_api.py: Synchronous API wrappers
    - agent.py: DocumentationAgent orchestrator

Usage:
    from vertice_cli.agents.documentation import DocumentationAgent, create_documentation_agent

    agent = create_documentation_agent(llm_client, mcp_client)
    response = await agent.execute(task)

Philosophy (Boris Cherny):
    "Code tells you how. Documentation tells you why."
"""

# Models
from .models import (
    DocFormat,
    DocstringStyle,
    FunctionDoc,
    ClassDoc,
    ModuleDoc,
)

# Analyzers
from .analyzers import (
    analyze_module,
    analyze_class,
    analyze_function,
)

# Generators
from .generators import (
    generate_markdown,
    generate_api_reference,
    generate_readme_content,
)

# Validators
from .validators import (
    validate_docstrings,
    check_google_style,
    contains_secrets,
    GOOGLE_DOCSTRING_PATTERN,
    SECRET_PATTERNS,
)

# Sync API
from .sync_api import DocumentationSyncAPI

# Agent
from .agent import (
    DocumentationAgent,
    create_documentation_agent,
)

__all__ = [
    # Models
    "DocFormat",
    "DocstringStyle",
    "FunctionDoc",
    "ClassDoc",
    "ModuleDoc",
    # Analyzers
    "analyze_module",
    "analyze_class",
    "analyze_function",
    # Generators
    "generate_markdown",
    "generate_api_reference",
    "generate_readme_content",
    # Validators
    "validate_docstrings",
    "check_google_style",
    "contains_secrets",
    "GOOGLE_DOCSTRING_PATTERN",
    "SECRET_PATTERNS",
    # Sync API
    "DocumentationSyncAPI",
    # Agent
    "DocumentationAgent",
    "create_documentation_agent",
]
