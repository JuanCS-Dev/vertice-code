"""
BaseAgent v2.0: The Cybernetic Kernel.

Implements the OODA Loop (Observe, Orient, Decide, Act) for AI Agents.
Features:
- Structured Reasoning (Chain of Thought enforcement)
- Tool Capability Sandboxing
- Telemetry & Token Budgeting
- Self-Correction Mechanism

Philosophy:
    "An agent that cannot correct its own errors is just a script."
"""

import abc
import uuid
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic, cast

from pydantic import BaseModel, Field

# --- Core Types ---

class AgentRole(str, Enum):
    ARCHITECT = "architect"
    EXPLORER = "explorer"
    PLANNER = "planner"
    REFACTORER = "refactorer"
    REVIEWER = "reviewer"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DATABASE = "database"
    DEVOPS = "devops"
    REFACTOR = "refactor"  # Alias for compatibility

class AgentCapability(str, Enum):
    READ_ONLY = "read_only"
    FILE_EDIT = "file_edit"
    BASH_EXEC = "bash_exec"
    GIT_OPS = "git_ops"
    DESIGN = "design"
    DATABASE = "database"

class TaskStatus(str, Enum):
    PENDING = "pending"
    THINKING = "thinking"
    ACTING = "acting"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: str
    context: Dict[str, Any] = Field(default_factory=dict)
    session_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # New in v2.0: History tracking
    history: List[Dict[str, Any]] = Field(default_factory=list)

class AgentResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    error: Optional[str] = None
    
    # New in v2.0: Execution metrics
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Alias for compatibility
    @property
    def metadata(self):
        return self.metrics

class CapabilityViolationError(Exception):
    pass

# Compatibility alias for Day 3 tests
class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- The Agent Kernel ---

class BaseAgent(abc.ABC):
    """
    Abstract Cybernetic Agent.
    
    Enforces the 'Think before Act' protocol and manages tool safety.
    """

    def __init__(
        self,
        role: AgentRole,
        capabilities: List[AgentCapability],
        llm_client: Any,
        mcp_client: Any,
        system_prompt: str = "",
    ) -> None:
        self.role = role
        self.capabilities = capabilities
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.system_prompt = system_prompt
        self.execution_count = 0
        self.logger = logging.getLogger(f"agent.{role.value}")

    @abc.abstractmethod
    async def execute(self, task: AgentTask) -> AgentResponse:
        """Main entry point. Must be implemented by subclasses."""
        pass

    async def _reason(self, task: AgentTask, context_str: str) -> str:
        """
        Internal 'Thinking' Step.
        Forces the agent to perform Chain of Thought before touching tools.
        """
        prompt = f"""
        TASK: {task.request}
        CONTEXT: {context_str}
        
        Analyze the situation. 
        1. Identify the goal.
        2. Identify constraints.
        3. Formulate a plan.
        
        Respond with your reasoning trace.
        """
        return await self._call_llm(prompt, system_prompt=self.system_prompt)

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Wrapper for LLM calls with error handling and logging."""
        final_sys_prompt = system_prompt or self.system_prompt
        try:
            # Handle both async generate() and async stream()
            if hasattr(self.llm_client, 'generate'):
                response = await self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=final_sys_prompt,
                    **kwargs,
                )
            else:
                # Fallback for streaming client
                buffer = []
                async for chunk in self.llm_client.stream(
                    prompt=prompt,
                    system_prompt=final_sys_prompt,
                    **kwargs,
                ):
                    buffer.append(chunk)
                response = ''.join(buffer)
                
            self.execution_count += 1
            return cast(str, response)
        except Exception as e:
            self.logger.error(f"LLM Call failed: {e}")
            raise

    async def _stream_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Stream LLM responses token by token for 30 FPS updates.

        Yields:
            str: Individual tokens as they arrive from LLM
        """
        final_sys_prompt = system_prompt or self.system_prompt
        try:
            # Use stream_chat for real-time token delivery
            if hasattr(self.llm_client, 'stream_chat'):
                async for chunk in self.llm_client.stream_chat(
                    prompt=prompt,
                    context=final_sys_prompt,
                    **kwargs,
                ):
                    yield chunk
            elif hasattr(self.llm_client, 'stream'):
                async for chunk in self.llm_client.stream(
                    prompt=prompt,
                    system_prompt=final_sys_prompt,
                    **kwargs,
                ):
                    yield chunk
            else:
                # Fallback: call non-streaming and yield whole response
                response = await self._call_llm(prompt, system_prompt, **kwargs)
                yield response

            self.execution_count += 1
        except Exception as e:
            self.logger.error(f"LLM Stream failed: {e}")
            raise

    def _can_use_tool(self, tool_name: str) -> bool:
        """Strict capability enforcement."""
        # Mapping definition (Expanded for v2)
        tool_map = {
            "read_file": AgentCapability.READ_ONLY,
            "list_files": AgentCapability.READ_ONLY,
            "grep_search": AgentCapability.READ_ONLY,
            "ast_parse": AgentCapability.READ_ONLY,
            "find_files": AgentCapability.READ_ONLY,
            "write_file": AgentCapability.FILE_EDIT,
            "edit_file": AgentCapability.FILE_EDIT,
            "delete_file": AgentCapability.FILE_EDIT,
            "create_directory": AgentCapability.FILE_EDIT,
            "bash_command": AgentCapability.BASH_EXEC,
            "exec_command": AgentCapability.BASH_EXEC,
            "git_diff": AgentCapability.GIT_OPS,
            "git_commit": AgentCapability.GIT_OPS,
            "git_push": AgentCapability.GIT_OPS,
            "git_status": AgentCapability.GIT_OPS,
            "db_query": AgentCapability.DATABASE,
            "db_execute": AgentCapability.DATABASE,
            "db_schema": AgentCapability.DATABASE,
            "k8s_action": AgentCapability.BASH_EXEC,  # DevOps: Kubernetes operations
            "docker_build": AgentCapability.BASH_EXEC,  # DevOps: Docker operations
            "argocd_sync": AgentCapability.BASH_EXEC,  # DevOps: ArgoCD operations
        }
        
        required = tool_map.get(tool_name)
        if not required:
            # If tool is unknown, default to blocking it for safety
            self.logger.warning(f"Unknown tool requested: {tool_name}")
            return False
            
        return required in self.capabilities

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Executes MCP tool with safety checks."""
        if not self._can_use_tool(tool_name):
            msg = f"SECURITY VIOLATION: {self.role.value} attempted to use forbidden tool '{tool_name}'"
            self.logger.critical(msg)
            raise CapabilityViolationError(msg)

        try:
            self.logger.info(f"Executing {tool_name} with params: {parameters.keys()}")
            
            # Handle case where mcp_client is None (fallback to direct calls)
            if self.mcp_client is None:
                self.logger.warning("MCP client not available, tool execution skipped")
                return {"success": False, "error": "MCP client not initialized"}
            
            result = await self.mcp_client.call_tool(tool_name=tool_name, arguments=parameters)
            return cast(Dict[str, Any], result)
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {"success": False, "error": str(e)}

# Compatibility aliases for existing agents
TaskContext = AgentTask  # Alias for old code
