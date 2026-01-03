"""
Sofia Chat Mode - Continuous Socratic Dialogue.

This module provides stateful chat interface for Sofia,
enabling deep Socratic exploration through progressive questioning.

Philosophy:
    "Wisdom grows through dialogue, not monologue."
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from vertice_governance.sofia import SofiaCounsel
    from .agent import SofiaIntegratedAgent
    from .models import CounselResponse


class SofiaChatMode:
    """
    Continuous Socratic dialogue mode for Sofia.

    Provides a stateful chat interface where Sofia maintains context
    across multiple turns of conversation.

    Example:
        >>> sofia = create_sofia_agent(llm, mcp)
        >>> chat = SofiaChatMode(sofia)
        >>> response = await chat.send_message("Should I change careers?")
    """

    def __init__(self, sofia_agent: "SofiaIntegratedAgent"):
        """Initialize chat mode.

        Args:
            sofia_agent: SofiaIntegratedAgent instance to use
        """
        self.sofia = sofia_agent
        self.session_id = str(uuid4())
        self.turn_count = 0
        self.started_at = datetime.now(timezone.utc)

    async def send_message(self, query: str) -> "CounselResponse":
        """Send a message in chat mode.

        Args:
            query: User message/question

        Returns:
            CounselResponse with Sofia's counsel
        """
        response = await self.sofia.provide_counsel_async(
            query=query,
            session_id=self.session_id,
            context={"mode": "chat", "turn": self.turn_count}
        )
        self.turn_count += 1
        return response

    def send_message_sync(self, query: str) -> "CounselResponse":
        """Synchronous version of send_message.

        Args:
            query: User message/question

        Returns:
            CounselResponse with Sofia's counsel
        """
        response = self.sofia.provide_counsel(
            query=query,
            session_id=self.session_id,
            context={"mode": "chat", "turn": self.turn_count}
        )
        self.turn_count += 1
        return response

    def get_history(self) -> List["SofiaCounsel"]:
        """Get full chat history.

        Returns:
            List of SofiaCounsel objects in chronological order
        """
        return self.sofia.get_session_history(self.session_id)

    def clear(self) -> None:
        """Clear chat session and start fresh."""
        self.sofia.clear_session(self.session_id)
        self.session_id = str(uuid4())
        self.turn_count = 0
        self.started_at = datetime.now(timezone.utc)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of chat session.

        Returns:
            Dictionary with session statistics
        """
        history = self.get_history()
        duration = (datetime.now(timezone.utc) - self.started_at).total_seconds()

        total_questions = sum(len(c.questions_asked) for c in history)
        avg_confidence = (
            sum(c.confidence for c in history) / len(history)
            if history else 0.0
        )

        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "duration_seconds": duration,
            "total_questions_asked": total_questions,
            "avg_confidence": avg_confidence,
            "started_at": self.started_at.isoformat(),
        }

    def export_transcript(self) -> str:
        """Export chat transcript as formatted text.

        Returns:
            Formatted string with full conversation
        """
        history = self.get_history()

        lines = [
            "=" * 70,
            "SOFIA CHAT TRANSCRIPT",
            f"Session: {self.session_id}",
            f"Started: {self.started_at.isoformat()}",
            f"Turns: {self.turn_count}",
            "=" * 70,
            ""
        ]

        for i, counsel in enumerate(history, 1):
            lines.append(f"Turn {i} - {counsel.timestamp.strftime('%H:%M:%S')}")
            lines.append(f"User Query: {counsel.user_query}")
            lines.append(f"Sofia ({counsel.counsel_type.name}): {counsel.response}")
            lines.append(f"Confidence: {counsel.confidence:.0%}")
            lines.append("")

        return "\n".join(lines)


__all__ = ["SofiaChatMode"]
