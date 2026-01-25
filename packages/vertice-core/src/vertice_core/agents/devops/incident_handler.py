"""
AWS-Style Incident Handler

Implements incident investigation and resolution workflow.

Pattern (AWS re:Invent 2025):
1. Build topology map of resources
2. Correlate alerts with topology
3. Check recent deployments
4. Analyze metrics for anomalies
5. Identify root cause
6. Propose remediations (human approval for risky)

Reference:
- AWS DevOps Agent (AWS re:Invent 2025)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Any
import logging

from .types import (
    Alert,
    Incident,
    IncidentStatus,
    InvestigationStep,
    Remediation,
    RootCauseAnalysis,
    RootCauseCategory,
    TopologyNode,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IncidentHandlerMixin:
    """
    Mixin providing AWS-style incident handling.

    Add to DevOpsAgent via multiple inheritance.
    """

    _topology: Dict[str, TopologyNode]
    _incidents: Dict[str, Incident]
    _deployment_history: List[Dict[str, Any]]

    def _init_incident_system(self) -> None:
        """Initialize the incident handling system."""
        self._topology = {}
        self._incidents = {}
        self._deployment_history = []

    def build_topology(
        self,
        services: List[Dict[str, Any]],
    ) -> Dict[str, TopologyNode]:
        """
        Build a topology map of services and their relationships.

        Args:
            services: List of service definitions with dependencies.

        Returns:
            Topology map indexed by service ID.
        """
        if not hasattr(self, "_topology"):
            self._init_incident_system()

        for svc in services:
            node = TopologyNode(
                id=svc["id"],
                name=svc["name"],
                type=svc.get("type", "service"),
                environment=svc.get("environment", "production"),
                dependencies=svc.get("dependencies", []),
                health_status=svc.get("health", "healthy"),
                metrics=svc.get("metrics", {}),
            )
            self._topology[node.id] = node

        logger.info(f"Topology built with {len(self._topology)} nodes")
        return self._topology

    def get_topology(self) -> Dict[str, TopologyNode]:
        """Get the current topology map."""
        if not hasattr(self, "_topology"):
            self._init_incident_system()
        return self._topology

    async def investigate_incident(self, alert: Alert) -> Incident:
        """
        Investigate an incident triggered by an alert.

        Args:
            alert: The triggering alert.

        Returns:
            Incident with investigation results.
        """
        if not hasattr(self, "_incidents"):
            self._init_incident_system()

        incident = Incident(
            id=f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=alert.title,
            severity=alert.severity,
            status=IncidentStatus.INVESTIGATING,
            alerts=[alert],
            affected_services=alert.affected_resources,
            detected_at=alert.triggered_at,
        )
        incident.add_timeline_event(f"Incident created from alert: {alert.id}")

        self._incidents[incident.id] = incident
        logger.info(f"[Incident] Started investigation: {incident.id}")

        step1 = await self._correlate_topology(incident)
        incident.investigation_steps.append(step1)
        incident.add_timeline_event("Topology correlation complete")

        step2 = await self._check_deployments(incident)
        incident.investigation_steps.append(step2)
        incident.add_timeline_event("Deployment check complete")

        step3 = await self._analyze_metrics(incident)
        incident.investigation_steps.append(step3)
        incident.add_timeline_event("Metrics analysis complete")

        incident.root_cause = self._identify_root_cause(incident)
        incident.status = IncidentStatus.IDENTIFIED
        incident.add_timeline_event(f"Root cause identified: {incident.root_cause.category.value}")

        incident.remediations = self._propose_remediations(incident)
        incident.add_timeline_event(f"Proposed {len(incident.remediations)} remediations")

        return incident

    async def _correlate_topology(self, incident: Incident) -> InvestigationStep:
        """Correlate incident with system topology."""
        affected_nodes = []
        upstream_deps = []
        downstream_deps = []

        for svc_id in incident.affected_services:
            if svc_id in self._topology:
                node = self._topology[svc_id]
                affected_nodes.append(node.name)

                for dep_id in node.dependencies:
                    if dep_id in self._topology:
                        upstream_deps.append(self._topology[dep_id].name)

                for other_id, other_node in self._topology.items():
                    if svc_id in other_node.dependencies:
                        downstream_deps.append(other_node.name)

        findings = f"Affected: {affected_nodes}. "
        if upstream_deps:
            findings += f"Upstream dependencies: {upstream_deps}. "
        if downstream_deps:
            findings += f"Downstream impact: {downstream_deps}. "

        return InvestigationStep(
            id="step-topology",
            action="Topology correlation",
            findings=findings or "No topology data available",
            timestamp=datetime.now().isoformat(),
            data_sources=["topology_map"],
            confidence=0.8 if affected_nodes else 0.3,
        )

    async def _check_deployments(self, incident: Incident) -> InvestigationStep:
        """Check recent deployments for potential causes."""
        recent_deployments = []

        for deploy in self._deployment_history[-10:]:
            if deploy.get("service") in incident.affected_services:
                recent_deployments.append(deploy)

        if recent_deployments:
            findings = f"Found {len(recent_deployments)} recent deployments: "
            findings += ", ".join(d.get("version", "unknown") for d in recent_deployments)
            confidence = 0.7
        else:
            findings = "No recent deployments to affected services"
            confidence = 0.5

        return InvestigationStep(
            id="step-deployments",
            action="Check recent deployments",
            findings=findings,
            timestamp=datetime.now().isoformat(),
            data_sources=["deployment_history", "git"],
            confidence=confidence,
        )

    async def _analyze_metrics(self, incident: Incident) -> InvestigationStep:
        """Analyze metrics for anomalies."""
        anomalies = []

        for svc_id in incident.affected_services:
            if svc_id in self._topology:
                metrics = self._topology[svc_id].metrics

                if metrics.get("cpu_percent", 0) > 80:
                    anomalies.append(f"{svc_id}: High CPU ({metrics['cpu_percent']}%)")
                if metrics.get("memory_percent", 0) > 90:
                    anomalies.append(f"{svc_id}: High memory ({metrics['memory_percent']}%)")
                if metrics.get("error_rate", 0) > 5:
                    anomalies.append(f"{svc_id}: High error rate ({metrics['error_rate']}%)")
                if metrics.get("latency_p99", 0) > 1000:
                    anomalies.append(f"{svc_id}: High latency ({metrics['latency_p99']}ms)")

        if anomalies:
            findings = f"Anomalies detected: {'; '.join(anomalies)}"
            confidence = 0.8
        else:
            findings = "No metric anomalies detected"
            confidence = 0.4

        return InvestigationStep(
            id="step-metrics",
            action="Analyze metrics",
            findings=findings,
            timestamp=datetime.now().isoformat(),
            data_sources=["cloudwatch", "prometheus", "datadog"],
            confidence=confidence,
        )

    def _identify_root_cause(self, incident: Incident) -> RootCauseAnalysis:
        """Identify root cause from investigation steps."""
        evidence = []
        for step in incident.investigation_steps:
            if step.confidence > 0.6:
                evidence.append(step.findings)

        all_findings = " ".join(s.findings.lower() for s in incident.investigation_steps)

        if "deployment" in all_findings and "recent" in all_findings:
            category = RootCauseCategory.CODE_CHANGE
            description = "Recent code deployment likely caused the issue"
        elif "cpu" in all_findings or "memory" in all_findings:
            category = RootCauseCategory.RESOURCE_LIMIT
            description = "Resource exhaustion detected"
        elif "upstream" in all_findings or "dependency" in all_findings:
            category = RootCauseCategory.DEPENDENCY
            description = "Upstream dependency failure"
        elif "error rate" in all_findings:
            category = RootCauseCategory.CODE_CHANGE
            description = "Application errors indicate code issue"
        else:
            category = RootCauseCategory.UNKNOWN
            description = "Root cause requires further investigation"

        avg_confidence = sum(s.confidence for s in incident.investigation_steps)
        avg_confidence /= len(incident.investigation_steps) if incident.investigation_steps else 1

        return RootCauseAnalysis(
            category=category,
            description=description,
            confidence=avg_confidence,
            evidence=evidence,
            contributing_factors=[],
            related_changes=[],
        )

    def _propose_remediations(self, incident: Incident) -> List[Remediation]:
        """Propose remediation actions based on root cause."""
        remediations = []

        if not incident.root_cause:
            return remediations

        category = incident.root_cause.category

        if category == RootCauseCategory.CODE_CHANGE:
            remediations.append(
                Remediation(
                    id="rem-rollback",
                    action="rollback",
                    description="Rollback to previous stable version",
                    risk_level="medium",
                    requires_approval=True,
                    estimated_impact="Service restart, brief downtime",
                    rollback_plan="Re-deploy current version if issues persist",
                )
            )

        elif category == RootCauseCategory.RESOURCE_LIMIT:
            remediations.append(
                Remediation(
                    id="rem-scale",
                    action="scale_up",
                    description="Increase resource allocation",
                    risk_level="low",
                    requires_approval=False,
                    estimated_impact="Temporary increased cost",
                    rollback_plan="Scale down after stabilization",
                )
            )

        elif category == RootCauseCategory.DEPENDENCY:
            remediations.append(
                Remediation(
                    id="rem-circuit-breaker",
                    action="enable_circuit_breaker",
                    description="Enable circuit breaker for failing dependency",
                    risk_level="low",
                    requires_approval=False,
                    estimated_impact="Graceful degradation of affected feature",
                    rollback_plan="Disable circuit breaker when dependency recovers",
                )
            )

        remediations.append(
            Remediation(
                id="rem-restart",
                action="restart_service",
                description="Restart affected services",
                risk_level="low",
                requires_approval=False,
                estimated_impact="Brief service interruption",
                rollback_plan="N/A - non-destructive action",
            )
        )

        return remediations

    async def execute_remediation(
        self,
        incident_id: str,
        remediation_id: str,
        approved_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a remediation action with optional approval."""
        if incident_id not in self._incidents:
            return {"success": False, "error": "Incident not found"}

        incident = self._incidents[incident_id]
        remediation = next((r for r in incident.remediations if r.id == remediation_id), None)

        if not remediation:
            return {"success": False, "error": "Remediation not found"}

        if remediation.requires_approval and not approved_by:
            return {
                "success": False,
                "error": "This action requires human approval",
                "requires": "approved_by parameter",
            }

        incident.add_timeline_event(
            f"Executing remediation: {remediation.action}"
            + (f" (approved by {approved_by})" if approved_by else "")
        )

        logger.info(f"[Incident] Executing {remediation.action} for {incident_id}")
        incident.status = IncidentStatus.MITIGATING

        return {
            "success": True,
            "action": remediation.action,
            "incident_id": incident_id,
            "executed_at": datetime.now().isoformat(),
        }

    def resolve_incident(
        self,
        incident_id: str,
        resolution_notes: str,
    ) -> Incident:
        """Mark incident as resolved and calculate MTTR."""
        if incident_id not in self._incidents:
            raise ValueError(f"Incident not found: {incident_id}")

        incident = self._incidents[incident_id]
        incident.resolved_at = datetime.now().isoformat()
        incident.status = IncidentStatus.RESOLVED
        incident.add_timeline_event(f"Resolved: {resolution_notes}")

        detected = datetime.fromisoformat(incident.detected_at)
        resolved = datetime.fromisoformat(incident.resolved_at)
        incident.mttr_seconds = int((resolved - detected).total_seconds())

        logger.info(f"[Incident] {incident_id} resolved. MTTR: {incident.mttr_seconds}s")
        return incident

    def record_deployment(
        self,
        service: str,
        version: str,
        environment: str,
        deployed_by: str,
    ) -> None:
        """Record a deployment for incident correlation."""
        if not hasattr(self, "_deployment_history"):
            self._init_incident_system()

        self._deployment_history.append(
            {
                "service": service,
                "version": version,
                "environment": environment,
                "deployed_by": deployed_by,
                "deployed_at": datetime.now().isoformat(),
            }
        )

    def get_incident_metrics(self) -> Dict[str, Any]:
        """Get incident handling metrics."""
        if not hasattr(self, "_incidents"):
            self._init_incident_system()

        total = len(self._incidents)
        resolved = sum(1 for i in self._incidents.values() if i.status == IncidentStatus.RESOLVED)
        mttr_values = [
            i.mttr_seconds for i in self._incidents.values() if i.mttr_seconds is not None
        ]

        return {
            "total_incidents": total,
            "resolved_incidents": resolved,
            "open_incidents": total - resolved,
            "avg_mttr_seconds": sum(mttr_values) / len(mttr_values) if mttr_values else 0,
            "min_mttr_seconds": min(mttr_values) if mttr_values else 0,
            "max_mttr_seconds": max(mttr_values) if mttr_values else 0,
        }
