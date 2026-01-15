"""
Enterprise Onboarding Session Management
=======================================

Structured management of customer onboarding sessions and meetings.

This module provides:
- Session scheduling and tracking
- Agenda management and follow-up
- Stakeholder engagement monitoring
- Automated session preparation

Part of the Customer Success Foundation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class OnboardingSession:
    """A customer onboarding session."""

    id: str
    customer_id: str
    session_type: str  # kickoff, milestone, checkpoint, completion
    scheduled_date: datetime
    actual_date: Optional[datetime] = None

    # Participants
    attendees: List[str] = field(default_factory=list)
    organizer: str = ""

    # Content and agenda
    agenda_items: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)

    # Outcomes
    completed_objectives: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    blockers_identified: List[str] = field(default_factory=list)

    # Follow-up
    next_session_date: Optional[datetime] = None
    follow_up_actions: List[str] = field(default_factory=list)

    # Metadata
    duration_minutes: Optional[int] = None
    satisfaction_rating: Optional[float] = None
    notes: str = ""


class SessionManager:
    """
    Manager for enterprise onboarding sessions.

    Handles scheduling, tracking, and follow-up for all customer sessions.
    """

    def __init__(self) -> None:
        """Initialize the session manager."""
        self.sessions: Dict[str, List[OnboardingSession]] = {}
        self.logger = logging.getLogger(f"{__name__}.SessionManager")

    async def schedule_session(
        self,
        customer_id: str,
        session_type: str,
        scheduled_date: datetime,
        agenda_items: List[str],
        attendees: List[str],
    ) -> OnboardingSession:
        """
        Schedule an onboarding session for a customer.

        Args:
            customer_id: Customer identifier
            session_type: Type of session
            scheduled_date: When to schedule the session
            agenda_items: Agenda items for the session
            attendees: List of attendees

        Returns:
            Scheduled onboarding session
        """
        session_id = f"session_{customer_id}_{session_type}_{int(scheduled_date.timestamp())}"

        session = OnboardingSession(
            id=session_id,
            customer_id=customer_id,
            session_type=session_type,
            scheduled_date=scheduled_date,
            agenda_items=agenda_items,
            attendees=attendees,
            organizer="success_manager",
        )

        if customer_id not in self.sessions:
            self.sessions[customer_id] = []

        self.sessions[customer_id].append(session)

        self.logger.info(f"Scheduled {session_type} session for customer {customer_id}")
        return session

    async def complete_session(
        self,
        session_id: str,
        completed_objectives: List[str],
        action_items: List[str],
        blockers: List[str],
        satisfaction_rating: Optional[float] = None,
        notes: str = "",
    ) -> bool:
        """
        Mark a session as completed with outcomes.

        Args:
            session_id: Session identifier
            completed_objectives: Objectives that were achieved
            action_items: Follow-up action items
            blockers: Blockers identified during session
            satisfaction_rating: Session satisfaction rating
            notes: Additional session notes

        Returns:
            True if session was completed successfully
        """
        session = self._find_session(session_id)
        if not session:
            return False

        session.actual_date = datetime.utcnow()
        session.completed_objectives = completed_objectives
        session.action_items = action_items
        session.blockers_identified = blockers
        session.satisfaction_rating = satisfaction_rating
        session.notes = notes

        self.logger.info(f"Completed session {session_id}")
        return True

    def _find_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Find a session by ID."""
        for customer_sessions in self.sessions.values():
            for session in customer_sessions:
                if session.id == session_id:
                    return session
        return None

    async def get_upcoming_sessions(self, customer_id: str) -> List[OnboardingSession]:
        """
        Get upcoming sessions for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of upcoming sessions
        """
        if customer_id not in self.sessions:
            return []

        now = datetime.utcnow()
        return [
            session
            for session in self.sessions[customer_id]
            if not session.actual_date and session.scheduled_date > now
        ]

    async def get_session_history(self, customer_id: str) -> List[OnboardingSession]:
        """
        Get completed session history for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of completed sessions
        """
        if customer_id not in self.sessions:
            return []

        return [session for session in self.sessions[customer_id] if session.actual_date]
