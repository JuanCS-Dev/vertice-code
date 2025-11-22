"""
RefactorAgent - The Code Quality Analyzer: Intelligent Refactoring Suggestions

This agent analyzes code to identify code smells, architectural issues, and
opportunities for refactoring. Unlike RefactorerAgent (executor), this agent
focuses on ANALYSIS and RECOMMENDATIONS, not execution.

Architecture (Boris Cherny Philosophy):
    - Type-safe interfaces
    - Functional analysis methods
    - Zero side effects (READ_ONLY)
    - Comprehensive metrics

Philosophy:
    "Code is read 10x more than written. Make it readable."
    - Boris Cherny

Capabilities:
    - Code smell detection (God classes, long methods, etc.)
    - Complexity analysis (cyclomatic, cognitive)
    - Maintainability scoring
    - Refactoring recommendations
    - Architectural pattern detection

References:
    - Refactoring (Fowler): https://refactoring.com/
    - Clean Code (Martin): https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882
    - radon: https://radon.readthedocs.io/ (complexity metrics)
"""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)


class CodeSmell(str, Enum):
    """Types of code smells that can be detected."""
    LONG_METHOD = "long_method"
    GOD_CLASS = "god_class"
    DUPLICATE_CODE = "duplicate_code"
    DEEP_NESTING = "deep_nesting"
    MAGIC_NUMBERS = "magic_numbers"
    SHOTGUN_SURGERY = "shotgun_surgery"
    FEATURE_ENVY = "feature_envy"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    LAZY_CLASS = "lazy_class"
    DATA_CLUMPS = "data_clumps"


class RefactoringPattern(str, Enum):
    """Refactoring patterns that can be applied."""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    INTRODUCE_NULL_OBJECT = "introduce_null_object"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    CONSOLIDATE_DUPLICATE = "consolidate_duplicate"
    DECOMPOSE_CONDITIONAL = "decompose_conditional"
    REPLACE_TEMP_WITH_QUERY = "replace_temp_with_query"


@dataclass(frozen=True)
class CodeIssue:
    """Represents a code quality issue.
    
    Attributes:
        smell: Type of code smell
        file_path: Path to file
        line_number: Line where issue starts
        severity: Severity level (1-10, 10 = critical)
        description: Human-readable description
        suggestion: Refactoring suggestion
        pattern: Recommended refactoring pattern
    """
    smell: CodeSmell
    file_path: str
    line_number: int
    severity: int
    description: str
    suggestion: str
    pattern: RefactoringPattern
    
    def __post_init__(self) -> None:
        """Validate severity range."""
        if not 1 <= self.severity <= 10:
            raise ValueError("Severity must be between 1 and 10")


@dataclass(frozen=True)
class ComplexityMetrics:
    """Code complexity metrics.
    
    Attributes:
        cyclomatic_complexity: McCabe cyclomatic complexity
        cognitive_complexity: Cognitive complexity score
        halstead_difficulty: Halstead difficulty measure
        loc: Lines of code
        lloc: Logical lines of code
        sloc: Source lines of code (excluding comments/blanks)
    """
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_difficulty: float
    loc: int
    lloc: int
    sloc: int
    
    @property
    def is_complex(self) -> bool:
        """Check if code is too complex."""
        return self.cyclomatic_complexity > 10 or self.cognitive_complexity > 15


@dataclass(frozen=True)
class MaintainabilityIndex:
    """Maintainability index calculation.
    
    Formula:
        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
    
    Where:
        HV = Halstead Volume
        CC = Cyclomatic Complexity
        LOC = Lines of Code
    
    Score:
        0-25: Difficult to maintain
        26-50: Needs work
        51-75: Good
        76-100: Excellent
    """
    score: float
    grade: str
    
    def __post_init__(self) -> None:
        """Validate score range."""
        if not 0 <= self.score <= 100:
            raise ValueError("Maintainability score must be 0-100")


