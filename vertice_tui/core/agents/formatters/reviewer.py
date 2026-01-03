"""
ReviewerFormatter - Format code review and security scan results.

Handles both ReviewerAgent and SecurityAgent outputs with
structured issue reporting and vulnerability details.
"""

from typing import Any, AsyncIterator, Dict, List

from .helpers import get_severity_emoji


class ReviewerFormatter:
    """
    Format ReviewerAgent and SecurityAgent code review results.

    Handles two report formats:
    1. String reports (SecurityAgent): Plain text with vulnerabilities
    2. Dict reports (ReviewerAgent): Structured with quality score, issues
    """

    @staticmethod
    def can_format(data: Any) -> bool:
        """Check if data contains a code review report ('report' key)."""
        return isinstance(data, dict) and 'report' in data

    @staticmethod
    async def format(data: Any, reasoning: str) -> AsyncIterator[str]:
        """Format code review report, delegating to appropriate sub-formatter."""
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
        """Format string-based report (SecurityAgent style)."""
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
        """Format dictionary-based report (ReviewerAgent style)."""
        score = report.get('quality_score')
        if score is not None:
            emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            yield f"### {emoji} Quality Score: {score}/100\n\n"

        if report.get('risk_level'):
            yield f"**Risk Level:** {report['risk_level']}\n\n"

        issues = report.get('issues', [])
        if issues:
            async for chunk in ReviewerFormatter._format_issues(issues):
                yield chunk
        else:
            yield "✅ No issues found!\n"

        recommendations = report.get('recommendations', [])
        if recommendations:
            yield f"\n### Recommendations\n\n"
            for rec in recommendations[:10]:
                yield f"- {rec}\n"

        if report.get('estimated_fix_time'):
            yield f"\n⏱️ Estimated fix time: {report['estimated_fix_time']}\n"

    @staticmethod
    async def _format_issues(issues: List[Dict]) -> AsyncIterator[str]:
        """Format code review issues with severity badges and fix suggestions."""
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
