"""
Enforcement Executors - Default executor implementations.

LoggingExecutor and ConsoleExecutor for action execution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions import EnforcementAction

from .types import ActionType


class LoggingExecutor:
    """Executor que apenas loga acoes."""

    def __init__(self, logger_name: str = "justica.enforcement"):
        self.logger = logging.getLogger(logger_name)

    def execute(self, action: EnforcementAction) -> bool:
        """Execute action by logging it."""
        level_map = {
            ActionType.LOG_INFO: "info",
            ActionType.LOG_WARNING: "warning",
            ActionType.LOG_ERROR: "error",
            ActionType.LOG_CRITICAL: "critical",
        }

        level = level_map.get(action.action_type, "info")
        getattr(self.logger, level)(f"[{action.action_type.name}] {action.target}: {action.reason}")
        return True


class ConsoleExecutor:
    """Executor que imprime no console (para debug/desenvolvimento)."""

    def execute(self, action: EnforcementAction) -> bool:
        """Execute action by printing to console."""
        icon_map = {
            ActionType.BLOCK_REQUEST: "🚫",
            ActionType.BLOCK_AGENT: "⛔",
            ActionType.BLOCK_TOOL: "🔒",
            ActionType.BLOCK_RESOURCE: "🔐",
            ActionType.WARNING: "⚠️",
            ActionType.STRONG_WARNING: "‼️",
            ActionType.ESCALATE_TO_HUMAN: "👤",
            ActionType.ESCALATE_TO_ADMIN: "👨‍💼",
            ActionType.ALLOW: "✅",
            ActionType.ALLOW_WITH_LOGGING: "✓",
            ActionType.LOG_INFO: "ℹ️",
            ActionType.LOG_WARNING: "⚠️",
            ActionType.LOG_ERROR: "❌",
            ActionType.LOG_CRITICAL: "🔥",
            ActionType.REDUCE_TRUST: "📉",
            ActionType.SUSPEND_AGENT: "🚷",
            ActionType.INCREASE_MONITORING: "👁️",
            ActionType.FLAG_FOR_REVIEW: "🚩",
        }

        icon = icon_map.get(action.action_type, "📝")
        print(f"{icon} [{action.action_type.name}] {action.target}: {action.reason}")
        return True


__all__ = [
    "LoggingExecutor",
    "ConsoleExecutor",
]
