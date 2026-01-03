"""
Documentation Generators - Multi-format Documentation Generation.

Provides generators for different documentation formats:
- Markdown (GitHub-flavored)
- API Reference
- README files

Philosophy:
    "Good documentation tells the story of your code."
"""

from pathlib import Path
from typing import List

from .models import DocstringStyle, ModuleDoc


def generate_markdown(module_doc: ModuleDoc, style: DocstringStyle) -> str:
    """Generate Markdown documentation for module.

    Args:
        module_doc: Analyzed module documentation
        style: Docstring style (not used for Markdown, but kept for consistency)

    Returns:
        Markdown-formatted documentation string
    """
    lines = [f"# {module_doc.name}", ""]

    if module_doc.docstring:
        lines.extend([module_doc.docstring, ""])

    # Table of contents
    if module_doc.classes or module_doc.functions:
        lines.append("## Table of Contents")
        lines.append("")

        if module_doc.classes:
            lines.append("### Classes")
            for cls in module_doc.classes:
                lines.append(f"- [{cls.name}](#{cls.name.lower()})")
            lines.append("")

        if module_doc.functions:
            lines.append("### Functions")
            for func in module_doc.functions:
                lines.append(f"- [{func.name}](#{func.name.lower()})")
            lines.append("")

    # Classes
    for cls in module_doc.classes:
        lines.extend([f"## {cls.name}", ""])

        if cls.bases:
            lines.append(f"**Inherits from:** `{', '.join(cls.bases)}`")
            lines.append("")

        if cls.docstring:
            lines.extend([cls.docstring, ""])

        # Methods
        if cls.methods:
            lines.append("### Methods")
            lines.append("")
            for method in cls.methods:
                lines.append(f"#### `{method.signature}`")
                lines.append("")
                if method.docstring:
                    lines.append("**Docstring:**")
                    lines.extend([method.docstring, ""])
                # Add params and return info
                if method.parameters:
                    lines.append("**Parameters:**")
                    for param in method.parameters:
                        desc = f" - {param[2]}" if len(param) > 2 and param[2] else ""
                        lines.append(f"- `{param[0]}`: {param[1]}{desc}")
                    lines.append("")
                if method.returns and method.returns[0]:
                    lines.append(f"**Returns:** `{method.returns[0]}`")
                    if method.returns[1]:
                        lines.append(f"  {method.returns[1]}")
                    lines.append("")

    # Standalone functions
    if module_doc.functions:
        lines.append("## Functions")
        lines.append("")

        for func in module_doc.functions:
            lines.append(f"### `{func.signature}`")
            lines.append("")
            if func.docstring:
                lines.append("**Docstring:**")
                lines.extend([func.docstring, ""])
            # Add params and return info
            if func.parameters:
                lines.append("**Parameters:**")
                for param in func.parameters:
                    desc = f" - {param[2]}" if len(param) > 2 and param[2] else ""
                    lines.append(f"- `{param[0]}`: {param[1]}{desc}")
                lines.append("")
            if func.returns and func.returns[0]:
                lines.append(f"**Returns:** `{func.returns[0]}`")
                if func.returns[1]:
                    lines.append(f"  {func.returns[1]}")
                lines.append("")

    return "\n".join(lines)


def generate_api_reference(modules: List[ModuleDoc]) -> str:
    """Generate comprehensive API reference.

    Args:
        modules: List of analyzed modules

    Returns:
        Markdown-formatted API reference
    """
    lines = ["# API Reference", "", "Auto-generated API documentation.", ""]

    for module in modules:
        lines.extend([f"## {module.name}", ""])

        if module.docstring:
            lines.extend([module.docstring, ""])

        # Classes summary
        if module.classes:
            lines.append("### Classes")
            lines.append("")
            for cls in module.classes:
                desc = cls.docstring.split('.')[0] if cls.docstring else 'No description'
                lines.append(f"- **{cls.name}**: {desc}")
            lines.append("")

        # Functions summary
        if module.functions:
            lines.append("### Functions")
            lines.append("")
            for func in module.functions:
                desc = func.docstring.split('.')[0] if func.docstring else 'No description'
                lines.append(f"- **{func.name}**: {desc}")
            lines.append("")

    return "\n".join(lines)


def generate_readme_content(
    project_path: Path, modules: List[ModuleDoc]
) -> str:
    """Generate README.md content.

    Args:
        project_path: Root project directory
        modules: List of analyzed modules

    Returns:
        README.md content
    """
    project_name = project_path.name

    lines = [
        f"# {project_name}",
        "",
        "## Overview",
        "",
        "Auto-generated project documentation.",
        "",
        "## Project Structure",
        "",
        "```",
    ]

    # Simple directory tree
    for module in modules[:20]:  # Limit to 20
        lines.append(f"├── {module.name}.py")

    lines.extend([
        "```",
        "",
        "## Modules",
        "",
    ])

    for module in modules:
        lines.append(f"### {module.name}")
        lines.append("")
        if module.docstring:
            lines.append(module.docstring.split("\n")[0])
            lines.append("")

    lines.extend([
        "## Installation",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "```",
        "",
        "## Usage",
        "",
        "```python",
        f"from {project_name} import ...",
        "```",
        "",
        "## License",
        "",
        "MIT License",
    ])

    return "\n".join(lines)


__all__ = [
    "generate_markdown",
    "generate_api_reference",
    "generate_readme_content",
]
