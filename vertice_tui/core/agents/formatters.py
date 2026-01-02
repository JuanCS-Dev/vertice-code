"""
Agent Result Formatters - Strategy pattern for agent output formatting.

SCALE & SUSTAIN Phase 3.2 - Nesting Flattening.

Extracted from manager.py:_format_agent_result (270 lines, 16 levels nesting)
to eliminate deep nesting via Strategy pattern.

Each formatter handles a specific agent type with max 3 levels of nesting.

Author: Vertice Team
Date: 2026-01-02
"""

from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol


class ResultFormatter(Protocol):
    """Protocol for agent result formatters."""

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if this formatter can handle the data."""
        ...

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format the data into markdown chunks."""
        ...


# =============================================================================
# HELPER FUNCTIONS (shared by formatters)
# =============================================================================

def get_severity_emoji(severity: str) -> str:
    """Map severity to emoji."""
    return {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "INFO": "ℹ️"
    }.get(severity, "⚪")


def format_list_items(items: List[Any], prefix: str = "- ") -> str:
    """Format list items with prefix."""
    return "".join(f"{prefix}{item}\n" for item in items)


async def yield_dict_items(
    data: Dict[str, Any],
    keys: List[str],
    headers: Optional[Dict[str, str]] = None
) -> AsyncIterator[str]:
    """Yield formatted dict items for given keys."""
    headers = headers or {}
    for key in keys:
        value = data.get(key)
        if not value:
            continue
        header = headers.get(key, f"**{key.title()}:**")
        if isinstance(value, list):
            yield f"\n{header}\n"
            for item in value:
                yield f"- {item}\n"
        else:
            yield f"{header} {value}\n"


# =============================================================================
# SPECIALIZED FORMATTERS
# =============================================================================

class ArchitectFormatter:
    """Format ArchitectAgent decisions."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'decision' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        decision = data.get('decision', 'UNKNOWN')
        emoji = "✅" if decision == "APPROVED" else "❌"
        yield f"{emoji} **{decision}**\n\n"
        yield f"*{reasoning}*\n"

        arch = data.get('architecture', {})
        if arch.get('approach'):
            yield f"\n**Approach:** {arch['approach']}\n"
        if arch.get('risks'):
            yield f"\n**Risks:** {', '.join(arch['risks'])}\n"
        if arch.get('estimated_complexity'):
            yield f"\n**Complexity:** {arch['estimated_complexity']}\n"

        recommendations = data.get('recommendations', [])
        if recommendations:
            yield "\n**Recommendations:**\n"
            for rec in recommendations:
                yield f"- {rec}\n"


class ReviewerFormatter:
    """Format ReviewerAgent / SecurityAgent results."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'report' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        report = data['report']
        yield f"## Code Review Report\n\n"
        yield f"*{reasoning}*\n\n"

        if isinstance(report, str):
            async for chunk in ReviewerFormatter._format_string_report(data, report):
                yield chunk
        elif isinstance(report, dict):
            async for chunk in ReviewerFormatter._format_dict_report(data, report):
                yield chunk

    @staticmethod
    async def _format_string_report(data: Dict, report: str) -> AsyncIterator[str]:
        """Format string report (SecurityAgent style)."""
        yield report
        yield "\n"

        vulns = data.get('vulnerabilities', [])
        if not vulns:
            return

        yield "\n### Vulnerabilities Detail\n\n"
        for vuln in vulns[:15]:
            severity = vuln.get('severity', 'MEDIUM')
            vuln_type = vuln.get('vulnerability_type', 'unknown')
            desc = vuln.get('description', 'No description')
            emoji = get_severity_emoji(severity)
            yield f"- {emoji} **[{severity}]** {vuln_type}: {desc}\n"

            file_path = vuln.get('file', '')
            if file_path:
                yield f"  📍 `{file_path}:{vuln.get('line', '')}`\n"

    @staticmethod
    async def _format_dict_report(data: Dict, report: Dict) -> AsyncIterator[str]:
        """Format dict report (ReviewerAgent style)."""
        # Quality score
        score = report.get('quality_score')
        if score is not None:
            emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            yield f"### {emoji} Quality Score: {score}/100\n\n"

        if report.get('risk_level'):
            yield f"**Risk Level:** {report['risk_level']}\n\n"

        # Issues
        issues = report.get('issues', [])
        if issues:
            async for chunk in ReviewerFormatter._format_issues(issues):
                yield chunk
        else:
            yield "✅ No issues found!\n"

        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            yield f"\n### Recommendations\n\n"
            for rec in recommendations[:10]:
                yield f"- {rec}\n"

        if report.get('estimated_fix_time'):
            yield f"\n⏱️ Estimated fix time: {report['estimated_fix_time']}\n"

    @staticmethod
    async def _format_issues(issues: List[Dict]) -> AsyncIterator[str]:
        """Format issues list."""
        yield f"### Issues Found ({len(issues)})\n\n"
        for i, issue in enumerate(issues[:20], 1):
            severity = issue.get('severity', 'MEDIUM')
            message = issue.get('message', 'No description')
            file_path = issue.get('file', '')
            line = issue.get('line', '')

            location = f" at `{file_path}:{line}`" if file_path and line else ""
            emoji = get_severity_emoji(severity)
            yield f"{i}. {emoji} **[{severity}]** {message}{location}\n"

            fix = issue.get('fix_suggestion') or issue.get('suggestion')
            if fix:
                yield f"   💡 *{fix}*\n"


