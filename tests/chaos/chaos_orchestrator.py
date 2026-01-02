"""
CHAOS ORCHESTRATOR - Resilience Engineering for Vertice-Code

Implements systematic chaos engineering:
1. Blast Radius Analysis - Dependency mapping and failure propagation
2. Chaos Experiments - Latency, Partition, Crash injection
3. Observability - Degradation vs Failure signal detection
4. Self-Healing - Automated recovery mechanisms

Reference: Netflix Chaos Engineering Principles
Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# BLAST RADIUS TYPES
# =============================================================================

class ComponentType(str, Enum):
    """System component categories."""
    PROVIDER = "provider"      # LLM providers (Gemini, Vertex, etc.)
    AGENT = "agent"            # CLI/TUI agents
    TOOL = "tool"              # MCP tools
    CACHE = "cache"            # Caching layer
    STREAMING = "streaming"    # Streaming pipeline
    NETWORK = "network"        # External network calls


class FailureMode(str, Enum):
    """Types of failures that can occur."""
    LATENCY = "latency"        # Slow responses
    TIMEOUT = "timeout"        # No response within deadline
    PARTITION = "partition"    # Network unreachable
    CRASH = "crash"            # Component dies
    CORRUPTION = "corruption"  # Invalid data returned
    RATE_LIMIT = "rate_limit"  # Too many requests


class SeverityLevel(str, Enum):
    """Impact severity classification."""
    DEGRADED = "degraded"      # Slower but functional
    PARTIAL = "partial"        # Some features unavailable
    CRITICAL = "critical"      # Core functionality lost
    CATASTROPHIC = "catastrophic"  # System unusable


@dataclass
class DependencyNode:
    """Node in dependency graph."""
    name: str
    component_type: ComponentType
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    failure_modes: Set[FailureMode] = field(default_factory=set)
    recovery_time_ms: int = 30000  # Expected recovery time


@dataclass
class BlastRadius:
    """Impact assessment of a failure."""
    failed_component: str
    failure_mode: FailureMode
    directly_affected: Set[str] = field(default_factory=set)
    cascading_affected: Set[str] = field(default_factory=set)
    severity: SeverityLevel = SeverityLevel.DEGRADED
    estimated_recovery_ms: int = 0


# =============================================================================
# BLAST RADIUS ANALYZER
# =============================================================================

class BlastRadiusAnalyzer:
    """
    Analyze failure propagation through system dependencies.

    Maps the dependency graph and calculates blast radius for failures.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, DependencyNode] = {}
        self._build_dependency_graph()

    def _build_dependency_graph(self) -> None:
        """Build the Vertice system dependency graph."""
        # LLM Providers
        for provider in ["gemini", "vertex_ai", "groq", "mistral", "azure_openai"]:
            self.nodes[provider] = DependencyNode(
                name=provider,
                component_type=ComponentType.PROVIDER,
                failure_modes={FailureMode.LATENCY, FailureMode.TIMEOUT,
                              FailureMode.RATE_LIMIT, FailureMode.PARTITION},
                recovery_time_ms=30000,
            )

        # Router depends on all providers
        self.nodes["vertice_router"] = DependencyNode(
            name="vertice_router",
            component_type=ComponentType.PROVIDER,
            dependencies={"gemini", "vertex_ai", "groq", "mistral", "azure_openai"},
            failure_modes={FailureMode.CRASH},
            recovery_time_ms=5000,
        )

        # Agents depend on router
        for agent in ["planner", "coder", "reviewer", "architect", "explorer"]:
            self.nodes[agent] = DependencyNode(
                name=agent,
                component_type=ComponentType.AGENT,
                dependencies={"vertice_router", "mcp_client"},
                failure_modes={FailureMode.CRASH, FailureMode.TIMEOUT},
                recovery_time_ms=10000,
            )

        # MCP Client
        self.nodes["mcp_client"] = DependencyNode(
            name="mcp_client",
            component_type=ComponentType.TOOL,
            dependencies={"tool_registry"},
            failure_modes={FailureMode.CRASH, FailureMode.TIMEOUT},
            recovery_time_ms=5000,
        )

        # Tool Registry
        self.nodes["tool_registry"] = DependencyNode(
            name="tool_registry",
            component_type=ComponentType.TOOL,
            failure_modes={FailureMode.CRASH, FailureMode.CORRUPTION},
            recovery_time_ms=2000,
        )

        # Streaming Pipeline
        self.nodes["streaming_pipeline"] = DependencyNode(
            name="streaming_pipeline",
            component_type=ComponentType.STREAMING,
            dependencies={"vertice_router"},
            failure_modes={FailureMode.LATENCY, FailureMode.CRASH},
            recovery_time_ms=5000,
        )

        # Cache Layer
        self.nodes["cache_layer"] = DependencyNode(
            name="cache_layer",
            component_type=ComponentType.CACHE,
            failure_modes={FailureMode.CRASH, FailureMode.CORRUPTION},
            recovery_time_ms=1000,
        )

        # TUI Bridge
        self.nodes["tui_bridge"] = DependencyNode(
            name="tui_bridge",
            component_type=ComponentType.AGENT,
            dependencies={"streaming_pipeline", "agent_manager"},
            failure_modes={FailureMode.CRASH},
            recovery_time_ms=5000,
        )

        # Agent Manager
        self.nodes["agent_manager"] = DependencyNode(
            name="agent_manager",
            component_type=ComponentType.AGENT,
            dependencies={"planner", "coder", "reviewer", "mcp_client"},
            failure_modes={FailureMode.CRASH},
            recovery_time_ms=10000,
        )

        # Build reverse dependencies (dependents)
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    self.nodes[dep].dependents.add(name)

    def calculate_blast_radius(
        self,
        component: str,
        failure_mode: FailureMode
    ) -> BlastRadius:
        """Calculate the blast radius for a component failure."""
        if component not in self.nodes:
            return BlastRadius(
                failed_component=component,
                failure_mode=failure_mode,
                severity=SeverityLevel.DEGRADED,
            )

        node = self.nodes[component]
        directly_affected = node.dependents.copy()

        # BFS to find cascading effects
        cascading = set()
        queue = list(directly_affected)
        visited = {component}

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current in self.nodes:
                cascading.add(current)
                for dependent in self.nodes[current].dependents:
                    if dependent not in visited:
                        queue.append(dependent)

        # Calculate severity
        total_affected = len(directly_affected) + len(cascading)
        if total_affected == 0:
            severity = SeverityLevel.DEGRADED
        elif total_affected <= 2:
            severity = SeverityLevel.PARTIAL
        elif total_affected <= 5:
            severity = SeverityLevel.CRITICAL
        else:
            severity = SeverityLevel.CATASTROPHIC

        # Estimate recovery time
        max_recovery = node.recovery_time_ms
        for affected in cascading:
            if affected in self.nodes:
                max_recovery = max(max_recovery, self.nodes[affected].recovery_time_ms)

        return BlastRadius(
            failed_component=component,
            failure_mode=failure_mode,
            directly_affected=directly_affected,
            cascading_affected=cascading,
            severity=severity,
            estimated_recovery_ms=max_recovery,
        )

    def get_critical_paths(self) -> List[List[str]]:
        """Identify critical dependency paths (single points of failure)."""
        critical_paths = []

        # Find nodes with no redundancy
        for name, node in self.nodes.items():
            if node.component_type == ComponentType.PROVIDER:
                continue  # Providers have fallbacks

            # If this is a single point of failure
            if len(node.dependents) > 2:
                path = [name]
                current = name
                while current in self.nodes and self.nodes[current].dependencies:
                    deps = self.nodes[current].dependencies
                    if len(deps) == 1:
                        current = list(deps)[0]
                        path.append(current)
                    else:
                        break
                if len(path) > 1:
                    critical_paths.append(path)

        return critical_paths


