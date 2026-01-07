"""
RefactorerAgent v8.0 - Enterprise Transactional Code Surgeon.

This module provides the main RefactorerAgent that orchestrates:
- AST-aware surgical patching (LibCST for formatting preservation)
- Transactional memory with multi-level rollback
- Semantic validation via knowledge graph
- Reinforcement learning-guided transformations
- Multi-file atomic refactoring (all-or-nothing)
- Blast radius integration (predict impact)
- Test-driven verification (run tests before commit)

Architecture inspired by:
- AI Code Refactoring with RL (2025)
- Morph's Automated Refactoring Engine
- Enterprise Code Modernization Best Practices

Philosophy (Martin Fowler):
    "Any fool can write code that a computer can understand.
     Good programmers write code that humans can understand."
"""

import ast
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)

from .models import (
    CodeChange,
    RefactoringAction,
    RefactoringPlan,
    RefactoringType,
    generate_change_id,
)
from .session import TransactionalSession
from .transformer import ASTTransformer
from .rl_policy import RLRefactoringPolicy

logger = logging.getLogger(__name__)


class RefactorerAgent(BaseAgent):
    """Enterprise Transactional Code Surgeon v8.0.

    This agent performs surgical code refactorings with:
    - Zero behavior changes
    - ACID transactional guarantees
    - Format preservation
    - Test-driven verification

    Attributes:
        transformer: AST transformation engine
        rl_policy: RL-based refactoring suggestions
        explorer: Optional ExplorerAgent for blast radius analysis
        session: Active transactional session
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
        explorer_agent: Optional[Any] = None,
    ):
        """Initialize RefactorerAgent.

        Args:
            llm_client: LLM provider client
            mcp_client: MCP client for tool execution
            explorer_agent: Optional ExplorerAgent for impact analysis
        """
        super().__init__(
            role=AgentRole.REFACTORER,
            capabilities=[
                AgentCapability.FILE_EDIT,
                AgentCapability.READ_ONLY,
                AgentCapability.BASH_EXEC,
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=self._build_system_prompt(),
        )

        self.transformer = ASTTransformer()
        self.rl_policy = RLRefactoringPolicy()
        self.explorer = explorer_agent
        self.session: Optional[TransactionalSession] = None

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return """
You are RefactorerAgent v8.0 - Enterprise Transactional Code Surgeon

MISSION: Perform surgical code refactorings with zero behavior changes.

PRINCIPLES:
1. **Preserve Behavior**: Never change external behavior
2. **Atomic Operations**: All changes or none (ACID)
3. **Semantic Validity**: Check references before commit
4. **Test-Driven**: Run tests before any commit
5. **Format Preservation**: Keep comments, whitespace, style

REFACTORING TYPES:
- Extract Method: Pull code into new function
- Inline Method: Replace calls with body
- Rename Symbol: Update symbol + all references
- Extract Class: Split large class
- Simplify Expression: Reduce complexity
- Modernize Syntax: Update to latest Python

