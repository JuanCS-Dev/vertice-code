"""
NEXUS Self-Healing Orchestrator

Implements autonomous system healing using Gemini 3 Pro for
intelligent diagnosis and remediation.

Three-phase self-healing cycle:
1. Detection: Real-time anomaly detection
2. Diagnosis: Causal reasoning for root cause analysis
3. Remediation: Autonomous corrective actions
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import HealingAction, HealingRecord

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


DIAGNOSIS_SYSTEM_PROMPT = """You are the Self-Healing Orchestrator of NEXUS, powered by Gemini 3 Pro.

Your role is to diagnose system anomalies and recommend healing actions.
You must perform CAUSAL analysis - understand WHY issues occur, not just WHAT is happening.

For each anomaly, provide:
1. ROOT_CAUSE: Deep analysis of why this issue occurred
2. SEVERITY: 0.0-1.0 rating of how critical this is
3. IMPACT: What systems/users are affected
4. HEALING_ACTION: One of [restart_agent, rollback_code, scale_resources, clear_cache, reset_state, patch_code, notify_operator]
5. PREVENTION: How to prevent this in the future

Be precise and actionable. Your recommendations will be executed automatically.
"""


class SelfHealingOrchestrator:
    """
    Autonomous system healing using Gemini 3 Pro.

    Monitors system health, diagnoses issues, and executes healing actions.
    """

    def __init__(self, config: NexusConfig):
        self.config = config
        self._healing_history: List[HealingRecord] = []
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None
        self._monitoring_active = False

        if GENAI_AVAILABLE:
            try:
                os.environ.setdefault("GOOGLE_CLOUD_PROJECT", config.project_id)
                os.environ.setdefault("GOOGLE_CLOUD_LOCATION", config.location)
                os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
                self._client = genai.Client()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=config.project_id)
                self._healing_collection = self._db.collection(config.firestore_healing_collection)
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}")

    async def start_monitoring(self) -> None:
        """Start continuous health monitoring loop."""
        if self._monitoring_active:
            logger.warning("Monitoring already active")
            return

        self._monitoring_active = True
        logger.info("🏥 Self-healing monitoring started")

        while self._monitoring_active:
            try:
                metrics = await self._collect_system_metrics()
                anomalies = await self._detect_anomalies(metrics)

                for anomaly in anomalies:
                    if anomaly["severity"] >= self.config.anomaly_severity_threshold:
                        await self.heal(anomaly)
                    else:
                        logger.debug(f"Minor anomaly: {anomaly['type']}")

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

            await asyncio.sleep(self.config.health_check_interval_seconds)

    async def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._monitoring_active = False
        logger.info("Self-healing monitoring stopped")

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        # In production, integrate with Cloud Monitoring
        # For now, return simulated metrics
        return {
            "cpu_usage": random.uniform(0.3, 0.9),
            "memory_usage": random.uniform(0.4, 0.8),
            "error_rate": random.uniform(0.0, 0.05),
            "response_time_ms": random.uniform(100, 500),
            "active_agents": random.randint(5, 20),
            "queue_depth": random.randint(0, 100),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _detect_anomalies(
        self,
        metrics: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in system metrics."""
        anomalies = []

        # Error rate check
        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.config.error_rate_threshold:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": min(1.0, error_rate / 0.05),
                    "metric": "error_rate",
                    "value": error_rate,
                    "threshold": self.config.error_rate_threshold,
                    "timestamp": metrics.get("timestamp"),
                }
            )

        # Response time check
        response_time = metrics.get("response_time_ms", 0)
        if response_time > self.config.response_time_threshold_ms:
            anomalies.append(
                {
                    "type": "slow_response",
                    "severity": min(1.0, response_time / 500),
                    "metric": "response_time_ms",
                    "value": response_time,
                    "threshold": self.config.response_time_threshold_ms,
                    "timestamp": metrics.get("timestamp"),
                }
            )

        # CPU spike check
        cpu = metrics.get("cpu_usage", 0)
        if cpu > 0.85:
            anomalies.append(
                {
                    "type": "cpu_spike",
                    "severity": (cpu - 0.85) / 0.15,
                    "metric": "cpu_usage",
                    "value": cpu,
                    "threshold": 0.85,
                    "timestamp": metrics.get("timestamp"),
                }
            )

        return anomalies

    async def heal(self, anomaly: Dict[str, Any]) -> HealingRecord:
        """Execute healing for a detected anomaly."""
        logger.info(f"🔧 Healing: {anomaly['type']} (severity: {anomaly['severity']:.2f})")

        # Diagnose
        diagnosis = await self._diagnose(anomaly)

        # Select and execute healing action
        action = self._select_action(diagnosis)
        success = await self._execute_action(action, anomaly)

        # Record
        record = HealingRecord(
            anomaly_type=anomaly["type"],
            anomaly_severity=anomaly["severity"],
            diagnosis=diagnosis.get("root_cause", "Unknown"),
            action=action,
            success=success,
            metadata={
                "anomaly": anomaly,
                "diagnosis": diagnosis,
            },
        )

        self._healing_history.append(record)

        # Persist
        if self._db:
            try:
                await self._healing_collection.document(record.record_id).set(record.to_dict())
            except Exception as e:
                logger.warning(f"Failed to persist healing record: {e}")

        if success:
            logger.info(f"✅ Healing successful: {action.value}")
        else:
            logger.warning(f"❌ Healing failed: {action.value}")

        return record

    async def _diagnose(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose the anomaly using Gemini 3 Pro."""
        if self._client:
            try:
                return await self._diagnose_with_gemini(anomaly)
            except Exception as e:
                logger.warning(f"Gemini diagnosis failed: {e}")

        # Fallback diagnosis
        return self._fallback_diagnosis(anomaly)

    async def _diagnose_with_gemini(
        self,
        anomaly: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use Gemini 3 Pro for intelligent diagnosis."""
        prompt = f"""Diagnose this system anomaly:

ANOMALY DETECTED:
Type: {anomaly['type']}
Severity: {anomaly['severity']:.2f}
Metric: {anomaly.get('metric', 'N/A')}
Value: {anomaly.get('value', 'N/A')}
Threshold: {anomaly.get('threshold', 'N/A')}
Timestamp: {anomaly.get('timestamp', 'N/A')}

Provide structured diagnosis:
ROOT_CAUSE: [Why this is happening]
SEVERITY: [0.0-1.0]
IMPACT: [What is affected]
HEALING_ACTION: [restart_agent|rollback_code|scale_resources|clear_cache|reset_state|patch_code|notify_operator]
PREVENTION: [How to prevent recurrence]
"""

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=DIAGNOSIS_SYSTEM_PROMPT,
                temperature=self.config.temperature,
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.HIGH,
                ),
            ),
        )

        return self._parse_diagnosis(response.text)

    def _parse_diagnosis(self, response: str) -> Dict[str, Any]:
        """Parse Gemini diagnosis response."""
        lines = response.strip().split("\n")
        result = {
            "root_cause": "Unknown",
            "severity": 0.5,
            "impact": "Unknown",
            "healing_action": "notify_operator",
            "prevention": "Unknown",
        }

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key == "root_cause":
                    result["root_cause"] = value
                elif key == "severity":
                    try:
                        result["severity"] = float(value)
                    except ValueError:
                        pass
                elif key == "impact":
                    result["impact"] = value
                elif key == "healing_action":
                    result["healing_action"] = value.lower()
                elif key == "prevention":
                    result["prevention"] = value

        return result

    def _fallback_diagnosis(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback diagnosis when Gemini unavailable."""
        anomaly_type = anomaly.get("type", "unknown")

        action_map = {
            "high_error_rate": "restart_agent",
            "slow_response": "scale_resources",
            "cpu_spike": "scale_resources",
            "memory_pressure": "clear_cache",
        }

        return {
            "root_cause": f"Detected {anomaly_type} exceeding threshold",
            "severity": anomaly.get("severity", 0.5),
            "impact": "Service degradation possible",
            "healing_action": action_map.get(anomaly_type, "notify_operator"),
            "prevention": "Implement better monitoring and auto-scaling",
        }

    def _select_action(self, diagnosis: Dict[str, Any]) -> HealingAction:
        """Select healing action from diagnosis."""
        action_str = diagnosis.get("healing_action", "notify_operator").lower()

        action_map = {
            "restart_agent": HealingAction.RESTART_AGENT,
            "rollback_code": HealingAction.ROLLBACK_CODE,
            "scale_resources": HealingAction.SCALE_RESOURCES,
            "clear_cache": HealingAction.CLEAR_CACHE,
            "reset_state": HealingAction.RESET_STATE,
            "patch_code": HealingAction.PATCH_CODE,
            "notify_operator": HealingAction.NOTIFY_OPERATOR,
        }

        return action_map.get(action_str, HealingAction.NOTIFY_OPERATOR)

    async def _execute_action(
        self,
        action: HealingAction,
        anomaly: Dict[str, Any],
    ) -> bool:
        """Execute the selected healing action."""
        logger.info(f"Executing healing action: {action.value}")

        # In production, implement actual healing actions
        # For now, simulate with high success rate
        await asyncio.sleep(0.5)  # Simulate execution time

        # Simulated success rate varies by action
        success_rates = {
            HealingAction.RESTART_AGENT: 0.95,
            HealingAction.CLEAR_CACHE: 0.98,
            HealingAction.SCALE_RESOURCES: 0.90,
            HealingAction.RESET_STATE: 0.85,
            HealingAction.ROLLBACK_CODE: 0.80,
            HealingAction.PATCH_CODE: 0.70,
            HealingAction.NOTIFY_OPERATOR: 1.0,
        }

        return random.random() < success_rates.get(action, 0.5)

    async def get_healing_history(
        self,
        limit: int = 50,
    ) -> List[HealingRecord]:
        """Get recent healing history."""
        return sorted(
            self._healing_history,
            key=lambda r: r.timestamp,
            reverse=True,
        )[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get healing orchestrator statistics."""
        total = len(self._healing_history)
        successful = sum(1 for r in self._healing_history if r.success)

        by_action = {}
        for action in HealingAction:
            count = sum(1 for r in self._healing_history if r.action == action)
            by_action[action.value] = count

        return {
            "total_healings": total,
            "successful_healings": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "by_action": by_action,
            "monitoring_active": self._monitoring_active,
            "gemini_available": self._client is not None,
        }
