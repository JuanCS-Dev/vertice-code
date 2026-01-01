"""
Agent Manager - Lazy-loading agent lifecycle management.

Extracted from agents_bridge.py for semantic modularity.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import inspect
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

from .types import AgentInfo
from .registry import AGENT_REGISTRY
from .router import AgentRouter
from .streaming import normalize_streaming_chunk

if TYPE_CHECKING:
    from ..llm_client import GeminiClient


class AgentManager:
    """
    Lazy-loading agent manager.

    Only imports agents when first used to keep startup fast.

    Usage:
        manager = AgentManager(llm_client)
        async for chunk in manager.invoke("planner", "Plan this feature"):
            print(chunk, end='')
    """

    def __init__(self, llm_client: Optional['GeminiClient'] = None) -> None:
        """Initialize agent manager.

        Args:
            llm_client: LLM client for fallback and agent creation
        """
        # CRITICAL: Register providers before any agent is created
        # This was missing and caused "Provider not available" errors
        try:
            from vertice_cli.core.providers.register import ensure_providers_registered
            ensure_providers_registered()
        except ImportError:
            pass  # CLI providers not available (minimal install)

        # Lazy import to avoid circular dependency
        if llm_client is None:
            from ..llm_client import GeminiClient
            llm_client = GeminiClient()

        self.llm_client = llm_client
        self._agents: Dict[str, Any] = {}
        self._load_errors: Dict[str, str] = {}
        self.router = AgentRouter()
        self._last_plan: Optional[str] = None  # Store last plan for execution

        # CRITICAL: Create MCP client for tools - was missing (passed None)
        self._mcp_client: Optional[Any] = None
        try:
            from vertice_cli.core.mcp import create_mcp_client
            # Attempt to create MCP client with error handling
            self._mcp_client = create_mcp_client()
            if self._mcp_client is None:
                # Log warning if client is None (fallback mode)
                print("⚠️ MCP Client creation returned None - capabilities will be limited.")
        except ImportError:
             print("⚠️ MCP module not found - running in standalone mode.")
        except Exception as e:
            print(f"❌ Failed to initialize MCP client: {e} - capabilities will be limited.")


    @property
    def available_agents(self) -> List[str]:
        """List of available agent names."""
        return list(AGENT_REGISTRY.keys())

    def get_agent_info(self, name: str) -> Optional[AgentInfo]:
        """Get agent metadata."""
        return AGENT_REGISTRY.get(name)

    async def get_agent(self, name: str) -> Optional[Any]:
        """
        Get or create agent instance.

        Lazy loads the agent module on first use.
        Uses inspect.signature() to detect constructor parameters.

        Args:
            name: Agent name from registry

        Returns:
            Agent instance or None if unavailable
        """
        if name in self._agents:
            return self._agents[name]

        if name in self._load_errors:
            return None

        info = AGENT_REGISTRY.get(name)
        if not info:
            self._load_errors[name] = f"Unknown agent: {name}"
            return None

        try:
            # Dynamic import
            import importlib
            module = importlib.import_module(info.module_path)
            agent_class = getattr(module, info.class_name)

            # Detect __init__ signature and pass appropriate args
            sig = inspect.signature(agent_class.__init__)
            params = sig.parameters

            init_kwargs: Dict[str, Any] = {}
            if 'llm_client' in params:
                init_kwargs['llm_client'] = self.llm_client
            if 'mcp_client' in params:
                # FIXED: Pass actual MCP client instead of None
                init_kwargs['mcp_client'] = self._mcp_client
            if 'model' in params:
                init_kwargs['model'] = self.llm_client

            agent = agent_class(**init_kwargs)

            # Wrap core agents with CoreAgentAdapter for mixin activation
            if info.is_core:
                from .core_adapter import CoreAgentAdapter
                adapter = CoreAgentAdapter(agent, info.name)
                self._agents[name] = adapter
                return adapter

            self._agents[name] = agent
            return agent

        except ImportError as e:
            self._load_errors[name] = f"Import error: {e}"
            return None
        except Exception as e:
            self._load_errors[name] = f"Init error: {e}"
            return None

    async def invoke(
        self,
        name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke an agent and stream response.

        Falls back to LLM if agent unavailable.

        Args:
            name: Agent name
            task: Task to execute
            context: Optional context dict

        Yields:
            Response chunks as strings
        """
        agent = await self.get_agent(name)

        if agent is None:
            # Fallback: use LLM directly with agent-specific prompt
            info = AGENT_REGISTRY.get(name)
            if info:
                system_prompt = (
                    f"You are a {info.role}. {info.description}. "
                    f"Capabilities: {', '.join(info.capabilities)}."
                )
                async for chunk in self.llm_client.stream(task, system_prompt):
                    yield chunk
            else:
                yield f"❌ Agent '{name}' not available"
            return

        # Create AgentTask
        from vertice_core import AgentTask
        agent_task = AgentTask(request=task, context=context or {})

        # Track plan output for later execution
        plan_chunks: Optional[List[str]] = [] if name == "planner" else None

        # Try streaming interface first
        if hasattr(agent, 'execute_streaming'):
            try:
                sig = inspect.signature(agent.execute_streaming)
                param_count = len([p for p in sig.parameters.values()
                                   if p.default == inspect.Parameter.empty])

                if param_count == 1:  # AgentTask only
                    async for chunk in agent.execute_streaming(agent_task):
                        normalized = normalize_streaming_chunk(chunk)
                        if plan_chunks is not None:
                            plan_chunks.append(normalized)
                        yield normalized
                else:  # task + context
                    async for chunk in agent.execute_streaming(task, context or {}):
                        normalized = normalize_streaming_chunk(chunk)
                        if plan_chunks is not None:
                            plan_chunks.append(normalized)
                        yield normalized

                # Save plan for later execution
                if plan_chunks:
                    plan_text = "".join(plan_chunks)
                    self._last_plan = plan_text
                    yield "\n💾 *Plan saved. Say 'create the files' or 'make it real' to execute.*\n"
                return
            except Exception as e:
                yield f"⚠️ Streaming failed: {e}\n"

        # Fallback to sync execute
        if hasattr(agent, 'execute'):
            try:
                result = await agent.execute(agent_task)
                async for chunk in self._format_agent_result(result):
                    yield chunk
                return
            except Exception as e:
                yield f"❌ Agent error: {e}"
                return

        yield f"❌ Agent '{name}' has no execute method"

    async def _format_agent_result(self, result: Any) -> AsyncIterator[str]:
        """Format agent result for display.

        Args:
            result: AgentResponse or similar result object

        Yields:
            Formatted chunks
        """
        # Format AgentResponse nicely instead of dumping raw dict
        if hasattr(result, 'data') and hasattr(result, 'reasoning'):
            data = result.data
            reasoning = result.reasoning

            # ArchitectAgent decisions
            if isinstance(data, dict) and 'decision' in data:
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
                if data.get('recommendations'):
                    yield "\n**Recommendations:**\n"
                    for rec in data['recommendations']:
                        yield f"- {rec}\n"

            # ReviewerAgent / SecurityAgent results
            elif isinstance(data, dict) and 'report' in data:
                report = data['report']
                yield f"## Code Review Report\n\n"
                yield f"*{reasoning}*\n\n"

                # SecurityAgent returns string report
                if isinstance(report, str):
                    yield report
                    yield "\n"
                    # Also show vulnerabilities if present
                    if data.get('vulnerabilities'):
                        yield "\n### Vulnerabilities Detail\n\n"
                        for vuln in data['vulnerabilities'][:15]:
                            severity = vuln.get('severity', 'MEDIUM')
                            vuln_type = vuln.get('vulnerability_type', 'unknown')
                            file_path = vuln.get('file', '')
                            line = vuln.get('line', '')
                            desc = vuln.get('description', 'No description')
                            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                            yield f"- {emoji} **[{severity}]** {vuln_type}: {desc}\n"
                            if file_path:
                                yield f"  📍 `{file_path}:{line}`\n"
                # ReviewerAgent returns dict report
                elif isinstance(report, dict):
                    if report.get('quality_score') is not None:
                        score = report['quality_score']
                        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                        yield f"### {emoji} Quality Score: {score}/100\n\n"

                    if report.get('risk_level'):
                        yield f"**Risk Level:** {report['risk_level']}\n\n"

                    issues = report.get('issues', [])
                    if issues:
                        yield f"### Issues Found ({len(issues)})\n\n"
                        for i, issue in enumerate(issues[:20], 1):  # Limit to 20
                            severity = issue.get('severity', 'MEDIUM')
                            category = issue.get('category', 'general')
                            message = issue.get('message', 'No description')
                            file_path = issue.get('file', '')
                            line = issue.get('line', '')
                            location = f" at `{file_path}:{line}`" if file_path and line else ""
                            severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️"}.get(severity, "⚪")
                            yield f"{i}. {severity_emoji} **[{severity}]** {message}{location}\n"
                            if issue.get('suggestion'):
                                yield f"   💡 *{issue['suggestion']}*\n"
                    else:
                        yield "✅ No issues found!\n"

                    recommendations = report.get('recommendations', [])
                    if recommendations:
                        yield f"\n### Recommendations\n\n"
                        for rec in recommendations[:10]:
                            yield f"- {rec}\n"

                    if report.get('estimated_fix_time'):
                        yield f"\n⏱️ Estimated fix time: {report['estimated_fix_time']}\n"

            # ExplorerAgent results
            elif isinstance(data, dict) and 'relevant_files' in data:
                if data.get('context_summary'):
                    yield f"{data['context_summary']}\n\n"
                relevant_files = data.get('relevant_files', [])
                if relevant_files:
                    yield "**Relevant Files:**\n"
                    for f in relevant_files:
                        if isinstance(f, dict):
                            path = f.get('path', 'unknown')
                            relevance = f.get('relevance', '')
                            reason = f.get('reason', '')
                            relevance_badge = f" [{relevance}]" if relevance else ""
                            reason_text = f" - {reason}" if reason else ""
                            yield f"- `{path}`{relevance_badge}{reason_text}\n"
                        else:
                            yield f"- `{f}`\n"
                else:
                    yield "⚠️ No relevant files found for this query.\n"

                if data.get('dependencies'):
                    yield "\n**Dependencies:**\n"
                    for d in data['dependencies']:
                        if isinstance(d, dict):
                            from_file = d.get('from', '')
                            to_file = d.get('to', '')
                            dep_type = d.get('type', '')
                            yield f"- `{from_file}` → `{to_file}` ({dep_type})\n"
                        else:
                            yield f"- {d}\n"
                if data.get('token_estimate'):
                    yield f"\n📊 *Token estimate: ~{data['token_estimate']} tokens*\n"

            # DevOps deployment plans
            elif isinstance(data, dict) and 'plan' in data:
                yield f"## DevOps Deployment Plan\n\n"
                yield f"*{reasoning}*\n\n"
                plan = data['plan']
                if isinstance(plan, dict):
                    if plan.get('deployment_id'):
                        yield f"**Deployment ID:** {plan['deployment_id']}\n"
                    if plan.get('strategy'):
                        yield f"**Strategy:** {plan['strategy']}\n"
                    if plan.get('pre_checks'):
                        yield "\n**Pre-Checks:**\n"
                        for check in plan['pre_checks']:
                            yield f"- {check}\n"
                    if plan.get('deployment_steps'):
                        yield "\n**Deployment Steps:**\n"
                        for step in plan['deployment_steps']:
                            yield f"- {step}\n"
                    if plan.get('post_checks'):
                        yield "\n**Post-Checks:**\n"
                        for check in plan['post_checks']:
                            yield f"- {check}\n"
                else:
                    yield str(plan)
                if data.get('status'):
                    yield f"\n**Status:** {data['status']}\n"
                # Infrastructure details
                if data.get('infrastructure'):
                    yield "\n**Infrastructure:**\n"
                    infra = data['infrastructure']
                    for key, value in infra.items():
                        yield f"- {key}: {value}\n"
                # Configuration details
                if data.get('configuration'):
                    yield "\n**Configuration:**\n"
                    config = data['configuration']
                    for key, value in config.items():
                        yield f"- {key}: {value}\n"

            # DevOps LLM response
            elif isinstance(data, dict) and 'response' in data:
                yield data['response']

            # Test cases (TestingAgent)
            elif isinstance(data, dict) and 'test_cases' in data:
                yield f"## Generated Test Cases\n\n"
                for tc in data['test_cases'][:10]:
                    yield f"### {tc.get('name', 'test')}\n"
                    yield f"```python\n{tc.get('code', '')}\n```\n\n"
                if data.get('total_assertions'):
                    yield f"*Total assertions: {data['total_assertions']}*\n"

            # Refactoring analysis (RefactorerAgent)
            elif isinstance(data, dict) and 'analysis' in data:
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

            # Documentation (DocumentationAgent)
            elif isinstance(data, dict) and 'documentation' in data:
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

            elif isinstance(data, dict) and 'formatted_markdown' in data:
                yield data['formatted_markdown']
            elif isinstance(data, dict) and 'markdown' in data:
                yield data['markdown']
            elif isinstance(data, str):
                yield data
            else:
                # Fallback: try to format any dict nicely
                if isinstance(data, dict) and data:
                    yield f"## Result\n\n"
                    for key, value in data.items():
                        if isinstance(value, list):
                            yield f"**{key}:**\n"
                            for item in value[:10]:
                                yield f"- {item}\n"
                        else:
                            yield f"**{key}:** {value}\n"
                elif reasoning and reasoning != "None":
                    yield f"{reasoning}\n"
                
                # FINAL FALLBACK: Check for common keys across all agents
                if isinstance(data, dict):
                    if 'infrastructure' in data and not any(k in str(data.get('infrastructure')) for k in ['Deployment Plan', 'DevOps']):
                         yield "\n**Infrastructure details:**\n"
                         for k, v in data['infrastructure'].items():
                             yield f"- {k}: {v}\n"
                    if 'configuration' in data:
                         yield "\n**Configuration details:**\n"
                         for k, v in data['configuration'].items():
                             yield f"- {k}: {v}\n"


        elif hasattr(result, 'data'):
            data = result.data
            if isinstance(data, str):
                yield data
            elif isinstance(data, dict) and 'formatted_markdown' in data:
                yield data['formatted_markdown']
            else:
                yield str(data)
        elif hasattr(result, 'result'):
            yield str(result.result)
        else:
            yield str(result)

    # =========================================================================
    # PLANNER v6.1 SPECIFIC METHODS
    # =========================================================================

    async def invoke_planner_multi(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner with Multi-Plan Generation (v6.1).

        Generates 3 alternative plans with different strategies:
        - STANDARD: Conservative, low-risk approach
        - ACCELERATOR: Fast execution, higher risk
        - LATERAL: Creative, unconventional approach
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'generate_multi_plan'):
            yield "⚠️ Planner doesn't support multi-plan (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🎯 **Generating 3 Alternative Plans...**\n\n"

            result = await agent.generate_multi_plan(agent_task)
            yield result.to_markdown()

        except Exception as e:
            yield f"❌ Multi-plan generation failed: {e}"

    async def invoke_planner_clarify(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner with Clarification Mode (v6.1).

        Before planning, the agent asks 2-3 clarifying questions.
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'generate_clarifying_questions'):
            yield "⚠️ Planner doesn't support clarification (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🤔 **Analyzing your request...**\n\n"

            questions = await agent.generate_clarifying_questions(agent_task)

            if questions:
                yield "Before I create a plan, I have some questions:\n\n"
                for i, q in enumerate(questions, 1):
                    yield f"**{i}.** {q.question}\n"
                    if q.options:
                        for opt in q.options:
                            yield f"   - {opt}\n"
                    yield "\n"
                yield "\n💡 *Answer these questions, then run `/plan` again with the context.*\n"
            else:
                yield "✅ No clarification needed. Proceeding with planning...\n\n"
                async for chunk in self.invoke("planner", task, context):
                    yield chunk

        except Exception as e:
            yield f"❌ Clarification failed: {e}"

    async def invoke_planner_explore(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner in Exploration Mode (v6.1).

        Read-only analysis mode - gathers context without modifications.
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'explore'):
            yield "⚠️ Planner doesn't support exploration (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🔍 **Exploration Mode (Read-Only)**\n\n"
            yield "_No modifications will be made - analysis only._\n\n"

            result = await agent.explore(agent_task)

            if result.success:
                exploration = result.data.get('exploration', {})

                if 'files_analyzed' in exploration:
                    yield f"**📁 Files Analyzed:** {exploration['files_analyzed']}\n\n"

                if 'key_findings' in exploration:
                    yield "**🔑 Key Findings:**\n"
                    for finding in exploration['key_findings']:
                        yield f"- {finding}\n"
                    yield "\n"

                if 'dependencies' in exploration:
                    yield "**🔗 Dependencies:**\n"
                    for dep in exploration['dependencies'][:10]:
                        yield f"- {dep}\n"
                    yield "\n"

                if 'recommendations' in exploration:
                    yield "**💡 Recommendations:**\n"
                    for rec in exploration['recommendations']:
                        yield f"- {rec}\n"
                    yield "\n"

                yield "\n✅ *Exploration complete. Use `/plan` to create an execution plan.*\n"
            else:
                yield f"❌ Exploration failed: {result.error}\n"

        except Exception as e:
            yield f"❌ Exploration failed: {e}"

    def detect_planner_mode(self, message: str) -> Optional[str]:
        """
        Detect which planner mode should be used based on message content.

        Returns:
            "multi" | "clarify" | "explore" | None (regular planning)
        """
        # Check for sub-mode patterns
        for mode in ["planner:multi", "planner:clarify", "planner:explore"]:
            patterns = self.router._compiled_patterns.get(mode, [])
            for compiled_pattern, weight in patterns:
                if compiled_pattern.search(message) and weight >= 0.85:
                    return mode.split(":")[1]

        return None
