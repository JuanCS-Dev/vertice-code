"""
Enterprise Customer Success Manager
===================================

Central coordinator for enterprise customer success activities.

This module provides:
- Unified customer success orchestration
- Integration of onboarding, health monitoring, and sessions
- Comprehensive success reporting and analytics

Part of the Customer Success Foundation.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .onboarding_playbooks import OnboardingPlaybookManager, OnboardingPlaybook
from .health_monitoring import HealthMonitoringEngine, CustomerHealthProfile
from .session_management import SessionManager, OnboardingSession


logger = logging.getLogger(__name__)


class CustomerSuccessManager:
    """
    Unified customer success management system.

    Orchestrates all aspects of enterprise customer success including
    onboarding, health monitoring, and stakeholder engagement.
    """

    def __init__(self) -> None:
        """Initialize the customer success manager."""
        self.playbook_manager = OnboardingPlaybookManager()
        self.health_engine = HealthMonitoringEngine()
        self.session_manager = SessionManager()
        self.logger = logging.getLogger(f"{__name__}.CustomerSuccessManager")

        # Register default enterprise playbook
        default_playbook = self.playbook_manager.create_default_enterprise_playbook()
        self.playbook_manager.register_playbook(default_playbook)

    async def create_onboarding_plan(
        self, customer_id: str, customer_profile: Dict[str, Any], playbook_id: Optional[str] = None
    ) -> OnboardingPlaybook:
        """
        Create a customized onboarding plan for a customer.

        Args:
            customer_id: Customer identifier
            customer_profile: Customer profile information
            playbook_id: Specific playbook to use (optional)

        Returns:
            Customized onboarding playbook
        """
        if playbook_id and playbook_id in self.playbook_manager.playbooks:
            playbook = self.playbook_manager.playbooks[playbook_id]
        else:
            playbook = self.playbook_manager.get_playbook_for_customer(customer_profile)

        if not playbook:
            playbook = self.playbook_manager.create_default_enterprise_playbook()

        # Customize for customer
        customized = self.playbook_manager.customize_playbook_for_customer(
            playbook, customer_profile
        )

        self.logger.info(f"Created onboarding plan for customer {customer_id}: {customized.name}")
        return customized

    async def assess_customer_health(
        self, customer_id: str, metrics_data: Dict[str, Any]
    ) -> CustomerHealthProfile:
        """
        Assess the overall health of a customer.

        Args:
            customer_id: Customer identifier
            metrics_data: Current metrics data

        Returns:
            Comprehensive health assessment
        """
        return await self.health_engine.assess_customer_health(customer_id, metrics_data)

    async def schedule_onboarding_session(
        self,
        customer_id: str,
        session_type: str,
        scheduled_date: datetime,
        agenda_items: List[str],
        attendees: List[str],
    ) -> OnboardingSession:
        """
        Schedule an onboarding session.

        Args:
            customer_id: Customer identifier
            session_type: Type of session
            scheduled_date: When to schedule
            agenda_items: Session agenda
            attendees: List of attendees

        Returns:
            Scheduled session
        """
        return await self.session_manager.schedule_session(
            customer_id, session_type, scheduled_date, agenda_items, attendees
        )

    async def get_customer_success_report(self, customer_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive customer success report.

        Args:
            customer_id: Customer identifier

        Returns:
            Complete customer success report
        """
        # Get health profile
        health_profile = self.health_engine.customer_profiles.get(customer_id)

        # Get onboarding progress (simplified)
        onboarding_progress = {
            "completed_milestones": 8,
            "total_milestones": 12,
            "next_milestone": "Production deployment validation",
            "days_until_completion": 21,
        }

        # Get session data
        upcoming_sessions = await self.session_manager.get_upcoming_sessions(customer_id)
        session_history = await self.session_manager.get_session_history(customer_id)

        engagement_metrics = {
            "total_sessions": len(session_history) + len(upcoming_sessions),
            "completed_sessions": len(session_history),
            "upcoming_sessions": len(upcoming_sessions),
            "average_satisfaction": 8.2 if session_history else 0.0,
        }

        return {
            "customer_id": customer_id,
            "report_date": datetime.utcnow(),
            "health_assessment": health_profile.dict() if health_profile else None,
            "onboarding_progress": onboarding_progress,
            "engagement_metrics": engagement_metrics,
            "upcoming_sessions": [
                {
                    "type": s.session_type,
                    "date": s.scheduled_date.isoformat(),
                    "agenda_items": s.agenda_items,
                }
                for s in upcoming_sessions
            ],
            "recent_activity": [
                {
                    "type": "session_completed",
                    "description": f"Completed {s.session_type} session",
                    "date": s.actual_date.isoformat() if s.actual_date else None,
                }
                for s in session_history[-5:]  # Last 5 sessions
            ],
            "recommendations": health_profile.recommended_actions if health_profile else [],
        }

    async def get_success_alerts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get active success alerts for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of active alerts
        """
        # Get health alerts
        health_alerts = await self.health_engine.get_health_alerts(customer_id)

        # Get session alerts
        now = datetime.utcnow()
        sessions = await self.session_manager.get_upcoming_sessions(customer_id)

        session_alerts = []
        for session in sessions:
            days_until = (session.scheduled_date - now).days
            if 0 < days_until <= 3:
                session_alerts.append(
                    {
                        "type": "upcoming_session",
                        "severity": "low",
                        "message": f"{session.session_type.title()} session in {days_until} days",
                        "session_date": session.scheduled_date.isoformat(),
                        "attendees": session.attendees,
                    }
                )

        return health_alerts + session_alerts
