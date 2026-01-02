"""
ReviewerAgent - Main Orchestrator.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Enterprise-Grade Agentic Code Review System v5.0.
Orchestrates multiple specialized agents and uses RAG for deep context.

Author: Vertice Team
Date: 2026-01-02
"""

import ast
import json
import logging
import re
from typing import Any, Dict, List

import networkx as nx

from vertice_cli.agents.base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)
from vertice_cli.prompts.grounding import (
    get_analysis_grounding,
    INLINE_CODE_PRIORITY,
)
from vertice_cli.core.temperature_config import get_temperature

from .types import (
    CodeIssue,
    ComplexityMetrics,
    IssueCategory,
    IssueSeverity,
    RAGContext,
    ReviewReport,
)
from .graph_analyzer import CodeGraphAnalyzer
from .rag_engine import RAGContextEngine
from .security_agent import SecurityAgent
from .sub_agents import (
    CodeGraphAnalysisAgent,
    PerformanceAgent,
    TestCoverageAgent,
)

logger = logging.getLogger(__name__)

# Smart truncation limit
MAX_FILE_CHARS = 8000


class ReviewerAgent(BaseAgent):
    """
    Enterprise-Grade Agentic Code Review System v5.0.

    Orchestrates multiple specialized agents and uses RAG for deep context.
    """

    def __init__(self, llm_client: Any, mcp_client: Any):
        super().__init__(
            role=AgentRole.REVIEWER,
            capabilities=[AgentCapability.READ_ONLY, AgentCapability.BASH_EXEC],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=self._build_system_prompt()
        )

        # Initialize components
        self.rag_engine = RAGContextEngine(mcp_client, llm_client)
        self.security_agent = SecurityAgent("")
        self.performance_agent = PerformanceAgent()
        self.test_agent = TestCoverageAgent()
        self.graph_agent = CodeGraphAnalysisAgent()

    def _build_system_prompt(self) -> str:
        return """
        You are ReviewerAgent v5.0 - Enterprise-Grade Code Review System.

        You have access to:
        1. Static Analysis (AST, Complexity, Code Graphs)
        2. RAG-based Codebase Context
        3. Specialized Sub-Agents (Security, Performance, Testing)
        4. Team Standards & Historical Data

        Your role:
        - Provide actionable, context-aware feedback
        - Flag issues with clear explanations
        - Suggest fixes that align with team standards
        - Identify patterns across the codebase
        - Balance thoroughness with pragmatism

        Output: Structured ReviewReport JSON
        """

    async def execute(self, task: AgentTask) -> AgentResponse:
        try:
            # Phase 1: Load files and context
            files_map = await self._load_context(task)
            if not files_map:
                return AgentResponse(
                    success=False,
                    reasoning="No files found to review.",
                    error="No files provided"
                )

            # Phase 2: Build RAG context
            rag_context = await self.rag_engine.build_context(
                list(files_map.keys()),
                task.context.get("description", "")
            )

            # Phase 3: Static Analysis (Code Graphs)
            all_metrics = []
            all_nodes = []
            all_graphs = []
            all_issues = []

            for fname, content in files_map.items():
                if not fname.endswith('.py') and fname != "<inline>":
                    continue

                try:
                    tree = ast.parse(content)
                    analyzer = CodeGraphAnalyzer(fname)
                    metrics, nodes, graph = analyzer.analyze(tree)
                    all_metrics.extend(metrics)
                    all_nodes.extend(nodes)
                    all_graphs.append(graph)

                    # Immediate heuristic checks
                    for m in metrics:
                        if m.cyclomatic > 15:
                            all_issues.append(CodeIssue(
                                file=fname, line=1,
                                severity=IssueSeverity.HIGH,
                                category=IssueCategory.COMPLEXITY,
                                message=f"Function '{m.function_name}' exceeds complexity limit (CC={m.cyclomatic})",
                                explanation="High cyclomatic complexity indicates too many decision points",
                                fix_suggestion="Refactor into smaller functions with single responsibilities",
                                confidence=1.0
                            ))
                        if m.cognitive > 20:
                            all_issues.append(CodeIssue(
                                file=fname, line=1,
                                severity=IssueSeverity.MEDIUM,
                                category=IssueCategory.MAINTAINABILITY,
                                message=f"Function '{m.function_name}' has very high cognitive complexity ({m.cognitive})",
                                explanation="Code is difficult for humans to understand",
                                fix_suggestion="Simplify control flow and reduce nesting",
                                confidence=0.95
                            ))

                except SyntaxError as e:
                    all_issues.append(CodeIssue(
                        file=fname,
                        line=e.lineno or 0,
                        severity=IssueSeverity.CRITICAL,
                        category=IssueCategory.LOGIC,
                        message=f"Syntax Error: {e.msg}",
                        explanation="Code cannot be parsed",
                        confidence=1.0
                    ))

            # Phase 4: Run specialized agents
            for fname, content in files_map.items():
                if not fname.endswith('.py') and fname != "<inline>":
                    continue

                try:
                    tree = ast.parse(content)
                    self.security_agent.file_path = fname
                    sec_issues = await self.security_agent.analyze(content, tree)
                    all_issues.extend(sec_issues)
                except Exception as e:
                    logger.debug(f"Security analysis failed for {fname}: {e}")

                perf_issues = await self.performance_agent.analyze(content, all_metrics)
                for issue in perf_issues:
                    issue.file = fname
                all_issues.extend(perf_issues)

            # Test coverage
            test_issues = await self.test_agent.analyze(list(files_map.keys()))
            all_issues.extend(test_issues)

            # Graph analysis
            mega_graph = nx.DiGraph()
            for g in all_graphs:
                mega_graph = nx.compose(mega_graph, g)

            graph_issues = await self.graph_agent.analyze(mega_graph, all_nodes)
            all_issues.extend(graph_issues)

            # Phase 5: LLM Deep Analysis
            llm_prompt = self._build_llm_prompt(
                files_map, all_metrics, rag_context, all_issues
            )

            try:
                llm_response = await self._call_llm(llm_prompt, temperature=0.2)
                llm_data = self._parse_llm_json(llm_response)

                if "additional_issues" in llm_data:
                    for issue_dict in llm_data["additional_issues"]:
                        if isinstance(issue_dict, dict):
                            all_issues.append(CodeIssue(**issue_dict))
            except Exception as e:
                llm_data = {"summary": f"LLM analysis failed: {str(e)}"}

            # Phase 6: Calculate final score and risk
            score = self._calculate_score(all_issues, all_metrics)
            risk_level = self._calculate_risk(all_issues, score)

            # Phase 7: Generate recommendations
            recommendations = self._generate_recommendations(
                all_issues, all_metrics, rag_context
            )

            # Phase 8: Build final report
            report = ReviewReport(
                approved=score >= 75 and risk_level != "CRITICAL",
                score=score,
                risk_level=risk_level,
                metrics=all_metrics,
                issues=all_issues,
                rag_context=rag_context,
                summary=llm_data.get("summary", "Automated review completed."),
                recommendations=recommendations,
                estimated_fix_time=self._estimate_fix_time(all_issues),
                requires_human_review=risk_level in ["HIGH", "CRITICAL"] or score < 60
            )

            return AgentResponse(
                success=True,
                data={"report": report.model_dump()},
                reasoning=f"Analyzed {len(all_metrics)} functions. Found {len(all_issues)} issues. Score: {score}/100"
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                reasoning=f"Review process failed: {str(e)}"
            )

    def _smart_truncate(self, content: str, limit: int = MAX_FILE_CHARS) -> str:
        """
        Smart truncation that preserves complete Python functions/classes.

        Unlike naive truncation, this method attempts to cut at natural
        code boundaries (function/class definitions) to maintain parseable
        code in the truncated output.

        Args:
            content: Full source code content
            limit: Maximum character limit (default: 8000)

        Returns:
            Truncated content with a note about truncation if applicable
        """
        if len(content) <= limit:
            return content

        truncated = content[:limit]

        last_def = truncated.rfind('\n\ndef ')
        if last_def > limit // 2:
            return truncated[:last_def] + '\n# ... [truncated, full file has more content]'

        last_class = truncated.rfind('\n\nclass ')
        if last_class > limit // 2:
            return truncated[:last_class] + '\n# ... [truncated, full file has more content]'

        last_newline = truncated.rfind('\n')
        if last_newline > 0:
            return truncated[:last_newline] + '\n# ... [truncated, full file has more content]'

        return truncated + '\n# ... [truncated]'

    def _build_llm_prompt(
        self,
        files: Dict[str, str],
        metrics: List[ComplexityMetrics],
        rag_context: RAGContext,
        static_issues: List[CodeIssue]
    ) -> str:
        """
        Build comprehensive prompt for LLM deep semantic analysis.

        Constructs a structured prompt that includes:
        - Files content (smartly truncated)
        - Static analysis metrics
        - RAG context (team standards, historical issues)
        - Analysis grounding instructions

        The LLM is asked to find issues that static analysis missed,
        particularly logic bugs, edge cases, and architecture problems.

        Args:
            files: Dict mapping filename to content
            metrics: List of complexity metrics from static analysis
            rag_context: Team standards and historical context
            static_issues: Issues already found by static analysis

        Returns:
            Formatted prompt string for LLM analysis
        """
        truncated_files = {
            k: self._smart_truncate(v, MAX_FILE_CHARS)
            for k, v in files.items()
        }

        grounding = get_analysis_grounding()

        return f"""
{grounding}

{INLINE_CODE_PRIORITY}

Perform a semantic code review with the following context:

FILES TO REVIEW:
{json.dumps(truncated_files, indent=2)}

STATIC METRICS:
{json.dumps([m.model_dump() for m in metrics[:10]], indent=2)}

EXISTING ISSUES FOUND:
{len(static_issues)} issues already detected by static analysis.

RAG CONTEXT (Team Standards & History):
{json.dumps(rag_context.model_dump(), indent=2)}

Your task:
1. Find LOGIC BUGS that static analysis missed
2. Check for EDGE CASES not handled
3. Validate ARCHITECTURE decisions
4. Suggest improvements aligned with team standards
5. Focus on HIGH-IMPACT issues only
6. QUOTE specific code when pointing out issues

IMPORTANT: Only report issues you can see in the code. Do not speculate about code
that is not visible in the context above.

Output JSON with:
{{
    "additional_issues": [],
    "summary": "Brief summary of review with code references"
}}
"""

    async def _load_context(self, task: AgentTask) -> Dict[str, str]:
        """
        Load file contents from various sources for review.

        Priority order:
        1. Inline code in user message (markdown code blocks)
        2. Explicit files list in task context
        3. Single file_path in task context

        Returns:
            Dict mapping filename (or "<inline>") to file content
        """
        contents = {}

        # Priority 1: Inline code in user message
        user_message = task.context.get("user_message", "")
        if not user_message:
            user_message = task.context.get("prompt", task.context.get("request", ""))

        inline_code = self._extract_code_blocks(user_message)
        if inline_code:
            contents["<inline>"] = inline_code
            return contents

        # Priority 2: Files list
        files = task.context.get("files", [])
        for f in files:
            try:
                res = await self._execute_tool("read_file", {"path": f})
                if res.get("success"):
                    contents[f] = res.get("content", "")
                else:
                    with open(f, 'r', encoding='utf-8') as file:
                        contents[f] = file.read()
            except (OSError, UnicodeDecodeError) as e:
                logger.debug(f"Could not read file {f} for review: {e}")
                continue

        # Priority 3: File path
        if not contents:
            file_path = task.context.get("file_path", "")
            if file_path:
                try:
                    res = await self._execute_tool("read_file", {"path": file_path})
                    if res.get("success"):
                        contents[file_path] = res.get("content", "")
                    else:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            contents[file_path] = file.read()
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug(f"Could not read file {file_path} for review: {e}")

        return contents

    def _extract_code_blocks(self, text: str) -> str:
        """
        Extract Python code from text using multiple detection strategies.

        Extraction priority:
        1. Fenced markdown code blocks (```python ... ```)
        2. Lines starting with Python keywords (def, class, import, etc.)
        3. Indented blocks containing Python keywords

        Deduplicates extracted blocks to avoid reviewing the same code twice.

        Args:
            text: Raw text possibly containing code blocks

        Returns:
            Concatenated unique code blocks, or empty string if none found
        """
        if not text:
            return ""

        # Priority 1: Fenced code blocks
        fenced_pattern = r'```(?:python|py|python3)?\s*\n(.*?)```'
        fenced_matches = re.findall(fenced_pattern, text, re.DOTALL)

        if fenced_matches:
            unique_code = []
            seen = set()
            for code in fenced_matches:
                code = code.strip()
                if code and code not in seen:
                    seen.add(code)
                    unique_code.append(code)
            return '\n\n'.join(unique_code)

        # Priority 2: Python code at start of lines
        inline_code_pattern = r'(?:^|\n)((?:def |class |import |from |async def |@\w+).+(?:\n(?:    |\t).+)*)'
        inline_matches = re.findall(inline_code_pattern, text, re.DOTALL)

        if inline_matches:
            unique_code = []
            seen = set()
            for code in inline_matches:
                code = code.strip()
                if code and code not in seen:
                    seen.add(code)
                    unique_code.append(code)
            return '\n\n'.join(unique_code)

        # Priority 3: Indented blocks
        if any(kw in text for kw in ['def ', 'class ', 'return ', 'import ', 'if ', 'for ']):
            indented_pattern = r'(?:^|\n)((?:    |\t).+(?:\n(?:    |\t).+)*)'
            indented_matches = re.findall(indented_pattern, text)

            if indented_matches:
                unique_code = []
                seen = set()
                for code in indented_matches:
                    code = code.strip()
                    if code and code not in seen and len(code) > 20:
                        seen.add(code)
                        unique_code.append(code)
                if unique_code:
                    return '\n\n'.join(unique_code)

        return ""

    def _parse_llm_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response with robust error handling.

        Uses regex to find JSON objects in potentially mixed text output.
        Returns a fallback dict on parse failure rather than raising.

        Args:
            text: Raw LLM response text

        Returns:
            Parsed JSON dict with 'summary' and 'additional_issues' keys,
            or fallback dict on parse failure
        """
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"summary": "LLM response parsing failed", "additional_issues": []}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return {"summary": "LLM response invalid JSON", "additional_issues": []}

    def _calculate_score(
        self,
        issues: List[CodeIssue],
        metrics: List[ComplexityMetrics]
    ) -> int:
        """
        Calculate overall code quality score (0-100).

        Scoring algorithm:
        - Starts at 100
        - Deducts based on issue severity × confidence:
          CRITICAL: -30, HIGH: -15, MEDIUM: -7, LOW: -3, INFO: -1
        - Penalizes high average complexity (cyclomatic > 10, cognitive > 15)
        - Clamps to [0, 100] range

        Args:
            issues: List of found issues with severity and confidence
            metrics: List of complexity metrics per function

        Returns:
            Integer quality score between 0 and 100
        """
        score = 100

        severity_deductions = {
            IssueSeverity.CRITICAL: 30,
            IssueSeverity.HIGH: 15,
            IssueSeverity.MEDIUM: 7,
            IssueSeverity.LOW: 3,
            IssueSeverity.INFO: 1
        }

        for issue in issues:
            deduction = severity_deductions.get(issue.severity, 5)
            score -= int(deduction * issue.confidence)

        if metrics:
            avg_cyclo = sum(m.cyclomatic for m in metrics) / len(metrics)
            avg_cognitive = sum(m.cognitive for m in metrics) / len(metrics)

            if avg_cyclo > 10:
                score -= int((avg_cyclo - 10) * 2)
            if avg_cognitive > 15:
                score -= int((avg_cognitive - 15) * 1.5)

        return max(0, min(100, score))

    def _calculate_risk(self, issues: List[CodeIssue], score: int) -> str:
        """
        Determine deployment risk level based on issues and score.

        Risk levels:
        - CRITICAL: Any critical issues OR score < 40
        - HIGH: More than 2 high issues OR score < 60
        - MEDIUM: Score < 80
        - LOW: Score >= 80 with no critical/high issues

        Args:
            issues: List of found issues
            score: Calculated quality score (0-100)

        Returns:
            Risk level string: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
        """
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)

        if critical_count > 0 or score < 40:
            return "CRITICAL"
        elif high_count > 2 or score < 60:
            return "HIGH"
        elif score < 80:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendations(
        self,
        issues: List[CodeIssue],
        metrics: List[ComplexityMetrics],
        rag_context: RAGContext
    ) -> List[str]:
        """
        Generate actionable improvement recommendations.

        Recommendation logic:
        - Security issues → suggest security scanning tools
        - Many complex functions → suggest refactoring priorities
        - No test issues → remind about test coverage
        - Team standards → apply team-specific rules (e.g., docstrings)

        Args:
            issues: List of found issues by category
            metrics: Complexity metrics to identify refactoring candidates
            rag_context: Team standards from RAG engine

        Returns:
            List of human-readable recommendation strings
        """
        recs = []

        security_issues = [i for i in issues if i.category == IssueCategory.SECURITY]
        if security_issues:
            recs.append("Run a security scan with tools like Bandit or Semgrep")

        complex_funcs = [m for m in metrics if m.cyclomatic > 10]
        if len(complex_funcs) > 3:
            recs.append("Consider refactoring the most complex functions first")

        if not any(i.category == IssueCategory.TESTING for i in issues):
            recs.append("Ensure adequate test coverage for new functionality")

        if rag_context.team_standards.get("require_docstrings") == "true":
            recs.append("Add docstrings to all public functions")

        return recs

    def _estimate_fix_time(self, issues: List[CodeIssue]) -> str:
        """
        Estimate time required to fix all identified issues.

        Uses a simple weighted model:
        - CRITICAL: ~4 hours each
        - HIGH: ~2 hours each
        - MEDIUM: ~1 hour each
        - LOW/INFO: ignored

        Args:
            issues: List of issues with severity levels

        Returns:
            Human-readable time estimate string (e.g., "1-4 hours", "2+ days")
        """
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)

        total_hours = critical * 4 + high * 2 + medium * 1

        if total_hours < 1:
            return "< 1 hour"
        elif total_hours < 4:
            return "1-4 hours"
        elif total_hours < 8:
            return "4-8 hours (half day)"
        elif total_hours < 16:
            return "1-2 days"
        else:
            return "2+ days"


__all__ = ["ReviewerAgent"]
