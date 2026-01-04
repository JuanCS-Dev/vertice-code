"""
Code Agent Formatters - Testing, Refactoring, and Documentation.

Specialized formatters for code-related agent outputs.
"""

from typing import Any, AsyncIterator


class TestingFormatter:
    """
    Format TestingAgent generated test case outputs.

    Expected data structure:
        {
            "test_cases": List[{
                "name": str,
                "code": str
            }],
            "total_assertions": int
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains generated test cases ('test_cases' key)."""
        return isinstance(data, dict) and "test_cases" in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format test cases with Python code blocks (limited to 10)."""
        yield "## Generated Test Cases\n\n"

        for tc in data["test_cases"][:10]:
            yield f"### {tc.get('name', 'test')}\n"
            yield f"```python\n{tc.get('code', '')}\n```\n\n"

        if data.get("total_assertions"):
            yield f"*Total assertions: {data['total_assertions']}*\n"


class RefactorerFormatter:
    """
    Format RefactorerAgent code analysis and suggestion outputs.

    Expected data structure:
        {
            "analysis": str,
            "refactoring_suggestions": List[{
                "type": str,
                "description": str
            }]
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains refactoring analysis ('analysis' key)."""
        return isinstance(data, dict) and "analysis" in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format refactoring analysis with typed suggestions."""
        yield "## Refactoring Analysis\n\n"
        yield f"*{reasoning}*\n\n"

        analysis = data.get("analysis", "")
        if analysis:
            yield analysis
            yield "\n"

        suggestions = data.get("refactoring_suggestions", [])
        if suggestions:
            yield "\n### Suggested Refactorings\n\n"
            for s in suggestions:
                yield f"- **{s.get('type', 'unknown')}**: {s.get('description', '')}\n"


class DocumentationFormatter:
    """
    Format DocumentationAgent generated documentation outputs.

    Expected data structure:
        {
            "documentation": str,
            "modules": List[{
                "name": str,
                "classes": int,
                "functions": int
            }]
        }
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains generated documentation ('documentation' key)."""
        return isinstance(data, dict) and "documentation" in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format documentation with optional module analysis (limited to 10)."""
        yield "## Generated Documentation\n\n"
        yield f"*{reasoning}*\n\n"

        documentation = data.get("documentation", "")
        if documentation:
            yield documentation
            yield "\n"

        modules = data.get("modules", [])
        if modules:
            yield f"\n### Modules Analyzed ({len(modules)})\n\n"
            for m in modules[:10]:
                name = m.get("name", "unknown")
                classes = m.get("classes", 0)
                functions = m.get("functions", 0)
                yield f"- **{name}**: {classes} classes, {functions} functions\n"