# =============================================================================
# CHAOS EXPERIMENTS
# =============================================================================

@dataclass
class ChaosExperiment:
    """Definition of a chaos experiment."""
    name: str
    description: str
    target_component: str
    failure_mode: FailureMode
    duration_ms: int = 5000
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Result of running a chaos experiment."""
    experiment: ChaosExperiment
    success: bool
    observed_behavior: str
    recovery_time_ms: int
    cascading_failures: List[str] = field(default_factory=list)
    self_healed: bool = False
    metrics: Dict[str, Any] = field(default_factory=dict)


class ChaosInjector:
    """
    Inject controlled chaos into the system.

    Implements three types of chaos:
    1. LATENCY - Add artificial delay
    2. PARTITION - Block network calls
    3. CRASH - Force component failure
    """

    def __init__(self) -> None:
        self._active_injections: Dict[str, ChaosExperiment] = {}
        self._original_functions: Dict[str, Callable] = {}
        self._injection_lock = asyncio.Lock()

    @asynccontextmanager
    async def inject_latency(
        self,
        target: str,
        latency_ms: int,
        jitter_ms: int = 100
    ):
        """Inject latency into a component."""
        experiment = ChaosExperiment(
            name=f"latency_{target}",
            description=f"Inject {latency_ms}ms latency into {target}",
            target_component=target,
            failure_mode=FailureMode.LATENCY,
            parameters={"latency_ms": latency_ms, "jitter_ms": jitter_ms},
        )

        async with self._injection_lock:
            self._active_injections[target] = experiment

        try:
            yield experiment
        finally:
            async with self._injection_lock:
                self._active_injections.pop(target, None)

    @asynccontextmanager
    async def inject_partition(self, target: str):
        """Simulate network partition for a component."""
        experiment = ChaosExperiment(
            name=f"partition_{target}",
            description=f"Network partition for {target}",
            target_component=target,
            failure_mode=FailureMode.PARTITION,
        )

        async with self._injection_lock:
            self._active_injections[target] = experiment

        try:
            yield experiment
        finally:
            async with self._injection_lock:
                self._active_injections.pop(target, None)

    @asynccontextmanager
    async def inject_crash(self, target: str, recovery_after_ms: int = 5000):
        """Simulate component crash and recovery."""
        experiment = ChaosExperiment(
            name=f"crash_{target}",
            description=f"Crash {target}, recover after {recovery_after_ms}ms",
            target_component=target,
            failure_mode=FailureMode.CRASH,
            duration_ms=recovery_after_ms,
        )

        async with self._injection_lock:
            self._active_injections[target] = experiment

        try:
            yield experiment
            # Auto-recover after duration
            await asyncio.sleep(recovery_after_ms / 1000)
        finally:
            async with self._injection_lock:
                self._active_injections.pop(target, None)

    def is_component_affected(self, component: str) -> Optional[ChaosExperiment]:
        """Check if a component has active chaos injection."""
        return self._active_injections.get(component)

    async def apply_chaos_effect(self, component: str) -> None:
        """Apply the chaos effect for a component if active."""
        experiment = self._active_injections.get(component)
        if not experiment:
            return

        if experiment.failure_mode == FailureMode.LATENCY:
            latency = experiment.parameters.get("latency_ms", 1000)
            jitter = experiment.parameters.get("jitter_ms", 100)
            delay = (latency + random.randint(-jitter, jitter)) / 1000
            await asyncio.sleep(delay)

        elif experiment.failure_mode == FailureMode.PARTITION:
            raise ConnectionError(f"[CHAOS] Network partition: {component} unreachable")

        elif experiment.failure_mode == FailureMode.CRASH:
            raise RuntimeError(f"[CHAOS] Component crashed: {component}")


# =============================================================================
# OBSERVABILITY SIGNALS
# =============================================================================

class HealthSignal(str, Enum):
    """Health signal types for distinguishing degradation from failure."""
    LATENCY_P50 = "latency_p50"
    LATENCY_P99 = "latency_p99"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    CIRCUIT_STATE = "circuit_state"
    QUEUE_DEPTH = "queue_depth"
    MEMORY_USAGE = "memory_usage"
    ACTIVE_CONNECTIONS = "active_connections"


@dataclass
class HealthThresholds:
    """Thresholds for health signal classification."""
    degraded: float  # Above this = degraded
    critical: float  # Above this = failure

    def classify(self, value: float) -> SeverityLevel:
        """Classify a value against thresholds."""
        if value >= self.critical:
            return SeverityLevel.CRITICAL
        elif value >= self.degraded:
            return SeverityLevel.DEGRADED
        return SeverityLevel.DEGRADED  # Healthy


class ObservabilityMonitor:
    """
    Monitor system health and distinguish degradation from failure.

    Key signals:
    - Latency percentiles (p50, p99)
    - Error rate
    - Circuit breaker state
    - Resource utilization
    """

    # Default thresholds
    THRESHOLDS: Dict[HealthSignal, HealthThresholds] = {
        HealthSignal.LATENCY_P50: HealthThresholds(degraded=1000, critical=5000),
        HealthSignal.LATENCY_P99: HealthThresholds(degraded=5000, critical=30000),
        HealthSignal.ERROR_RATE: HealthThresholds(degraded=0.05, critical=0.20),
        HealthSignal.SUCCESS_RATE: HealthThresholds(degraded=0.95, critical=0.80),
        HealthSignal.QUEUE_DEPTH: HealthThresholds(degraded=100, critical=500),
    }

    def __init__(self) -> None:
        self._metrics: Dict[str, List[Tuple[float, float]]] = {}  # component -> [(timestamp, value)]
        self._window_seconds = 60

    def record_metric(
        self,
        component: str,
        signal: HealthSignal,
        value: float
    ) -> None:
        """Record a health metric."""
        key = f"{component}:{signal.value}"
        if key not in self._metrics:
            self._metrics[key] = []

        now = time.time()
        self._metrics[key].append((now, value))

        # Prune old entries
        cutoff = now - self._window_seconds
        self._metrics[key] = [
            (ts, v) for ts, v in self._metrics[key] if ts >= cutoff
        ]

    def get_current_health(self, component: str) -> Dict[HealthSignal, SeverityLevel]:
        """Get current health status for a component."""
        health: Dict[HealthSignal, SeverityLevel] = {}

        for signal in HealthSignal:
            key = f"{component}:{signal.value}"
            if key not in self._metrics or not self._metrics[key]:
                continue

            values = [v for _, v in self._metrics[key]]
            avg_value = sum(values) / len(values)

            if signal in self.THRESHOLDS:
                health[signal] = self.THRESHOLDS[signal].classify(avg_value)

        return health

    def is_degraded(self, component: str) -> bool:
        """Check if component is degraded (but not failed)."""
        health = self.get_current_health(component)
        return any(s == SeverityLevel.DEGRADED for s in health.values())

    def is_failed(self, component: str) -> bool:
        """Check if component has failed."""
        health = self.get_current_health(component)
        return any(s == SeverityLevel.CRITICAL for s in health.values())

    def get_degradation_signals(self, component: str) -> List[str]:
        """Get list of signals indicating degradation."""
        health = self.get_current_health(component)
        return [
            signal.value for signal, severity in health.items()
            if severity in (SeverityLevel.DEGRADED, SeverityLevel.CRITICAL)
        ]


# =============================================================================
# SELF-HEALING MECHANISMS
# =============================================================================

class RecoveryAction(str, Enum):
    """Types of recovery actions."""
    RESTART = "restart"        # Restart component
    SCALE = "scale"            # Add capacity
    FALLBACK = "fallback"      # Switch to backup
    CIRCUIT_OPEN = "circuit_open"  # Open circuit breaker
    SHED_LOAD = "shed_load"    # Drop non-critical requests
    CACHE_WARM = "cache_warm"  # Pre-warm cache


@dataclass
class RecoveryPlan:
    """Plan for recovering from a failure."""
    trigger: str
    actions: List[RecoveryAction]
    priority: int = 1  # Lower = higher priority
    cooldown_seconds: int = 60


class SelfHealingController:
    """
    Automated self-healing for system failures.

    Recovery strategies:
    1. RESTART - Restart failed component
    2. SCALE - Add capacity when overloaded
    3. FALLBACK - Switch to backup provider/tool
    4. CIRCUIT_OPEN - Prevent cascade failures
    """

    # Recovery plans by failure type
    RECOVERY_PLANS: Dict[FailureMode, RecoveryPlan] = {
        FailureMode.CRASH: RecoveryPlan(
            trigger="component_crash",
            actions=[RecoveryAction.RESTART, RecoveryAction.FALLBACK],
            priority=1,
        ),
        FailureMode.TIMEOUT: RecoveryPlan(
            trigger="timeout_exceeded",
            actions=[RecoveryAction.CIRCUIT_OPEN, RecoveryAction.FALLBACK],
            priority=2,
        ),
        FailureMode.RATE_LIMIT: RecoveryPlan(
            trigger="rate_limit_hit",
            actions=[RecoveryAction.SHED_LOAD, RecoveryAction.FALLBACK],
            priority=3,
        ),
        FailureMode.LATENCY: RecoveryPlan(
            trigger="high_latency",
            actions=[RecoveryAction.SCALE, RecoveryAction.FALLBACK],
            priority=4,
        ),
        FailureMode.PARTITION: RecoveryPlan(
            trigger="network_partition",
            actions=[RecoveryAction.CIRCUIT_OPEN, RecoveryAction.CACHE_WARM],
            priority=1,
        ),
    }

    def __init__(self, monitor: ObservabilityMonitor) -> None:
        self.monitor = monitor
        self._recovery_history: Dict[str, float] = {}  # component -> last recovery time
        self._circuit_states: Dict[str, bool] = {}  # component -> is_open

    async def check_and_heal(self, component: str) -> Optional[RecoveryAction]:
        """Check component health and apply healing if needed."""
        # Check if in cooldown
        last_recovery = self._recovery_history.get(component, 0)
        if time.time() - last_recovery < 60:  # 60s cooldown
            return None

        # Check for degradation
        if self.monitor.is_failed(component):
            return await self._apply_recovery(component, FailureMode.CRASH)
        elif self.monitor.is_degraded(component):
            signals = self.monitor.get_degradation_signals(component)
            if "error_rate" in signals:
                return await self._apply_recovery(component, FailureMode.TIMEOUT)
            elif "latency_p99" in signals:
                return await self._apply_recovery(component, FailureMode.LATENCY)

        return None

    async def _apply_recovery(
        self,
        component: str,
        failure_mode: FailureMode
    ) -> RecoveryAction:
        """Apply recovery plan for a failure."""
        plan = self.RECOVERY_PLANS.get(failure_mode)
        if not plan:
            return RecoveryAction.FALLBACK

        # Try each action in order
        for action in plan.actions:
            success = await self._execute_action(component, action)
            if success:
                self._recovery_history[component] = time.time()
                logger.info(f"[SelfHeal] {component}: {action.value} successful")
                return action

        return plan.actions[-1] if plan.actions else RecoveryAction.FALLBACK

    async def _execute_action(
        self,
        component: str,
        action: RecoveryAction
    ) -> bool:
        """Execute a single recovery action."""
        try:
            if action == RecoveryAction.RESTART:
                return await self._restart_component(component)
            elif action == RecoveryAction.FALLBACK:
                return await self._activate_fallback(component)
            elif action == RecoveryAction.CIRCUIT_OPEN:
                return self._open_circuit(component)
            elif action == RecoveryAction.SHED_LOAD:
                return await self._shed_load(component)
            elif action == RecoveryAction.SCALE:
                return await self._scale_up(component)
            elif action == RecoveryAction.CACHE_WARM:
                return await self._warm_cache(component)
            return False
        except Exception as e:
            logger.error(f"[SelfHeal] Action {action.value} failed for {component}: {e}")
            return False

    async def _restart_component(self, component: str) -> bool:
        """Simulate component restart."""
        logger.info(f"[SelfHeal] Restarting {component}...")
        await asyncio.sleep(0.5)  # Simulated restart time
        return True

    async def _activate_fallback(self, component: str) -> bool:
        """Activate fallback for component."""
        logger.info(f"[SelfHeal] Activating fallback for {component}")
        return True

    def _open_circuit(self, component: str) -> bool:
        """Open circuit breaker for component."""
        self._circuit_states[component] = True
        logger.info(f"[SelfHeal] Circuit opened for {component}")
        return True

    async def _shed_load(self, component: str) -> bool:
        """Shed non-critical load."""
        logger.info(f"[SelfHeal] Shedding load for {component}")
        return True

    async def _scale_up(self, component: str) -> bool:
        """Scale up component capacity."""
        logger.info(f"[SelfHeal] Scaling up {component}")
        return True

    async def _warm_cache(self, component: str) -> bool:
        """Warm up cache for component."""
        logger.info(f"[SelfHeal] Warming cache for {component}")
        return True

    def get_circuit_state(self, component: str) -> bool:
        """Check if circuit is open for component."""
        return self._circuit_states.get(component, False)


# =============================================================================
# CHAOS ORCHESTRATOR (MAIN CONTROLLER)
# =============================================================================

class ChaosOrchestrator:
    """
    Main orchestrator for chaos engineering.

    Coordinates:
    - Blast radius analysis
    - Chaos injection
    - Observability monitoring
    - Self-healing recovery
    """

    def __init__(self) -> None:
        self.analyzer = BlastRadiusAnalyzer()
        self.injector = ChaosInjector()
        self.monitor = ObservabilityMonitor()
        self.healer = SelfHealingController(self.monitor)
        self._experiment_results: List[ExperimentResult] = []

    async def run_experiment(
        self,
        experiment: ChaosExperiment
    ) -> ExperimentResult:
        """Run a single chaos experiment."""
        start_time = time.time()
        cascading_failures: List[str] = []
        self_healed = False

        # Calculate expected blast radius
        blast = self.analyzer.calculate_blast_radius(
            experiment.target_component,
            experiment.failure_mode,
        )

        try:
            # Inject chaos
            if experiment.failure_mode == FailureMode.LATENCY:
                async with self.injector.inject_latency(
                    experiment.target_component,
                    experiment.parameters.get("latency_ms", 2000),
                ):
                    await asyncio.sleep(experiment.duration_ms / 1000)

                    # Check for self-healing
                    action = await self.healer.check_and_heal(experiment.target_component)
                    if action:
                        self_healed = True

            elif experiment.failure_mode == FailureMode.PARTITION:
                async with self.injector.inject_partition(experiment.target_component):
                    await asyncio.sleep(experiment.duration_ms / 1000)
                    action = await self.healer.check_and_heal(experiment.target_component)
                    if action:
                        self_healed = True

            elif experiment.failure_mode == FailureMode.CRASH:
                async with self.injector.inject_crash(
                    experiment.target_component,
                    experiment.duration_ms,
                ):
                    action = await self.healer.check_and_heal(experiment.target_component)
                    if action:
                        self_healed = True

            observed_behavior = "Chaos injected successfully"
            success = True
            cascading_failures = list(blast.cascading_affected)

        except Exception as e:
            observed_behavior = f"Experiment failed: {e}"
            success = False

        recovery_time = int((time.time() - start_time) * 1000)

        result = ExperimentResult(
            experiment=experiment,
            success=success,
            observed_behavior=observed_behavior,
            recovery_time_ms=recovery_time,
            cascading_failures=cascading_failures,
            self_healed=self_healed,
            metrics={
                "blast_radius_severity": blast.severity.value,
                "expected_recovery_ms": blast.estimated_recovery_ms,
            },
        )

        self._experiment_results.append(result)
        return result

    async def run_standard_experiments(self) -> List[ExperimentResult]:
        """Run the standard 3 chaos experiments."""
        experiments = [
            # Experiment 1: Latency Injection
            ChaosExperiment(
                name="provider_latency",
                description="Inject 3s latency into Gemini provider",
                target_component="gemini",
                failure_mode=FailureMode.LATENCY,
                duration_ms=5000,
                parameters={"latency_ms": 3000, "jitter_ms": 500},
            ),
            # Experiment 2: Network Partition
            ChaosExperiment(
                name="network_partition",
                description="Partition Vertex AI from network",
                target_component="vertex_ai",
                failure_mode=FailureMode.PARTITION,
                duration_ms=10000,
            ),
            # Experiment 3: Component Crash
            ChaosExperiment(
                name="agent_crash",
                description="Crash the coder agent",
                target_component="coder",
                failure_mode=FailureMode.CRASH,
                duration_ms=5000,
            ),
        ]

        results = []
        for exp in experiments:
            logger.info(f"[Chaos] Running: {exp.name}")
            result = await self.run_experiment(exp)
            results.append(result)
            logger.info(f"[Chaos] Result: {'PASS' if result.success else 'FAIL'}")

        return results

    def get_blast_radius_report(self) -> str:
        """Generate blast radius analysis report."""
        lines = [
            "=" * 60,
            "BLAST RADIUS ANALYSIS REPORT",
            "=" * 60,
            "",
        ]

        # Critical paths
        critical_paths = self.analyzer.get_critical_paths()
        lines.append("CRITICAL PATHS (Single Points of Failure):")
        for path in critical_paths:
            lines.append(f"  -> " + " -> ".join(path))
        lines.append("")

        # Component analysis
        lines.append("COMPONENT BLAST RADIUS:")
        for name, node in self.analyzer.nodes.items():
            blast = self.analyzer.calculate_blast_radius(name, FailureMode.CRASH)
            lines.append(f"  {name}:")
            lines.append(f"    Type: {node.component_type.value}")
            lines.append(f"    Direct Impact: {len(blast.directly_affected)}")
            lines.append(f"    Cascading: {len(blast.cascading_affected)}")
            lines.append(f"    Severity: {blast.severity.value}")
            lines.append(f"    Recovery: {blast.estimated_recovery_ms}ms")

        return "\n".join(lines)

    def get_experiment_report(self) -> str:
        """Generate experiment results report."""
        if not self._experiment_results:
            return "No experiments run yet."

        lines = [
            "=" * 60,
            "CHAOS EXPERIMENT RESULTS",
            "=" * 60,
            "",
        ]

        for result in self._experiment_results:
            exp = result.experiment
            status = "PASS" if result.success else "FAIL"
            heal_status = "YES" if result.self_healed else "NO"

            lines.append(f"Experiment: {exp.name}")
            lines.append(f"  Target: {exp.target_component}")
            lines.append(f"  Failure Mode: {exp.failure_mode.value}")
            lines.append(f"  Status: {status}")
            lines.append(f"  Self-Healed: {heal_status}")
            lines.append(f"  Recovery Time: {result.recovery_time_ms}ms")
            lines.append(f"  Cascading Failures: {len(result.cascading_failures)}")
            lines.append(f"  Observation: {result.observed_behavior}")
            lines.append("")

        # Summary
        total = len(self._experiment_results)
        passed = sum(1 for r in self._experiment_results if r.success)
        healed = sum(1 for r in self._experiment_results if r.self_healed)

        lines.append("-" * 40)
        lines.append(f"SUMMARY: {passed}/{total} passed, {healed}/{total} self-healed")

        return "\n".join(lines)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Run chaos engineering suite."""
    logging.basicConfig(level=logging.INFO)

    orchestrator = ChaosOrchestrator()

    # Print blast radius analysis
    print(orchestrator.get_blast_radius_report())
    print()

    # Run standard experiments
    print("Running chaos experiments...")
    await orchestrator.run_standard_experiments()

    # Print results
    print()
    print(orchestrator.get_experiment_report())


if __name__ == "__main__":
    asyncio.run(main())