class ExplorerFormatter:
    """Format ExplorerAgent results."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'relevant_files' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        if data.get('context_summary'):
            yield f"{data['context_summary']}\n\n"

        relevant_files = data.get('relevant_files', [])
        if relevant_files:
            yield "**Relevant Files:**\n"
            async for chunk in ExplorerFormatter._format_files(relevant_files):
                yield chunk
        else:
            yield "⚠️ No relevant files found for this query.\n"

        # Dependencies
        deps = data.get('dependencies', [])
        if deps:
            yield "\n**Dependencies:**\n"
            for d in deps:
                if isinstance(d, dict):
                    yield f"- `{d.get('from', '')}` → `{d.get('to', '')}` ({d.get('type', '')})\n"
                else:
                    yield f"- {d}\n"

        if data.get('token_estimate'):
            yield f"\n📊 *Token estimate: ~{data['token_estimate']} tokens*\n"

    @staticmethod
    async def _format_files(files: List[Any]) -> AsyncIterator[str]:
        """Format file list with optional snippets."""
        for f in files:
            if isinstance(f, dict):
                path = f.get('path', 'unknown')
                relevance = f.get('relevance', '')
                reason = f.get('reason', '')

                relevance_badge = f" [{relevance}]" if relevance else ""
                reason_text = f" - {reason}" if reason else ""
                yield f"- `{path}`{relevance_badge}{reason_text}\n"

                snippet = f.get('snippet', '')
                if snippet:
                    preview = snippet[:200].strip()
                    if len(snippet) > 200:
                        preview += "..."
                    yield f"  ```\n  {preview}\n  ```\n"
            else:
                yield f"- `{f}`\n"


class DevOpsFormatter:
    """Format DevOps deployment plans."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'plan' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield f"## DevOps Deployment Plan\n\n"
        yield f"*{reasoning}*\n\n"

        plan = data['plan']
        if isinstance(plan, dict):
            async for chunk in DevOpsFormatter._format_plan_dict(plan):
                yield chunk
        else:
            yield str(plan)

        if data.get('status'):
            yield f"\n**Status:** {data['status']}\n"

        # Infrastructure
        async for chunk in DevOpsFormatter._format_section(data, 'infrastructure', 'Infrastructure'):
            yield chunk

        # Configuration
        async for chunk in DevOpsFormatter._format_section(data, 'configuration', 'Configuration'):
            yield chunk

    @staticmethod
    async def _format_plan_dict(plan: Dict) -> AsyncIterator[str]:
        """Format plan dictionary."""
        if plan.get('deployment_id'):
            yield f"**Deployment ID:** {plan['deployment_id']}\n"
        if plan.get('strategy'):
            yield f"**Strategy:** {plan['strategy']}\n"

        for section, title in [
            ('pre_checks', 'Pre-Checks'),
            ('deployment_steps', 'Deployment Steps'),
            ('post_checks', 'Post-Checks')
        ]:
            items = plan.get(section, [])
            if items:
                yield f"\n**{title}:**\n"
                for item in items:
                    yield f"- {item}\n"

    @staticmethod
    async def _format_section(data: Dict, key: str, title: str) -> AsyncIterator[str]:
        """Format a key-value section."""
        section = data.get(key)
        if not section:
            return
        yield f"\n**{title}:**\n"
        for k, v in section.items():
            yield f"- {k}: {v}\n"


