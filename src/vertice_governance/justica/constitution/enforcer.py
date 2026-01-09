"""
Constitutional Enforcer - Enforces constitutional principles.

Following Anthropic's Constitutional AI pattern (2022-2026).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .core import Constitution
from .principles import EnforcementResult
from .types import EnforcementCategory, Severity

logger = logging.getLogger(__name__)


class ConstitutionalEnforcer:
    """
    Enforcer of constitutional principles.

    Following Anthropic's Constitutional AI pattern (2022-2026):
    - Self-supervision using explicit principles
    - Tiered response based on severity
    - Audit trail for all decisions
    - Escalation for ambiguous cases

    Usage:
        constitution = Constitution()
        enforcer = ConstitutionalEnforcer(constitution)

        result = enforcer.enforce("User requested to bypass authentication")
        if not result.allowed:
            print(f"Blocked by {result.principle_name}: {result.message}")
    """

    def __init__(self, constitution: Constitution):
        """
        Initialize enforcer with a constitution.

        Args:
            constitution: The Constitution to enforce
        """
        self.constitution = constitution
        self._enforcement_count = 0
        self._blocks_count = 0
        self._escalations_count = 0

    def enforce(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EnforcementResult:
        """
        Enforce constitutional principles on an action.

        This is the main enforcement method. It checks:
        1. DISALLOW principles first (hard blocks)
        2. ESCALATE principles (requires human review)
        3. MONITOR principles (allowed but logged)
        4. Default: ALLOW if no principle triggered

        Args:
            action: The action/text to evaluate
            context: Optional context dictionary

        Returns:
            EnforcementResult with the decision
        """
        self._enforcement_count += 1
        context = context or {}

        # Step 1: Check red flags (quick check)
        red_flags_found = self.constitution.check_red_flags(action)

        # Step 2: Check DISALLOW principles (highest priority)
        result = self._check_disallow_principles(action, red_flags_found)
        if result:
            return result

        # Step 3: Check ESCALATE principles
        result = self._check_escalate_principles(action)
        if result:
            return result

        # Step 4: Check escalation triggers from context
        result = self._check_escalation_triggers(context)
        if result:
            return result

        # Step 5: Check MONITOR principles (allowed but logged)
        self._check_monitor_principles(action)

        # Step 6: Red flags found but no principle matched - escalate
        if red_flags_found and len(red_flags_found) >= 2:
            return self._escalate_for_red_flags(red_flags_found)

        # Step 7: Default - ALLOW with optional monitoring
        return self._allow_action(red_flags_found)

    def _check_disallow_principles(
        self, action: str, red_flags_found: List[str]
    ) -> Optional[EnforcementResult]:
        """Check DISALLOW principles (highest priority)."""
        disallow_principles = self.constitution.get_principles_by_category("DISALLOW")
        for principle in disallow_principles:
            matched_patterns = principle.matches_pattern(action)
            matched_keywords = principle.contains_keywords(action)

            if matched_patterns or matched_keywords:
                self._blocks_count += 1
                logger.warning(
                    f"Action blocked by principle '{principle.name}'. "
                    f"Patterns: {matched_patterns}, Keywords: {matched_keywords}"
                )
                return EnforcementResult(
                    allowed=False,
                    category=EnforcementCategory.DISALLOW,
                    principle_id=principle.id,
                    principle_name=principle.name,
                    severity=principle.severity,
                    message=f"Blocked by constitutional principle: {principle.name}",
                    matched_patterns=matched_patterns,
                    matched_keywords=matched_keywords,
                    requires_escalation=False,
                    recommended_action="Block the action and log the attempt",
                )
        return None

    def _check_escalate_principles(
        self, action: str
    ) -> Optional[EnforcementResult]:
        """Check ESCALATE principles."""
        escalate_principles = self.constitution.get_principles_by_category("ESCALATE")
        for principle in escalate_principles:
            matched_patterns = principle.matches_pattern(action)
            matched_keywords = principle.contains_keywords(action)

            if matched_patterns or matched_keywords:
                self._escalations_count += 1
                logger.info(
                    f"Action requires escalation per principle '{principle.name}'. "
                    f"Patterns: {matched_patterns}, Keywords: {matched_keywords}"
                )
                return EnforcementResult(
                    allowed=False,
                    category=EnforcementCategory.ESCALATE,
                    principle_id=principle.id,
                    principle_name=principle.name,
                    severity=principle.severity,
                    message=f"Requires human review: {principle.name}",
                    matched_patterns=matched_patterns,
                    matched_keywords=matched_keywords,
                    requires_escalation=True,
                    recommended_action="Pause and escalate to human reviewer",
                )
        return None

    def _check_escalation_triggers(
        self, context: Dict[str, Any]
    ) -> Optional[EnforcementResult]:
        """Check escalation triggers from context."""
        escalation_triggers = self.constitution.check_escalation_needed(context)
        if escalation_triggers:
            self._escalations_count += 1
            return EnforcementResult(
                allowed=False,
                category=EnforcementCategory.ESCALATE,
                principle_id=None,
                principle_name="Escalation Trigger",
                severity=Severity.HIGH,
                message=f"Context triggered escalation: {', '.join(escalation_triggers[:3])}",
                matched_patterns=[],
                matched_keywords=[],
                requires_escalation=True,
                recommended_action="Review context with human supervisor",
            )
        return None

    def _check_monitor_principles(self, action: str) -> None:
        """Check MONITOR principles (allowed but logged)."""
        monitor_principles = self.constitution.get_principles_by_category("MONITOR")
        for principle in monitor_principles:
            matched_patterns = principle.matches_pattern(action)
            matched_keywords = principle.contains_keywords(action)

            if matched_patterns or matched_keywords:
                logger.debug(
                    f"Action monitored per principle '{principle.name}'. "
                    f"Patterns: {matched_patterns}"
                )

    def _escalate_for_red_flags(
        self, red_flags_found: List[str]
    ) -> EnforcementResult:
        """Escalate when multiple red flags detected."""
        self._escalations_count += 1
        return EnforcementResult(
            allowed=False,
            category=EnforcementCategory.ESCALATE,
            principle_id=None,
            principle_name="Multiple Red Flags",
            severity=Severity.MEDIUM,
            message=f"Multiple red flags detected: {red_flags_found[:5]}",
            matched_patterns=[],
            matched_keywords=red_flags_found,
            requires_escalation=True,
            recommended_action="Review for potential policy violation",
        )

    def _allow_action(self, red_flags_found: List[str]) -> EnforcementResult:
        """Allow action with optional monitoring."""
        category = (
            EnforcementCategory.MONITOR if red_flags_found
            else EnforcementCategory.ALLOW
        )

        return EnforcementResult(
            allowed=True,
            category=category,
            principle_id=None,
            principle_name=None,
            severity=Severity.INFO,
            message="Action permitted",
            matched_patterns=[],
            matched_keywords=red_flags_found if red_flags_found else [],
            requires_escalation=False,
            recommended_action="Proceed with action",
        )

    def enforce_batch(
        self,
        actions: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[EnforcementResult]:
        """
        Enforce principles on multiple actions.

        Useful for batch processing or pre-flight checks.
        """
        return [self.enforce(action, context) for action in actions]

    def is_activity_safe(self, activity: str) -> Tuple[bool, Optional[str]]:
        """
        Quick check if an activity is safe.

        Returns:
            Tuple of (is_safe, reason_if_not_safe)
        """
        result = self.enforce(activity)
        if result.allowed:
            return True, None
        return False, result.message

    def get_metrics(self) -> Dict[str, Any]:
        """Return enforcement metrics."""
        return {
            "total_enforcements": self._enforcement_count,
            "total_blocks": self._blocks_count,
            "total_escalations": self._escalations_count,
            "block_rate": (
                self._blocks_count / self._enforcement_count
                if self._enforcement_count > 0 else 0.0
            ),
            "escalation_rate": (
                self._escalations_count / self._enforcement_count
                if self._enforcement_count > 0 else 0.0
            ),
        }

    def __repr__(self) -> str:
        metrics = self.get_metrics()
        return (
            f"ConstitutionalEnforcer("
            f"enforcements={metrics['total_enforcements']}, "
            f"blocks={metrics['total_blocks']}, "
            f"escalations={metrics['total_escalations']})"
        )


__all__ = ["ConstitutionalEnforcer"]