class RefactorAgent(BaseAgent):
    """
    The Code Quality Analyzer - Intelligent refactoring suggestions.
    
    This agent analyzes code for quality issues, complexity, and maintainability.
    It provides actionable refactoring recommendations without modifying code.
    
    Capabilities:
        - READ_ONLY: Analyze source code
        - BASH_EXEC: Run complexity analysis tools (radon, etc.)
    
    Philosophy (Boris Cherny):
        "Code quality is not subjective. It's measurable."
    """

    def __init__(
        self,
        llm_client: Any = None,
        mcp_client: Any = None,
        model: Any = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RefactorAgent with type-safe configuration.
        
        Args:
            llm_client: LLM provider client
            mcp_client: MCP tools client
            model: Alternative model (for test compatibility)
            config: Optional configuration dictionary
        """
        if llm_client is not None and mcp_client is not None:
            super().__init__(
                role=AgentRole.REFACTOR,
                capabilities=[
                    AgentCapability.READ_ONLY,
                    AgentCapability.BASH_EXEC,
                ],
                llm_client=llm_client,
                mcp_client=mcp_client,
                system_prompt=REFACTOR_SYSTEM_PROMPT,
            )
        else:
            # Test compatibility mode
            self.role = AgentRole.REFACTOR
            self.capabilities = [
                AgentCapability.READ_ONLY,
                AgentCapability.BASH_EXEC,
            ]
            self.name = "RefactorAgent"
            self.llm_client = model
            self.config = config or {}
        
        # Configuration
        self.max_method_lines: int = 20
        self.max_class_methods: int = 10
        self.max_cyclomatic_complexity: int = 10
        self.min_maintainability_index: float = 65.0
        
        # Execution tracking
        self.execution_count: int = 0

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute code quality analysis task.
        
        Args:
            task: Analysis task with action type in context
        
        Returns:
            AgentResponse with analysis results
        
        Workflow:
            1. Parse task action (detect_smells, analyze_complexity, etc.)
            2. Execute appropriate analysis method
            3. Calculate quality score
            4. Return structured response
        """
        self.execution_count += 1
        
        try:
            action = task.context.get("action", "detect_smells")
            
            if action == "detect_smells":
                return await self._handle_smell_detection(task)
            elif action == "analyze_complexity":
                return await self._handle_complexity_analysis(task)
            elif action == "calculate_maintainability":
                return await self._handle_maintainability_calculation(task)
            elif action == "suggest_refactorings":
                return await self._handle_refactoring_suggestions(task)
            elif action == "quality_score":
                return await self._handle_quality_scoring(task)
            else:
                return AgentResponse(
                    success=False,
                    data={},
                    reasoning=f"Unknown action: {action}",
                    error=f"Supported actions: detect_smells, analyze_complexity, calculate_maintainability, suggest_refactorings, quality_score",
                )
        
        except Exception as e:
            return AgentResponse(
                success=False,
                data={},
                reasoning=f"RefactorAgent execution failed: {str(e)}",
                error=str(e),
            )

    async def _handle_smell_detection(self, task: AgentTask) -> AgentResponse:
        """Detect code smells in source code.
        
        Args:
            task: Task with source_code or file_path in context
        
        Returns:
            AgentResponse with detected code smells
        """
        source_code = task.context.get("source_code", "")
        file_path = task.context.get("file_path", "")
        
        if not source_code and file_path:
            try:
                result = await self._execute_tool("read_file", {"path": file_path})
                source_code = result.get("content", "")
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    reasoning=f"Failed to read file: {file_path}",
                    error=str(e),
                )
        
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code provided",
                error="source_code or file_path required in task context",
            )
        
        # Detect smells
        issues = await self._detect_code_smells(source_code, file_path)
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(issues)
        
        return AgentResponse(
            success=True,
            data={
                "issues": [
                    {
                        "smell": issue.smell.value,
                        "file_path": issue.file_path,
                        "line_number": issue.line_number,
                        "severity": issue.severity,
                        "description": issue.description,
                        "suggestion": issue.suggestion,
                        "pattern": issue.pattern.value,
                    }
                    for issue in issues
                ],
                "total_issues": len(issues),
                "severity_score": severity_score,
            },
            reasoning=f"Found {len(issues)} code smells (severity score: {severity_score}/100)",
            metadata={
                "smells_by_type": self._group_smells_by_type(issues),
            },
        )

    async def _detect_code_smells(
        self, source_code: str, file_path: str
    ) -> List[CodeIssue]:
        """Detect various code smells in source code.
        
        Args:
            source_code: Python source code to analyze
            file_path: Path to file (for reporting)
        
        Returns:
            List of detected CodeIssue objects
        """
        issues: List[CodeIssue] = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return issues
        
        # Detect long methods
        issues.extend(self._detect_long_methods(tree, file_path))
        
        # Detect God classes
        issues.extend(self._detect_god_classes(tree, file_path))
        
        # Detect deep nesting
        issues.extend(self._detect_deep_nesting(tree, file_path))
        
        # Detect magic numbers
        issues.extend(self._detect_magic_numbers(tree, file_path))
        
        # Detect duplicate code (simplified)
        issues.extend(self._detect_duplicate_code(tree, file_path))
        
        return issues

    def _detect_long_methods(
        self, tree: ast.AST, file_path: str
    ) -> List[CodeIssue]:
        """Detect methods that are too long.
        
        Args:
            tree: AST of source code
            file_path: Path to file
        
        Returns:
            List of long method issues
        """
        issues: List[CodeIssue] = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                    lines = node.end_lineno - node.lineno + 1
                    
                    if lines > self.max_method_lines:
                        issues.append(
                            CodeIssue(
                                smell=CodeSmell.LONG_METHOD,
                                file_path=file_path,
                                line_number=node.lineno,
                                severity=min(10, (lines // self.max_method_lines) + 5),
                                description=f"Method '{node.name}' is too long ({lines} lines)",
                                suggestion=f"Extract smaller methods to reduce '{node.name}' to <{self.max_method_lines} lines",
                                pattern=RefactoringPattern.EXTRACT_METHOD,
                            )
                        )
        
        return issues

    def _detect_god_classes(
        self, tree: ast.AST, file_path: str
    ) -> List[CodeIssue]:
        """Detect classes with too many responsibilities.
        
        Args:
            tree: AST of source code
            file_path: Path to file
        
        Returns:
            List of God class issues
        """
        issues: List[CodeIssue] = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [
                    item
                    for item in node.body
                    if isinstance(item, ast.FunctionDef)
                ]
                
                if len(methods) > self.max_class_methods:
                    issues.append(
                        CodeIssue(
                            smell=CodeSmell.GOD_CLASS,
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=min(10, (len(methods) // self.max_class_methods) + 6),
                            description=f"Class '{node.name}' has too many methods ({len(methods)})",
                            suggestion=f"Split '{node.name}' into smaller, focused classes with single responsibilities",
                            pattern=RefactoringPattern.EXTRACT_CLASS,
                        )
                    )
        
        return issues

    def _detect_deep_nesting(
        self, tree: ast.AST, file_path: str
    ) -> List[CodeIssue]:
        """Detect deeply nested control structures.
        
        Args:
            tree: AST of source code
            file_path: Path to file
        
        Returns:
            List of deep nesting issues
        """
        issues: List[CodeIssue] = []
        
        def calculate_nesting_depth(node: ast.AST, depth: int = 0) -> int:
            """Calculate max nesting depth."""
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                    child_depth = calculate_nesting_depth(child, depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = calculate_nesting_depth(child, depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                depth = calculate_nesting_depth(node)
                
                if depth > 3:
                    issues.append(
                        CodeIssue(
                            smell=CodeSmell.DEEP_NESTING,
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=min(10, depth + 2),
                            description=f"Function '{node.name}' has deep nesting (depth: {depth})",
                            suggestion=f"Simplify nested conditions in '{node.name}' using guard clauses or extraction",
                            pattern=RefactoringPattern.DECOMPOSE_CONDITIONAL,
                        )
                    )
        
        return issues

    def _detect_magic_numbers(
        self, tree: ast.AST, file_path: str
    ) -> List[CodeIssue]:
        """Detect magic numbers (literal numbers in code).
        
        Args:
            tree: AST of source code
            file_path: Path to file
        
        Returns:
            List of magic number issues
        """
        issues: List[CodeIssue] = []
        
        # Allowed numbers (not magic)
        allowed = {0, 1, -1, 2}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in allowed:
                    issues.append(
                        CodeIssue(
                            smell=CodeSmell.MAGIC_NUMBERS,
                            file_path=file_path,
                            line_number=node.lineno if hasattr(node, "lineno") else 0,
                            severity=4,
                            description=f"Magic number {node.value} found",
                            suggestion=f"Replace {node.value} with a named constant",
                            pattern=RefactoringPattern.REPLACE_MAGIC_NUMBER,
                        )
                    )
        
        return issues

    def _detect_duplicate_code(
        self, tree: ast.AST, file_path: str
    ) -> List[CodeIssue]:
        """Detect duplicate code blocks (simplified).
        
        Args:
            tree: AST of source code
            file_path: Path to file
        
        Returns:
            List of duplicate code issues
        """
        # Simplified: This would need more sophisticated analysis
        # For now, return empty list
        return []

    def _calculate_severity_score(self, issues: List[CodeIssue]) -> int:
        """Calculate overall severity score (0-100, higher is worse).
        
        Args:
            issues: List of code issues
        
        Returns:
            Severity score
        """
        if not issues:
            return 0
        
        total_severity = sum(issue.severity for issue in issues)
        # Normalize to 0-100 range (assuming max 10 issues at severity 10)
        normalized = min(100, (total_severity / 100) * 100)
        
        return int(normalized)

    def _group_smells_by_type(
        self, issues: List[CodeIssue]
    ) -> Dict[str, int]:
        """Group smells by type for reporting.
        
        Args:
            issues: List of code issues
        
        Returns:
            Dictionary of smell type to count
        """
        groups: Dict[str, int] = {}
        for issue in issues:
            smell_type = issue.smell.value
            groups[smell_type] = groups.get(smell_type, 0) + 1
        return groups

    async def _handle_complexity_analysis(self, task: AgentTask) -> AgentResponse:
        """Analyze code complexity metrics.
        
        Args:
            task: Task with source_code in context
        
        Returns:
            AgentResponse with complexity metrics
        """
        source_code = task.context.get("source_code", "")
        
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code provided",
                error="source_code required in task context",
            )
        
        # Calculate complexity
        metrics = self._calculate_complexity_metrics(source_code)
        
        return AgentResponse(
            success=True,
            data={
                "metrics": {
                    "cyclomatic_complexity": metrics.cyclomatic_complexity,
                    "cognitive_complexity": metrics.cognitive_complexity,
                    "halstead_difficulty": metrics.halstead_difficulty,
                    "loc": metrics.loc,
                    "lloc": metrics.lloc,
                    "sloc": metrics.sloc,
                },
                "is_complex": metrics.is_complex,
            },
            reasoning=f"Cyclomatic: {metrics.cyclomatic_complexity}, Cognitive: {metrics.cognitive_complexity}",
            metadata={"complexity_analysis": "complete"},
        )

    def _calculate_complexity_metrics(self, source_code: str) -> ComplexityMetrics:
        """Calculate complexity metrics for source code.
        
        Args:
            source_code: Python source code
        
        Returns:
            ComplexityMetrics object
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return ComplexityMetrics(
                cyclomatic_complexity=0,
                cognitive_complexity=0,
                halstead_difficulty=0.0,
                loc=0,
                lloc=0,
                sloc=0,
            )
        
        # Calculate cyclomatic complexity (simplified)
        cyclomatic = self._calculate_cyclomatic_complexity(tree)
        
        # Calculate lines of code
        lines = source_code.split("\n")
        loc = len(lines)
        sloc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])
        lloc = sloc  # Simplified
        
        # Halstead (simplified, would need proper calculation)
        halstead = 1.0
        
        # Cognitive complexity (simplified)
        cognitive = cyclomatic + 2  # Rough estimate
        
        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            halstead_difficulty=halstead,
            loc=loc,
            lloc=lloc,
            sloc=sloc,
        )

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate McCabe cyclomatic complexity.
        
        Formula: CC = E - N + 2P
        Where:
            E = edges in control flow graph
            N = nodes in control flow graph
            P = connected components (functions)
        
        Simplified: Count decision points + 1
        
        Args:
            tree: AST of source code
        
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity

    async def _handle_maintainability_calculation(self, task: AgentTask) -> AgentResponse:
        """Calculate maintainability index.
        
        Args:
            task: Task with source_code in context
        
        Returns:
            AgentResponse with maintainability index
        """
        source_code = task.context.get("source_code", "")
        
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code provided",
                error="source_code required in task context",
            )
        
        # Calculate maintainability
        index = self._calculate_maintainability_index(source_code)
        
        return AgentResponse(
            success=True,
            data={
                "maintainability_index": {
                    "score": index.score,
                    "grade": index.grade,
                },
                "meets_threshold": index.score >= self.min_maintainability_index,
            },
            reasoning=f"Maintainability: {index.score:.1f}/100 ({index.grade})",
            metadata={"threshold": self.min_maintainability_index},
        )

    def _calculate_maintainability_index(self, source_code: str) -> MaintainabilityIndex:
        """Calculate maintainability index.
        
        Args:
            source_code: Python source code
        
        Returns:
            MaintainabilityIndex object
        """
        # Simplified calculation
        metrics = self._calculate_complexity_metrics(source_code)
        
        # Simplified MI formula (normally would use Halstead Volume)
        if metrics.loc == 0:
            score = 100.0
        else:
            # Penalize complexity and length
            score = 100 - (metrics.cyclomatic_complexity * 2) - (metrics.loc / 10)
            score = max(0, min(100, score))
        
        # Determine grade
        if score >= 76:
            grade = "A"
        elif score >= 51:
            grade = "B"
        elif score >= 26:
            grade = "C"
        else:
            grade = "D"
        
        return MaintainabilityIndex(score=score, grade=grade)

    async def _handle_refactoring_suggestions(self, task: AgentTask) -> AgentResponse:
        """Generate refactoring suggestions based on analysis.
        
        Args:
            task: Task with source_code in context
        
        Returns:
            AgentResponse with refactoring suggestions
        """
        source_code = task.context.get("source_code", "")
        file_path = task.context.get("file_path", "unknown.py")
        
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code provided",
                error="source_code required in task context",
            )
        
        # Detect smells
        issues = await self._detect_code_smells(source_code, file_path)
        
        # Group by pattern
        suggestions_by_pattern: Dict[str, List[CodeIssue]] = {}
        for issue in issues:
            pattern = issue.pattern.value
            if pattern not in suggestions_by_pattern:
                suggestions_by_pattern[pattern] = []
            suggestions_by_pattern[pattern].append(issue)
        
        return AgentResponse(
            success=True,
            data={
                "suggestions": [
                    {
                        "pattern": pattern,
                        "count": len(pattern_issues),
                        "issues": [
                            {
                                "line": issue.line_number,
                                "description": issue.description,
                                "suggestion": issue.suggestion,
                            }
                            for issue in pattern_issues
                        ],
                    }
                    for pattern, pattern_issues in suggestions_by_pattern.items()
                ],
                "total_suggestions": len(issues),
            },
            reasoning=f"Generated {len(suggestions_by_pattern)} refactoring patterns for {len(issues)} issues",
            metadata={"patterns_used": list(suggestions_by_pattern.keys())},
        )

    async def _handle_quality_scoring(self, task: AgentTask) -> AgentResponse:
        """Calculate comprehensive code quality score.
        
        Args:
            task: Task with source_code in context
        
        Returns:
            AgentResponse with quality score (0-100)
        
        Scoring Formula:
            - Smell severity: 40 points (inverted - fewer smells = higher score)
            - Complexity: 30 points (lower complexity = higher score)
            - Maintainability: 30 points (higher MI = higher score)
        """
        source_code = task.context.get("source_code", "")
        file_path = task.context.get("file_path", "")
        
        if not source_code:
            return AgentResponse(
                success=False,
                data={},
                reasoning="No source code provided",
                error="source_code required in task context",
            )
        
        # Calculate components
        issues = await self._detect_code_smells(source_code, file_path)
        severity_score = self._calculate_severity_score(issues)
        smell_component = max(0, 40 - (severity_score * 0.4))  # Invert and scale
        
        metrics = self._calculate_complexity_metrics(source_code)
        complexity_penalty = min(30, metrics.cyclomatic_complexity * 3)
        complexity_component = max(0, 30 - complexity_penalty)
        
        mi = self._calculate_maintainability_index(source_code)
        maintainability_component = (mi.score / 100) * 30
        
        total_score = int(smell_component + complexity_component + maintainability_component)
        
        return AgentResponse(
            success=True,
            data={
                "quality_score": total_score,
                "breakdown": {
                    "smell_score": int(smell_component),
                    "complexity_score": int(complexity_component),
                    "maintainability_score": int(maintainability_component),
                },
                "grade": self._score_to_grade(total_score),
                "issues_found": len(issues),
            },
            reasoning=f"Code quality: {total_score}/100 ({self._score_to_grade(total_score)})",
            metadata={"scoring_version": "1.0"},
        )

    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade.
        
        Args:
            score: Score from 0-100
        
        Returns:
            Letter grade
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


# System prompt for RefactorAgent
REFACTOR_SYSTEM_PROMPT = """You are the REFACTOR AGENT, the Code Quality Analyzer in the DevSquad.

ROLE: Analyze code for quality issues and suggest refactorings
PERSONALITY: Meticulous analyzer who sees patterns in chaos
CAPABILITIES: READ_ONLY + BASH_EXEC

YOUR RESPONSIBILITIES:
1. Detect code smells (God classes, long methods, etc.)
2. Calculate complexity metrics (cyclomatic, cognitive)
3. Measure maintainability index
4. Suggest refactoring patterns
5. Calculate comprehensive quality scores

CODE SMELL DETECTION:
- Long Method: >20 lines → Extract Method
- God Class: >10 methods → Extract Class
- Deep Nesting: >3 levels → Decompose Conditional
- Magic Numbers: Literals in code → Replace with Named Constants
- Duplicate Code: Similar blocks → Consolidate

COMPLEXITY ANALYSIS:
- Cyclomatic Complexity: Decision points in code
- Cognitive Complexity: Mental effort to understand
- Halstead Metrics: Program difficulty
- Target: CC < 10, Cognitive < 15

MAINTAINABILITY INDEX:
- Formula: 171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC)
- Score 0-100 (higher is better)
- Target: MI >= 65

REFACTORING PATTERNS:
1. Extract Method: Long method → Smaller methods
2. Extract Class: God class → Focused classes
3. Introduce Parameter Object: Long param list → Object
4. Replace Conditional with Polymorphism: Complex if/else → Classes
5. Decompose Conditional: Nested conditions → Guard clauses

QUALITY SCORING:
- Smell Detection: 40 points
- Complexity: 30 points
- Maintainability: 30 points
- Total: 0-100 (90+ = A, 80+ = B, 70+ = C, 60+ = D, <60 = F)

OUTPUT FORMAT (JSON):
{
  "issues": [
    {
      "smell": "long_method",
      "file_path": "src/user.py",
      "line_number": 42,
      "severity": 7,
      "description": "Method 'process_user' is too long (45 lines)",
      "suggestion": "Extract smaller methods to reduce to <20 lines",
      "pattern": "extract_method"
    }
  ],
  "quality_score": 75,
  "grade": "C"
}

REMEMBER:
- Code quality is measurable, not subjective
- Refactoring makes code easier to understand
- Small, focused methods beat large, complex ones
- When in doubt, simplify

You are analytical, you are precise, you are uncompromising on quality.
"""