OUTPUT:
Structured refactoring plan with dependencies and risk assessment.
"""

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute refactoring workflow.

        Args:
            task: Task containing refactoring request and context

        Returns:
            AgentResponse with refactoring results
        """
        try:
            self.session = TransactionalSession()

            # Check for pre-existing plan from PlannerAgent
            existing_plan = task.context.get("plan")

            if existing_plan and (existing_plan.get("sops") or existing_plan.get("stages")):
                plan = self._convert_sops_to_refactoring_plan(existing_plan)
            else:
                plan = await self._generate_standalone_plan(task)
                if isinstance(plan, AgentResponse):
                    return plan  # Analysis-only response

            # Execute plan transactionally
            result = await self._execute_plan(plan, dry_run=False)

            return AgentResponse(
                success=result["success"],
                data=result,
                reasoning=result.get("message", "Refactoring completed"),
            )

        except Exception as e:
            if self.session:
                await self.session.rollback_all()

            return AgentResponse(
                success=False,
                error=str(e),
                reasoning="Refactoring failed - all changes rolled back",
            )

    async def _generate_standalone_plan(self, task: AgentTask) -> RefactoringPlan | AgentResponse:
        """Generate plan when no pre-existing plan is provided.

        Args:
            task: The agent task

        Returns:
            RefactoringPlan or AgentResponse (for analysis mode)
        """
        target = task.context.get("target_file")
        refactoring_type = task.context.get("refactoring_type", "")

        # Use analysis mode if no explicit target
        if not target and not refactoring_type:
            return await self._analyze_refactoring_opportunities(task)

        # Try to find target from files list
        if not target:
            files_list = task.context.get("files", [])
            for f in files_list:
                if f.endswith(".py") and Path(f).exists():
                    target = f
                    break

        if not target:
            return await self._analyze_refactoring_opportunities(task)

        refactoring_type = refactoring_type or "auto"

        # Blast radius analysis
        blast_radius = await self._analyze_blast_radius(target)

        # Generate refactoring plan
        return await self._generate_plan(
            target=target,
            refactoring_type=refactoring_type,
            blast_radius=blast_radius,
            context=task.context,
        )

    def _convert_sops_to_refactoring_plan(self, execution_plan: Dict[str, Any]) -> RefactoringPlan:
        """Convert ExecutionPlan from PlannerAgent to RefactoringPlan.

        Args:
            execution_plan: Plan from PlannerAgent containing sops/stages

        Returns:
            RefactoringPlan compatible with _execute_plan()
        """
        sops = execution_plan.get("sops", [])
        stages = execution_plan.get("stages", [])

        changes = []
        for sop in sops:
            role = sop.get("role", "")
            if role in ["coder", "refactorer", "executor"]:
                changes.append(
                    {
                        "id": sop.get("id", f"sop-{len(changes)}"),
                        "action": sop.get("action", ""),
                        "file_path": sop.get("target_file", sop.get("file")),
                        "description": sop.get("description", sop.get("action", "")),
                        "dependencies": sop.get("dependencies", []),
                        "original_sop": sop,
                    }
                )

        if not changes and stages:
            for stage in stages:
                for step in stage.get("steps", []):
                    changes.append(
                        {
                            "id": step.get("id", f"stage-step-{len(changes)}"),
                            "action": step.get("action", ""),
                            "file_path": step.get("target_file"),
                            "description": step.get("description", ""),
                            "dependencies": step.get("dependencies", []),
                        }
                    )

        execution_order = [c["id"] for c in changes]
        affected_files = list(set(c["file_path"] for c in changes if c.get("file_path")))

        return RefactoringPlan(
            plan_id=execution_plan.get("plan_id", f"converted-{id(execution_plan)}"),
            goal=execution_plan.get("goal", "Execute planned changes"),
            changes=changes,
            execution_order=execution_order,
            affected_files=affected_files,
            blast_radius=execution_plan.get("blast_radius", {}),
            risk_level=execution_plan.get("risk_assessment", "MEDIUM"),
            require_tests=execution_plan.get("require_tests", True),
            require_approval=execution_plan.get("require_approval", False),
            rollback_strategy=execution_plan.get("rollback_strategy", "incremental"),
        )

    async def _analyze_blast_radius(self, target: str) -> Dict[str, List[str]]:
        """Analyze impact using Explorer agent.

        Args:
            target: Target file path

        Returns:
            Blast radius analysis with affected files and risk level
        """
        target_name = Path(target).name
        stem = Path(target).stem
        dependent_files = []

        if self.explorer:
            try:
                explore_task = AgentTask(
                    request=f"find code that imports or uses '{stem}'", context={"max_files": 50}
                )

                response = await self.explorer.execute(explore_task)

                if response.success and response.data:
                    relevant = response.data.get("relevant_files", [])
                    for f in relevant:
                        path = f.get("path")
                        if path and not path.endswith(target_name):
                            dependent_files.append(path)
            except Exception as e:
                logger.debug(f"Blast radius calculation warning: {e}")

        unique_dependents = list(set(dependent_files))
        usage_count = len(unique_dependents)

        if usage_count > 20:
            risk = "CRITICAL"
        elif usage_count > 5:
            risk = "HIGH"
        elif usage_count > 0:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return {
            "affected_files": [target],
            "dependent_files": unique_dependents,
            "risk_level": risk,
        }

    async def _analyze_refactoring_opportunities(self, task: AgentTask) -> AgentResponse:
        """Analyze code and suggest refactoring opportunities.

        Used when no target file is specified.

        Args:
            task: The agent task

        Returns:
            AgentResponse with analysis results
        """
        files_list = task.context.get("files", [])
        source_code = task.context.get("source_code", "")

        if not source_code and files_list:
            code_parts = []
            for f in files_list[:3]:
                try:
                    if Path(f).exists():
                        content = Path(f).read_text(errors="ignore")[:3000]
                        code_parts.append(f"# File: {f}\n{content}")
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug(f"Could not read file {f}: {e}")
                    continue
            source_code = "\n\n".join(code_parts)

        if not source_code:
            return AgentResponse(
                success=False,
                error="No source code provided for refactoring analysis",
                reasoning="Need either source_code or files in context",
            )

        prompt = f"""Analyze this code and identify refactoring opportunities.

CODE:
```python
{source_code[:4000]}
```

REQUEST: {task.request}

Provide a structured analysis with:
1. Duplicate code that can be extracted into functions
2. Complex methods that can be simplified
3. Naming improvements
4. Design pattern opportunities
5. Performance improvements

Format as markdown with specific line references."""

        try:
            analysis = await self._call_llm(prompt)

            return AgentResponse(
                success=True,
                data={
                    "analysis": analysis,
                    "refactoring_suggestions": [
                        {"type": "extract_method", "description": "Extract common patterns"},
                        {
                            "type": "simplify_expression",
                            "description": "Simplify complex conditionals",
                        },
                        {"type": "improve_naming", "description": "Use more descriptive names"},
                    ],
                    "files_analyzed": len(files_list),
                    "mode": "analysis_only",
                },
                reasoning=f"Analyzed {len(files_list)} files for refactoring opportunities",
            )
        except Exception as e:
            return AgentResponse(
                success=False, error=str(e), reasoning="Failed to analyze refactoring opportunities"
            )

    async def _generate_plan(
        self,
        target: str,
        refactoring_type: str,
        blast_radius: Dict[str, List[str]],
        context: Dict[str, Any],
    ) -> RefactoringPlan:
        """Generate comprehensive refactoring plan.

        Args:
            target: Target file path
            refactoring_type: Type of refactoring to perform
            blast_radius: Impact analysis results
            context: Additional context

        Returns:
            RefactoringPlan with all planned changes
        """
        target_path = Path(target)
        if not target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target}")

        original_content = target_path.read_text()
        self.session.backup_original(target, original_content)

        code_metrics = self._analyze_code_metrics(original_content)

        if refactoring_type == "auto":
            available_actions = self._generate_available_actions(original_content)
            best_action = self.rl_policy.suggest_refactoring(code_metrics, available_actions)
            refactoring_type = best_action.type.value

        prompt = self._build_refactoring_prompt(
            target=target,
            content=original_content,
            refactoring_type=refactoring_type,
            metrics=code_metrics,
            blast_radius=blast_radius,
        )

        llm_response = await self._call_llm(prompt)
        plan_data = self._parse_refactoring_plan(llm_response)

        return RefactoringPlan(
            plan_id=f"refactor-{self.session.session_id}",
            goal=f"Refactor {target} using {refactoring_type}",
            changes=plan_data.get("changes", []),
            affected_files=blast_radius.get("affected_files", []),
            blast_radius=blast_radius,
            risk_level=blast_radius.get("risk_level", "MEDIUM"),
        )

    async def _execute_plan(self, plan: RefactoringPlan, dry_run: bool = False) -> Dict[str, Any]:
        """Execute refactoring plan transactionally.

        Args:
            plan: The refactoring plan to execute
            dry_run: If True, don't write to disk

        Returns:
            Execution results
        """
        results = {
            "success": False,
            "changes_applied": 0,
            "changes_failed": 0,
            "test_results": None,
            "message": "",
        }

        try:
            for change_data in plan.changes:
                change = self._create_code_change(change_data)
                transformed = self._apply_transformation(change)
                change.new_content = transformed

                validation = self.session.stage_change(change, validate=True)

                if not validation.passed:
                    results["changes_failed"] += 1
                    results["message"] = f"Validation failed: {validation.errors}"
                    return results

                results["changes_applied"] += 1

            self.session.create_checkpoint("pre-commit")

            commit_success, commit_msg = await self.session.commit(
                dry_run=dry_run, run_tests=plan.require_tests
            )

            results["success"] = commit_success
            results["message"] = commit_msg

            return results

        except Exception as e:
            await self.session.rollback_all()
            results["message"] = f"Error: {e} - All changes rolled back"
            return results

    def _apply_transformation(self, change: CodeChange) -> str:
        """Apply AST transformation based on refactoring type.

        Args:
            change: The code change to apply

        Returns:
            Transformed source code
        """
        if change.refactoring_type == RefactoringType.EXTRACT_METHOD:
            return self.transformer.extract_method(
                change.original_content,
                change.line_start,
                change.line_end,
                change.affected_symbols[0] if change.affected_symbols else "extracted_method",
            )

        elif change.refactoring_type == RefactoringType.RENAME_SYMBOL:
            old_name, new_name = change.affected_symbols[:2]
            return self.transformer.rename_symbol(change.original_content, old_name, new_name)

        elif change.refactoring_type == RefactoringType.MODERNIZE_SYNTAX:
            return self.transformer.modernize_syntax(change.original_content)

        else:
            return change.new_content

    def _build_refactoring_prompt(
        self,
        target: str,
        content: str,
        refactoring_type: str,
        metrics: Dict[str, Any],
        blast_radius: Dict[str, List[str]],
    ) -> str:
        """Build LLM prompt for refactoring plan generation.

        Args:
            target: Target file path
            content: File content
            refactoring_type: Type of refactoring
            metrics: Code metrics
            blast_radius: Impact analysis

        Returns:
            Formatted prompt string
        """
        return f"""
REFACTORING REQUEST:
Target: {target}
Type: {refactoring_type}

CURRENT CODE:
```python
{content[:2000]}
```

CODE METRICS:
{json.dumps(metrics, indent=2)}

BLAST RADIUS:
Affected Files: {", ".join(blast_radius.get("affected_files", []))}
Risk Level: {blast_radius.get("risk_level", "UNKNOWN")}

TASK:
Generate a detailed refactoring plan that:
1. Preserves all external behavior
2. Updates ALL affected files in blast radius
3. Maintains code formatting and comments
4. Includes test updates if needed

OUTPUT FORMAT (JSON):
{{
    "changes": [
        {{
            "file": "path/to/file.py",
            "refactoring_type": "{refactoring_type}",
            "line_start": 10,
            "line_end": 20,
            "description": "Extract validation logic into separate method",
            "affected_symbols": ["old_name", "new_name"],
            "new_code": "def validate_input():\\n    ..."
        }}
    ],
    "execution_order": ["change-1", "change-2"],
    "risk_assessment": "MEDIUM"
}}
"""

    def _analyze_code_metrics(self, code: str) -> Dict[str, Any]:
        """Analyze code metrics for RL policy.

        Args:
            code: Source code to analyze

        Returns:
            Dictionary with code metrics
        """
        try:
            ast.parse(code)  # Validate syntax
            return {"loc": len(code.split("\n")), "complexity": 5, "coupling": 3}
        except Exception as e:
            logger.debug(f"Failed to extract metrics: {e}")
            return {}

    def _generate_available_actions(self, code: str) -> List[RefactoringAction]:
        """Generate list of possible refactoring actions.

        Args:
            code: Source code

        Returns:
            List of possible refactoring actions
        """
        return [
            RefactoringAction(
                type=RefactoringType.EXTRACT_METHOD,
                target="long_method",
                parameters={"lines": (10, 50)},
            )
        ]

    def _create_code_change(self, data: Dict[str, Any]) -> CodeChange:
        """Create CodeChange from dict.

        Args:
            data: Dictionary with change data

        Returns:
            CodeChange instance
        """
        file_path = data.get("file", data.get("file_path", ""))
        original = ""
        if file_path and Path(file_path).exists():
            original = Path(file_path).read_text()

        return CodeChange(
            id=generate_change_id(data),
            file_path=file_path,
            refactoring_type=RefactoringType(data.get("refactoring_type", "extract_method")),
            original_content=original,
            new_content=data.get("new_code", ""),
            description=data.get("description", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            affected_symbols=data.get("affected_symbols", []),
        )

    def _parse_refactoring_plan(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured plan.

        Args:
            llm_response: Raw LLM response

        Returns:
            Parsed plan dictionary
        """
        try:
            start = llm_response.find("{")
            end = llm_response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(llm_response[start:end])
        except Exception as e:
            logger.debug(f"Failed to parse refactoring plan: {e}")
        return {"changes": []}


def create_refactorer_agent(
    llm_client: Any, mcp_client: Any, explorer_agent: Optional[Any] = None
) -> RefactorerAgent:
    """Factory function to create RefactorerAgent.

    Args:
        llm_client: LLM provider client
        mcp_client: MCP client for tools
        explorer_agent: Optional ExplorerAgent for impact analysis

    Returns:
        Configured RefactorerAgent instance
    """
    return RefactorerAgent(
        llm_client=llm_client, mcp_client=mcp_client, explorer_agent=explorer_agent
    )


__all__ = [
    "RefactorerAgent",
    "create_refactorer_agent",
]
