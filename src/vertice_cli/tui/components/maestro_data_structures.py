"""
MAESTRO v10.0 - Data Structures for UI Components

Dataclasses for managing agent state, file operations, and metrics
in the new 30 FPS streaming interface.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"


class FileStatus(Enum):
    """File operation status"""

    ANALYZING = "analyzing"
    MODIFIED = "modified"
    SAVED = "saved"
    CREATING = "creating"
    ERROR = "error"


@dataclass
class AgentState:
    """
    State of an agent for display in streaming panel.

    Attributes:
        name: Agent display name (e.g., "CODE EXECUTOR AGENT")
        icon: Emoji icon representing the agent (e.g., "⚡")
        status: Current execution status
        content: List of content lines to display (streaming buffer)
        progress: Progress percentage (0.0 to 100.0)
        spinner_frame: Current frame index for spinner animation
        error_message: Error message if status is ERROR
    """

    name: str
    icon: str
    status: AgentStatus = AgentStatus.IDLE
    content: List[str] = field(default_factory=list)
    progress: float = 0.0
    spinner_frame: int = 0
    error_message: Optional[str] = None

    def add_content(self, text: str, max_lines: int = 1000):
        """
        Add content line with automatic buffer management.

        Args:
            text: Content line to add
            max_lines: Maximum lines to keep in buffer (increased to 1000 for streaming)
        """
        self.content.append(text)
        if len(self.content) > max_lines:
            # Keep only the most recent lines
            self.content = self.content[-max_lines:]

    def clear_content(self):
        """Clear all content"""
        self.content.clear()

    def set_error(self, message: str):
        """Set error state"""
        self.status = AgentStatus.ERROR
        self.error_message = message


@dataclass
class FileOperation:
    """
    File operation for display in file tree.

    Attributes:
        path: Relative file path (e.g., "src/agent.py")
        status: Current operation status
        lines_added: Number of lines added (for diffs)
        lines_removed: Number of lines removed (for diffs)
        timestamp: Operation timestamp (for sorting)
    """

    path: str
    status: FileStatus
    lines_added: int = 0
    lines_removed: int = 0
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    @property
    def has_diff(self) -> bool:
        """Check if operation has diff information"""
        return self.lines_added > 0 or self.lines_removed > 0

    @property
    def net_change(self) -> int:
        """Calculate net line change"""
        return self.lines_added - self.lines_removed


@dataclass
class MetricsData:
    """
    System metrics for performance dashboard.

    Attributes:
        success_rate: Success rate percentage (0.0 to 100.0)
        tokens_used: Total tokens used in current session
        tokens_saved: Token efficiency percentage from MCP pattern
        saved_money: Estimated money saved from token reduction
        latency_ms: Average latency in milliseconds
        execution_count: Total number of executions
        error_count: Total number of errors
    """

    success_rate: float = 100.0
    tokens_used: int = 0
    tokens_saved: float = 98.7  # MCP pattern default
    saved_money: float = 0.0
    latency_ms: int = 0
    execution_count: int = 0
    error_count: int = 0

    def update_from_execution(self, success: bool, tokens: int, latency: float):
        """
        Update metrics from execution result.

        Args:
            success: Whether execution succeeded
            tokens: Tokens used in this execution
            latency: Execution latency in seconds
        """
        self.execution_count += 1
        if not success:
            self.error_count += 1

        # Update success rate
        self.success_rate = (self.execution_count - self.error_count) / self.execution_count * 100

        # Update tokens
        self.tokens_used += tokens

        # Update latency (rolling average)
        if self.latency_ms == 0:
            self.latency_ms = int(latency * 1000)
        else:
            # Exponential moving average
            alpha = 0.3
            self.latency_ms = int(alpha * (latency * 1000) + (1 - alpha) * self.latency_ms)

    def calculate_savings(self, cost_per_1k_tokens: float = 0.015) -> float:
        """
        Calculate money saved from token efficiency.

        Args:
            cost_per_1k_tokens: Cost per 1000 tokens (default: Claude Sonnet)

        Returns:
            Estimated savings in dollars
        """
        if self.tokens_saved <= 0:
            return 0.0

        # Calculate what would have been used without MCP pattern
        original_tokens = self.tokens_used / (1 - self.tokens_saved / 100)
        saved_tokens = original_tokens - self.tokens_used

        self.saved_money = (saved_tokens / 1000) * cost_per_1k_tokens
        return self.saved_money


@dataclass
class StreamingEvent:
    """
    Normalized streaming event from agents.

    Used to standardize events from different agent implementations.

    Attributes:
        type: Event type ("thinking", "command", "status", "progress", "result")
        data: Event data (format depends on type)
        agent_name: Name of agent that emitted the event
        timestamp: Event timestamp
    """

    type: str
    data: any
    agent_name: str = ""
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    @classmethod
    def thinking(cls, token: str, agent_name: str = "") -> "StreamingEvent":
        """Create thinking event (LLM token)"""
        return cls(type="thinking", data=token, agent_name=agent_name)

    @classmethod
    def command(cls, command: str, agent_name: str = "") -> "StreamingEvent":
        """Create command event"""
        return cls(type="command", data=command, agent_name=agent_name)

    @classmethod
    def status(cls, message: str, agent_name: str = "") -> "StreamingEvent":
        """Create status event"""
        return cls(type="status", data=message, agent_name=agent_name)

    @classmethod
    def progress(cls, percent: float, agent_name: str = "") -> "StreamingEvent":
        """Create progress event"""
        return cls(type="progress", data={"percent": percent}, agent_name=agent_name)

    @classmethod
    def result(cls, data: dict, agent_name: str = "") -> "StreamingEvent":
        """Create result event"""
        return cls(type="result", data=data, agent_name=agent_name)

    @classmethod
    def error(cls, message: str, agent_name: str = "") -> "StreamingEvent":
        """Create error event"""
        return cls(type="error", data={"message": message}, agent_name=agent_name)
