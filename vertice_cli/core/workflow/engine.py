"""
Workflow Engine - Multi-step workflow orchestration.

Combines best practices from:
- Cursor AI: Dependency graph + checkpoints
- Claude: Tree-of-Thought + self-critique
- Constitutional: LEI tracking + validation
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .models import StepStatus, WorkflowResult, Critique
from .dependency_graph import DependencyGraph
from .tree_of_thought import TreeOfThought
from .auto_critique import AutoCritique
from .checkpoint_manager import CheckpointManager
from .transaction import Transaction

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Multi-step workflow orchestration engine.

    Combines:
    - Cursor AI: Dependency graph + checkpoints
    - Claude: Tree-of-Thought + self-critique
    - Constitutional: LEI tracking + validation
    """

    def __init__(
        self,
        llm_client: Any,
        recovery_engine: Any,
        tool_registry: Any
    ) -> None:
        self.llm = llm_client
        self.recovery = recovery_engine
        self.tools = tool_registry

        # Components
        self.tree_of_thought: TreeOfThought = TreeOfThought(llm_client)
        self.dependency_graph: DependencyGraph = DependencyGraph()
        self.auto_critique: AutoCritique = AutoCritique()
        self.checkpoints: CheckpointManager = CheckpointManager()

    async def execute_workflow(
        self,
        user_goal: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute multi-step workflow.

        Args:
            user_goal: User's goal
            initial_context: Initial context

        Returns:
            Workflow result
        """
        start_time = time.time()
        context = initial_context or {}

        logger.info(f"Starting workflow: {user_goal}")

        # 1. Tree-of-Thought planning (Constitutional Layer 2)
        available_tools = list(self.tools.get_all().keys())
        paths = await self.tree_of_thought.generate_paths(
            user_goal,
            available_tools,
            max_paths=3
        )

        best_path = self.tree_of_thought.select_best_path(paths)
        logger.info(f"Selected path: {best_path.description} (score: {best_path.total_score:.2f})")

        # 2. Build dependency graph
        for step in best_path.steps:
            self.dependency_graph.add_step(step)

        try:
            execution_order = self.dependency_graph.topological_sort()
        except ValueError as e:
            logger.error(f"Dependency error: {e}")
            return WorkflowResult(
                success=False,
                completed_steps=[],
                total_time=time.time() - start_time
            )

        # 3. Create transaction
        transaction = Transaction(f"workflow_{int(time.time())}")

        # 4. Execute steps with checkpoints
        completed: List = []
        critiques: List[Critique] = []

        for i, step in enumerate(execution_order):
            result = await self._execute_step(
                step, i, transaction, context, completed, critiques
            )
            if result is not None:
                # Early return on failure
                result.total_time = time.time() - start_time
                return result

        # 5. Commit transaction
        await transaction.commit()

        total_time = time.time() - start_time
        logger.info(f"Workflow completed in {total_time:.2f}s ({len(completed)} steps)")

        return WorkflowResult(
            success=True,
            completed_steps=completed,
            total_time=total_time,
            critiques=critiques,
            final_context=context
        )

    async def _execute_step(
        self,
        step: Any,
        index: int,
        transaction: Transaction,
        context: Dict[str, Any],
        completed: List,
        critiques: List[Critique]
    ) -> Optional[WorkflowResult]:
        """Execute single workflow step.

        Returns:
            WorkflowResult if failed, None if success
        """
        # Create checkpoint before risky operations
        if step.is_risky:
            checkpoint_id = f"{transaction.transaction_id}_step_{index}"
            self.checkpoints.create_checkpoint(
                checkpoint_id,
                context,
                [s.step_id for s in completed]
            )

        # Execute step
        step.status = StepStatus.EXECUTING
        step_start = time.time()

        tool = self.tools.get(step.tool_name)
        if not tool:
            step.status = StepStatus.FAILED
            step.error = f"Tool not found: {step.tool_name}"

            await transaction.rollback(self.checkpoints)

            return WorkflowResult(
                success=False,
                completed_steps=completed,
                failed_step=step,
                total_time=0
            )

        try:
            result = await tool.execute(**step.args)
            step.execution_time = time.time() - step_start
            step.result = result

            if not result.success:
                step.status = StepStatus.FAILED
                step.error = str(result.data)

                await transaction.rollback(self.checkpoints)

                return WorkflowResult(
                    success=False,
                    completed_steps=completed,
                    failed_step=step,
                    total_time=0,
                    critiques=critiques
                )

            # Auto-critique (Constitutional Layer 2)
            critique = self.auto_critique.critique_step(step, result)
            critiques.append(critique)

            if not critique.passed:
                logger.warning(f"Step {step.step_id} critique failed: {critique.issues}")

                step.status = StepStatus.FAILED
                step.error = f"Critique failed: {', '.join(critique.issues)}"

                await transaction.rollback(self.checkpoints)

                return WorkflowResult(
                    success=False,
                    completed_steps=completed,
                    failed_step=step,
                    total_time=0,
                    critiques=critiques
                )

            # Success
            step.status = StepStatus.COMPLETED
            transaction.add_operation(step, result)
            completed.append(step)

            # Update context
            context[f"step_{step.step_id}_result"] = result

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)

            await transaction.rollback(self.checkpoints)

            return WorkflowResult(
                success=False,
                completed_steps=completed,
                failed_step=step,
                total_time=0,
                critiques=critiques
            )

        return None  # Success, continue
