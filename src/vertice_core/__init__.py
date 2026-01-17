"""
🧠 Vertice Core - AI Domain Kernel
🕐 Temporal Consciousness Core

Core types, protocols, and domain logic for AI-powered development tools.
Temporal Awareness: MICROSECOND PRECISION
"""

from vertice_core.types import (
    # Enums
    AgentRole,
    AgentCapability,
    # Exceptions
    CapabilityViolationError,
    QwenCoreError,
)

from vertice_core.protocols import (
    LLMClientProtocol,
    MCPClientProtocol,
    AgentProtocol,
    ToolProtocol,
)

from vertice_core.language_detector import (
    LanguageDetector,
    LANGUAGE_NAMES,
)

# Moved modules from core
from vertice_core.a2a import (
    TaskStatus,
)

__all__ = [
    # Enums
    "AgentRole",
    "AgentCapability",
    "TaskStatus",
    # Models
    "AgentTask",
    "AgentResponse",
    "TaskResult",
    # Exceptions
    "CapabilityViolationError",
    "QwenCoreError",
    # Protocols
    "LLMClientProtocol",
    "MCPClientProtocol",
    "AgentProtocol",
    "ToolProtocol",
    # Utilities
    "LanguageDetector",
    "LANGUAGE_NAMES",
]

__version__ = "1.0.0"
