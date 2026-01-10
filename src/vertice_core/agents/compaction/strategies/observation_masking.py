"""
Observation Masking Strategy - Intelligent tool output masking.

Removes verbose tool outputs while preserving critical information.
Best strategy for agentic loops based on 2025 research.
"""

import logging
import re
import time
from typing import Any, Dict, TYPE_CHECKING

from .base import CompactionStrategy_ABC

if TYPE_CHECKING:
    from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
    from vertice_core.agents.context import UnifiedContext

logger = logging.getLogger(__name__)


class ObservationMaskingStrategy(CompactionStrategy_ABC):
    """
    Observation masking strategy.

    Removes verbose tool outputs while preserving:
    - Command/tool name
    - Success/failure status
    - Key output values
    - Error messages

    This is the BEST strategy for agentic loops (Dec 2025 research).
    """

    # Tool output patterns to extract key info
    EXTRACT_PATTERNS = {
        "error": r"(?:error|exception|failed):\s*(.+?)(?:\n|$)",
        "success": r"(?:success|completed|done)(?::\s*(.+?))?(?:\n|$)",
        "count": r"(\d+)\s+(?:files?|items?|matches?|results?)",
        "path": r"(?:file|path|location):\s*(.+?)(?:\n|$)",
    }

    def compact(
        self,
        context: "UnifiedContext",
        config: "CompactionConfig",
    ) -> "CompactionResult":
        """Apply observation masking to context."""
        start_time = time.time()
        tokens_before = context._token_usage
        messages_removed = 0

        messages = context._messages.copy()
        masked_messages = []

        # Keep recent messages verbatim
        recent_count = config.keep_recent_messages

        for i, msg in enumerate(messages):
            is_recent = i >= len(messages) - recent_count

            if is_recent:
                # Keep verbatim
                masked_messages.append(msg)
            else:
                # Apply masking
                content = msg.get("content", "")
                role = msg.get("role", "")

                if role == "tool" or self._is_tool_output(content):
                    # Mask tool output
                    masked = self._mask_tool_output(content, config)
                    if masked:
                        masked_messages.append(
                            {
                                **msg,
                                "content": masked,
                                "_masked": "true",
                            }
                        )
                    else:
                        messages_removed += 1
                elif len(content) > config.max_tool_output_chars * 2:
                    # Truncate long non-tool content
                    truncated = self._truncate_content(content, config)
                    masked_messages.append({**msg, "content": truncated})
                else:
                    masked_messages.append(msg)

        # Update context
        context._messages = masked_messages
        tokens_after = context._token_usage
        compression_ratio = tokens_after / tokens_before if tokens_before > 0 else 1.0

        return CompactionResult(
            success=True,
            strategy_used=config.default_strategy,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio,
            duration_ms=(time.time() - start_time) * 1000,
            messages_removed=messages_removed,
        )

    def _is_tool_output(self, content: str) -> bool:
        """Check if content appears to be tool output."""
        # Look for common tool output patterns
        patterns = [
            r"^Command executed",
            r"^Output:",
            r"^Result:",
            r"^\$ ",  # Shell prompt
            r"^```",  # Code blocks
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in patterns)

    def _mask_tool_output(self, content: str, config: "CompactionConfig") -> str:
        """Mask verbose tool output, keeping essential info."""
        if len(content) <= config.max_tool_output_chars:
            return content

        # Extract key information
        key_info = self._extract_key_info(content)

        # Create summary
        summary_parts = []

        if key_info.get("success") is not None:
            status = "✅ Success" if key_info["success"] else "❌ Failed"
            summary_parts.append(status)

        if key_info.get("error"):
            summary_parts.append(f"Error: {key_info['error'][:100]}...")

        if key_info.get("count"):
            summary_parts.append(f"Found: {key_info['count']}")

        if key_info.get("path"):
            summary_parts.append(f"Path: {key_info['path'][:50]}...")

        # Apply regex masking for verbose patterns
        masked_content = content
        for pattern in config.mask_patterns:
            masked_content = re.sub(pattern, "", masked_content, flags=re.MULTILINE)

        # Truncate if still too long
        if len(masked_content) > config.max_tool_output_chars:
            masked_content = masked_content[: config.max_tool_output_chars] + "..."

        return masked_content

    def _extract_key_info(self, content: str) -> Dict[str, Any]:
        """Extract key information from tool output."""
        info: Dict[str, Any] = {}

        # Check for success/failure
        if re.search(r"(?:success|completed|done|ok)", content, re.IGNORECASE):
            info["success"] = True
        elif re.search(r"(?:error|exception|failed|fail)", content, re.IGNORECASE):
            info["success"] = False

        # Extract using patterns
        for key, pattern in self.EXTRACT_PATTERNS.items():
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                info[key] = match.group(1).strip() if match.groups() else match.group(0).strip()

        return info

    def _truncate_content(self, content: str, config: "CompactionConfig") -> str:
        """Truncate content to maximum length."""
        if len(content) <= config.max_tool_output_chars:
            return content
        return content[: config.max_tool_output_chars] + "..."