class DevOpsResponseFormatter:
    """Format DevOps LLM response."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'response' in data and 'plan' not in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield data['response']


class TestingFormatter:
    """Format TestingAgent results."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'test_cases' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield f"## Generated Test Cases\n\n"

        for tc in data['test_cases'][:10]:
            yield f"### {tc.get('name', 'test')}\n"
            yield f"```python\n{tc.get('code', '')}\n```\n\n"

        if data.get('total_assertions'):
            yield f"*Total assertions: {data['total_assertions']}*\n"


class RefactorerFormatter:
    """Format RefactorerAgent results."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'analysis' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield f"## Refactoring Analysis\n\n"
        yield f"*{reasoning}*\n\n"

        analysis = data.get('analysis', '')
        if analysis:
            yield analysis
            yield "\n"

        suggestions = data.get('refactoring_suggestions', [])
        if suggestions:
            yield "\n### Suggested Refactorings\n\n"
            for s in suggestions:
                yield f"- **{s.get('type', 'unknown')}**: {s.get('description', '')}\n"


class DocumentationFormatter:
    """Format DocumentationAgent results."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, dict) and 'documentation' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield f"## Generated Documentation\n\n"
        yield f"*{reasoning}*\n\n"

        documentation = data.get('documentation', '')
        if documentation:
            yield documentation
            yield "\n"

        modules = data.get('modules', [])
        if modules:
            yield f"\n### Modules Analyzed ({len(modules)})\n\n"
            for m in modules[:10]:
                name = m.get('name', 'unknown')
                classes = m.get('classes', 0)
                functions = m.get('functions', 0)
                yield f"- **{name}**: {classes} classes, {functions} functions\n"


class MarkdownFormatter:
    """Format pre-formatted markdown data."""

    @staticmethod
    def can_format(data: Any) -> bool:
        if not isinstance(data, dict):
            return False
        return 'formatted_markdown' in data or 'markdown' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        if 'formatted_markdown' in data:
            yield data['formatted_markdown']
        elif 'markdown' in data:
            yield data['markdown']


class StringFormatter:
    """Format plain string data."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return isinstance(data, str)

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        yield data


class FallbackFormatter:
    """Fallback formatter for unknown data structures."""

    @staticmethod
    def can_format(data: Any) -> bool:
        return True  # Always matches as fallback

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        if isinstance(data, dict) and data:
            yield f"## Result\n\n"
            for key, value in data.items():
                if isinstance(value, list):
                    yield f"**{key}:**\n"
                    for item in value[:10]:
                        yield f"- {item}\n"
                else:
                    yield f"**{key}:** {value}\n"

            # Extra fallback sections
            if 'infrastructure' in data:
                infra = data['infrastructure']
                if isinstance(infra, dict) and not any(
                    k in str(infra) for k in ['Deployment Plan', 'DevOps']
                ):
                    yield "\n**Infrastructure details:**\n"
                    for k, v in infra.items():
                        yield f"- {k}: {v}\n"

            if 'configuration' in data:
                yield "\n**Configuration details:**\n"
                for k, v in data['configuration'].items():
                    yield f"- {k}: {v}\n"

        elif reasoning and reasoning != "None":
            yield f"{reasoning}\n"


# =============================================================================
# FORMATTER REGISTRY
# =============================================================================

# Order matters - more specific formatters first, FallbackFormatter last
FORMATTERS: List[type] = [
    ArchitectFormatter,
    ReviewerFormatter,
    ExplorerFormatter,
    DevOpsFormatter,
    DevOpsResponseFormatter,
    TestingFormatter,
    RefactorerFormatter,
    DocumentationFormatter,
    MarkdownFormatter,
    StringFormatter,
    FallbackFormatter,
]


async def format_agent_result(result: Any) -> AsyncIterator[str]:
    """
    Format agent result using appropriate formatter.

    Main entry point that replaces the deeply nested _format_agent_result.

    Args:
        result: AgentResponse or similar result object

    Yields:
        Formatted markdown chunks
    """
    # Extract data and reasoning from result
    if hasattr(result, 'data') and hasattr(result, 'reasoning'):
        data = result.data
        reasoning = result.reasoning or ""
    elif hasattr(result, 'data'):
        data = result.data
        reasoning = ""
    elif hasattr(result, 'result'):
        yield str(result.result)
        return
    else:
        yield str(result)
        return

    # Find matching formatter
    for formatter_class in FORMATTERS:
        if formatter_class.can_format(data):
            async for chunk in formatter_class.format(data, reasoning):
                yield chunk
            return

    # Should never reach here due to FallbackFormatter
    yield str(data)


__all__ = [
    'format_agent_result',
    'ResultFormatter',
    'FORMATTERS',
]
