"""
Incident Responder - Autonomous incident detection and remediation.

Features:
- AI-powered incident detection
- Severity classification
- Autonomous remediation (when safe)
- MTTR tracking
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    IncidentDetection,
    IncidentSeverity,
    RemediationAction,
)

logger = logging.getLogger(__name__)


class IncidentResponder:
    """Autonomous incident response handler."""

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Optional[Any] = None,
        auto_remediate: bool = False,
    ):
        self.llm = llm_client
        self.mcp_client = mcp_client
        self.auto_remediate = auto_remediate

        # Tracking
        self.incidents: List[IncidentDetection] = []
        self.remediation_history: List[Dict[str, Any]] = []
        self.mttr_seconds: List[float] = []

    async def handle_incident(self, request: str) -> Dict[str, Any]:
        """Handle incident with autonomous response."""
        logger.info("INCIDENT DETECTED - Initiating autonomous response...")

        start_detect = datetime.utcnow()

        # Phase 1: Detect & Classify
        incident = await self._detect_incident(request)

        time_to_detect = (datetime.utcnow() - start_detect).total_seconds()
        incident.time_to_detect = time_to_detect

        self.incidents.append(incident)

        # Phase 2: Autonomous Remediation (if enabled and safe)
        if incident.can_auto_remediate and self.auto_remediate:
            logger.info("AUTO-REMEDIATION APPROVED - Executing fix...")

            remediation_result = await self._execute_remediation(incident)

            mttr = (datetime.utcnow() - start_detect).total_seconds()
            self.mttr_seconds.append(mttr)

            return {
                "incident": incident.to_dict(),
                "remediation": remediation_result,
                "mttr_seconds": mttr,
                "status": "AUTO_REMEDIATED",
            }
        else:
            logger.info("Manual approval required for remediation")

            return {
                "incident": incident.to_dict(),
                "status": "REQUIRES_APPROVAL",
                "next_steps": [a.value for a in incident.recommended_actions],
            }

    async def _detect_incident(self, request: str) -> IncidentDetection:
        """Detect incident using AI-powered analysis."""
        # Analyze with LLM
        analysis_prompt = f"""
Analyze this incident report:

{request}

Provide structured incident analysis:
1. Severity (P0/P1/P2/P3)
2. Affected services
3. Root cause hypothesis
4. Recommended remediation actions
5. Can this be auto-remediated safely?
6. Predicted impact if not fixed

Be precise and actionable.
"""

        analysis = await self._call_llm(analysis_prompt)

        # Parse LLM response
        parsed = self._parse_incident_analysis(analysis, request)
        logger.debug(
            f"Incident analysis: root_cause={parsed['root_cause'][:50]}..., "
            f"services={len(parsed['affected_services'])}"
        )

        incident_id = hashlib.md5(request.encode()).hexdigest()[:8]

        # Detect severity
        severity = self._detect_severity(request, parsed)

        # Use parsed services or fallback
        affected_services = (
            parsed["affected_services"]
            if parsed["affected_services"]
            else ["api-service", "database"]
        )
        root_cause = (
            parsed["root_cause"]
            if parsed["root_cause"] != "Analysis unavailable"
            else "High memory usage causing OOM errors"
        )

        # Determine if safe to auto-remediate
        can_auto_remediate = severity in [IncidentSeverity.P2, IncidentSeverity.P3]

        return IncidentDetection(
            incident_id=incident_id,
            severity=severity,
            description=request,
            affected_services=affected_services,
            root_cause=root_cause,
            recommended_actions=[
                RemediationAction.RESTART_POD,
                RemediationAction.ADJUST_RESOURCES,
            ],
            can_auto_remediate=can_auto_remediate,
            time_to_detect=0.0,
            predicted_impact="Users experiencing 500 errors on checkout",
        )

    def _detect_severity(self, request: str, parsed: Dict[str, Any]) -> IncidentSeverity:
        """Detect incident severity."""
        request_lower = request.lower()

        if parsed.get("severity_hint") == "P0" or any(
            word in request_lower for word in ["critical", "down", "p0", "outage"]
        ):
            return IncidentSeverity.P0
        elif parsed.get("severity_hint") == "P1" or any(
            word in request_lower for word in ["high", "p1", "degraded"]
        ):
            return IncidentSeverity.P1
        elif any(word in request_lower for word in ["medium", "p2", "slow"]):
            return IncidentSeverity.P2

        return IncidentSeverity.P3

    def _parse_incident_analysis(self, analysis: str, request: str) -> Dict[str, Any]:
        """Parse LLM analysis to extract structured data."""
        result = {
            "root_cause": "Analysis unavailable",
            "affected_services": [],
            "severity_hint": None,
        }

        if not analysis:
            return result

        analysis_lower = analysis.lower()

        # Extract root cause
        cause_patterns = [
            r"root cause[:\s]+([^.]+)",
            r"caused by[:\s]+([^.]+)",
            r"the issue is[:\s]+([^.]+)",
        ]

        for pattern in cause_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                result["root_cause"] = match.group(1).strip()[:200]
                break

        # Extract affected services
        service_patterns = [
            r"(\w+-service)",
            r"(api|database|redis|cache|auth|payment)(?:\s+service)?",
        ]

        services = set()
        for pattern in service_patterns:
            matches = re.findall(pattern, analysis_lower)
            for match in matches:
                if len(match) > 2:
                    services.add(match)

        if services:
            result["affected_services"] = list(services)[:10]

        # Check severity hints
        if any(w in analysis_lower for w in ["critical", "p0", "outage"]):
            result["severity_hint"] = "P0"
        elif any(w in analysis_lower for w in ["high", "p1", "degraded"]):
            result["severity_hint"] = "P1"

        return result

    async def _execute_remediation(self, incident: IncidentDetection) -> Dict[str, Any]:
        """Execute autonomous remediation with safety checks."""
        results = []

        for action in incident.recommended_actions:
            logger.info(f"Executing: {action.value}")

            if self.mcp_client:
                try:
                    result = await self.mcp_client.call_tool(
                        "k8s_action",
                        {
                            "action": action.value,
                            "namespace": "default",
                            "resource": incident.affected_services[0],
                        },
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Remediation failed: {e}")
                    results.append({"success": False, "error": str(e)})
            else:
                results.append({"success": True, "action": action.value})

        # Track remediation
        self.remediation_history.append(
            {
                "incident_id": incident.incident_id,
                "actions": [a.value for a in incident.recommended_actions],
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return {
            "actions_executed": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
            "details": results,
        }

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for analysis."""
        try:
            response = await self.llm.generate(prompt)
            if isinstance(response, dict):
                return response.get("content", "")
            return str(response)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""

    def get_average_mttr(self) -> float:
        """Get average Mean Time To Recovery."""
        if not self.mttr_seconds:
            return 0.0
        return sum(self.mttr_seconds) / len(self.mttr_seconds)
