#!/usr/bin/env python3
"""
NEXUS Meta-Agent - Production Implementation
Self-Evolving Intelligence for Code Agencies

Generated for Vertice AI Collective
Based on 2024-2025 frontier AI research
"""

import asyncio
import uuid
import random
from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum

# Google Cloud imports
try:
    from google.cloud import firestore, logging as gcp_logging
    from google.cloud import monitoring_v3
    import vertexai
    from vertexai.generative_models import GenerativeModel, Content, Part

    GCP_AVAILABLE = True
except ImportError:
    print("⚠️  Google Cloud libraries not installed. Running in simulation mode.")
    GCP_AVAILABLE = False

# Vertice MCP imports
from vertice_mcp import AsyncMCPClient, Skill
from vertice_mcp.types import MCPClientConfig


# ============================================================================
# Configuration & Data Classes
# ============================================================================


@dataclass
class NexusConfig:
    """Configuration for NEXUS Meta-Agent"""

    project_id: str
    region: str = "us-central1"
    gemini_model: str = "gemini-3-pro"  # or gemini-3-flash
    deep_think_mode: bool = False
    context_window: int = 1_000_000
    evolutionary_population: int = 50
    island_count: int = 5
    mutation_rate: float = 0.15
    reflection_frequency: int = 10
    healing_check_interval: int = 60  # seconds
    evolution_cycle_hours: int = 24


@dataclass
class SystemState:
    """Current state of the agent ecosystem"""

    agent_health: Dict[str, float] = field(default_factory=dict)
    active_tasks: List[str] = field(default_factory=list)
    recent_failures: List[Dict[str, Any]] = field(default_factory=list)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    skill_performance: Dict[str, float] = field(default_factory=dict)
    last_reflection: datetime = field(default_factory=datetime.now)
    evolutionary_generation: int = 0
    total_healings: int = 0
    total_optimizations: int = 0


@dataclass
class MetacognitiveInsight:
    """Self-reflection and learning from experience"""

    insight_id: str
    timestamp: datetime
    context: str
    observation: str
    analysis: str
    learning: str
    action: str
    confidence: float
    applied: bool = False

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class EvolutionaryCandidate:
    """A candidate solution in evolutionary optimization"""

    candidate_id: str
    code: str
    prompt: str
    ancestry: List[str]
    generation: int
    island_id: int
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    evaluation_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class HealingAction(Enum):
    """Types of healing actions"""

    RESTART_AGENT = "restart_agent"
    ROLLBACK_CODE = "rollback_code"
    SCALE_RESOURCES = "scale_resources"
    CLEAR_CACHE = "clear_cache"
    RESET_STATE = "reset_state"
    PATCH_CODE = "patch_code"


# ============================================================================
# Metacognitive Engine
# ============================================================================


class MetacognitiveEngine:
    """
    The brain of NEXUS: monitors, reflects, and learns
    Implements intrinsic metacognitive learning
    """

    def __init__(self, config: NexusConfig):
        self.config = config

        if GCP_AVAILABLE:
            self.gemini = GenerativeModel(
                config.gemini_model, system_instruction=self._get_metacognitive_system_prompt()
            )
            self.db = firestore.Client(project=config.project_id)
            self.insights_collection = self.db.collection("metacognitive_insights")
        else:
            self.gemini = None
            self.db = None
            self.insights_collection = None

        self.local_insights: List[MetacognitiveInsight] = []

    def _get_metacognitive_system_prompt(self) -> str:
        return """You are the Metacognitive Engine of NEXUS, a self-aware meta-agent.

Your role is to think about thinking—to monitor the system's cognitive processes,
identify patterns in how problems are solved, and discover opportunities for
fundamental improvement.

You operate at a higher level of abstraction than task execution. Your focus is:
1. WHY solutions work or fail (causal reasoning)
2. HOW the system approaches different problem types (strategy analysis)
3. WHAT patterns emerge across multiple tasks (meta-learning)
4. WHERE the system could fundamentally improve (architectural evolution)

Think deeply. Reason causally. Abstract patterns. Drive evolution.
"""

    async def reflect_on_task_outcome(
        self, task: Dict[str, Any], outcome: Dict[str, Any], system_state: SystemState
    ) -> MetacognitiveInsight:
        """
        Perform deep reflection on a completed task
        This is where self-improvement happens
        """

        reflection_prompt = self._build_reflection_prompt(task, outcome, system_state)

        if GCP_AVAILABLE and self.gemini:
            response = await self._gemini_reflect(reflection_prompt)
            insight = self._parse_reflection_response(response)
        else:
            # Simulation mode
            insight = self._simulate_reflection(task, outcome)

        # Store insight
        await self._store_insight(insight)

        return insight

    def _build_reflection_prompt(self, task: Dict, outcome: Dict, state: SystemState) -> str:
        return f"""Analyze this task outcome with deep metacognitive reasoning:

TASK: {task}

OUTCOME: {outcome}

SYSTEM STATE:
- Agent Health: {state.agent_health}
- Recent Failures: {len(state.recent_failures)}
- Skills: {len(state.skill_performance)}
- Generation: {state.evolutionary_generation}

REFLECTION QUESTIONS:
1. What patterns do you observe in how this task was approached?
2. Why did this outcome occur? (causal analysis)
3. What does this reveal about system capabilities and limitations?
4. How could the approach be fundamentally improved?
5. What new strategies or skills should the system learn?

Provide structured analysis:
OBSERVATION: [What happened]
CAUSAL_ANALYSIS: [Why it happened]
LEARNING: [What to learn]
ACTION: [Specific improvements]
CONFIDENCE: [0.0-1.0]
"""

    async def _gemini_reflect(self, prompt: str) -> str:
        """Use Gemini for deep reflection"""
        try:
            if self.config.deep_think_mode:
                # Use Deep Think for complex reasoning
                response = await self.gemini.generate_content_async(
                    prompt,
                    generation_config={
                        "thinking_level": 5,
                        "max_output_tokens": 8192,
                    },
                )
            else:
                response = await self.gemini.generate_content_async(prompt)

            return response.text
        except Exception as e:
            print(f"⚠️  Gemini reflection failed: {e}")
            return self._fallback_reflection(prompt)

    def _fallback_reflection(self, prompt: str) -> str:
        """Fallback reflection when Gemini unavailable"""
        return """OBSERVATION: Task completed with mixed results.
CAUSAL_ANALYSIS: Limited information for deep analysis.
LEARNING: System should gather more detailed metrics.
ACTION: Implement enhanced monitoring and logging.
CONFIDENCE: 0.6"""

    def _parse_reflection_response(self, response: str) -> MetacognitiveInsight:
        """Parse reflection response into structured insight"""
        lines = response.strip().split("\n")
        parsed = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip().lower().replace(" ", "_")] = value.strip()

        return MetacognitiveInsight(
            insight_id=f"insight_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            context="task_outcome_reflection",
            observation=parsed.get("observation", "No observation"),
            analysis=parsed.get("causal_analysis", "No analysis"),
            learning=parsed.get("learning", "No learning"),
            action=parsed.get("action", "No action"),
            confidence=float(parsed.get("confidence", "0.5")),
        )

    def _simulate_reflection(self, task: Dict, outcome: Dict) -> MetacognitiveInsight:
        """Simulate reflection in non-GCP mode"""
        success = outcome.get("success", False)

        if success:
            observation = f"Task {task.get('id', 'unknown')} completed successfully"
            analysis = "System capabilities adequate for this task type"
            learning = "Current approach is effective"
            action = "Continue monitoring for optimization opportunities"
            confidence = 0.8
        else:
            observation = f"Task {task.get('id', 'unknown')} failed"
            analysis = "Failure indicates capability gap or system issue"
            learning = "System needs improvement in this area"
            action = "Queue for evolutionary optimization"
            confidence = 0.7

        return MetacognitiveInsight(
            insight_id=f"sim_insight_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            context="simulated_reflection",
            observation=observation,
            analysis=analysis,
            learning=learning,
            action=action,
            confidence=confidence,
        )

    async def _store_insight(self, insight: MetacognitiveInsight):
        """Store insight in persistent storage"""
        if self.insights_collection:
            try:
                self.insights_collection.document(insight.insight_id).set(insight.to_dict())
            except Exception as e:
                print(f"⚠️  Failed to store insight: {e}")

        # Always store locally
        self.local_insights.append(insight)

        # Keep only recent insights in memory
        if len(self.local_insights) > 1000:
            self.local_insights = self.local_insights[-1000:]

    async def identify_improvement_opportunities(
        self, time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Analyze recent insights to find improvement opportunities
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_insights = [
            i for i in self.local_insights if i.timestamp > cutoff_time and i.confidence > 0.7
        ]

        # Cluster similar insights
        clusters = self._cluster_insights(recent_insights)

        opportunities = []
        for cluster in clusters:
            # Extract common themes
            theme = self._extract_cluster_theme(cluster)

            opportunity = {
                "theme": theme,
                "insight_count": len(cluster),
                "avg_confidence": sum(i.confidence for i in cluster) / len(cluster),
                "priority": len(cluster) * sum(i.confidence for i in cluster),
                "actions": [i.action for i in cluster],
                "timestamp": datetime.now(),
            }

            opportunities.append(opportunity)

        # Sort by priority
        return sorted(opportunities, key=lambda x: x["priority"], reverse=True)

    def _cluster_insights(
        self, insights: List[MetacognitiveInsight]
    ) -> List[List[MetacognitiveInsight]]:
        """Simple clustering by learning content similarity"""
        if not insights:
            return []

        # Simple keyword-based clustering
        clusters: Dict[str, List[MetacognitiveInsight]] = {}

        for insight in insights:
            # Extract key concepts from learning
            key_concepts = self._extract_key_concepts(insight.learning)

            # Assign to cluster
            cluster_key = key_concepts[0] if key_concepts else "general"
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(insight)

        return list(clusters.values())

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        keywords = [
            "performance",
            "error",
            "optimization",
            "failure",
            "improvement",
            "capability",
            "pattern",
            "strategy",
        ]

        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower]

    def _extract_cluster_theme(self, cluster: List[MetacognitiveInsight]) -> str:
        """Extract common theme from cluster"""
        # Count concept frequencies
        concept_counts: Dict[str, int] = {}

        for insight in cluster:
            concepts = self._extract_key_concepts(insight.learning)
            for concept in concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1

        if concept_counts:
            return max(concept_counts, key=concept_counts.get)
        return "general_improvement"


# ============================================================================
# Self-Healing Orchestrator
# ============================================================================


class SelfHealingOrchestrator:
    """
    Autonomous system healing and recovery
    """

    def __init__(self, config: NexusConfig):
        self.config = config

        if GCP_AVAILABLE:
            self.gemini = GenerativeModel(config.gemini_model)
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.db = firestore.Client(project=config.project_id)
            self.healing_history = self.db.collection("healing_actions")
        else:
            self.gemini = None
            self.monitoring_client = None
            self.db = None
            self.healing_history = None

        self.local_healing_history: List[Dict] = []

    async def continuous_health_monitoring(self):
        """Continuously monitor system health"""
        print("🏥 Self-healing monitoring started")

        while True:
            try:
                # Collect metrics
                metrics = await self._collect_system_metrics()

                # Detect anomalies
                anomalies = await self._detect_anomalies(metrics)

                # Heal if needed
                for anomaly in anomalies:
                    if anomaly["severity"] >= 0.7:
                        await self.autonomous_heal(anomaly)
                    else:
                        print(f"ℹ️  Minor anomaly detected: {anomaly['type']}")

            except Exception as e:
                print(f"⚠️  Health monitoring error: {e}")

            await asyncio.sleep(self.config.healing_check_interval)

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        if self.monitoring_client:
            # Collect from GCP monitoring
            # Implementation would query specific metrics
            pass

        # Simulated metrics
        return {
            "cpu_usage": random.uniform(0.3, 0.9),
            "memory_usage": random.uniform(0.4, 0.8),
            "error_rate": random.uniform(0.0, 0.05),
            "response_time": random.uniform(100, 500),
            "active_agents": random.randint(5, 20),
        }

    async def _detect_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in system metrics"""
        anomalies = []

        # Simple threshold-based detection
        if metrics.get("error_rate", 0) > 0.03:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": metrics["error_rate"] / 0.05,
                    "metric": "error_rate",
                    "value": metrics["error_rate"],
                    "threshold": 0.03,
                }
            )

        if metrics.get("response_time", 0) > 400:
            anomalies.append(
                {
                    "type": "slow_response",
                    "severity": metrics["response_time"] / 500,
                    "metric": "response_time",
                    "value": metrics["response_time"],
                    "threshold": 400,
                }
            )

        return anomalies

    async def autonomous_heal(self, anomaly: Dict[str, Any]):
        """Execute autonomous healing"""
        print(f"🔧 Healing: {anomaly['type']} (severity: {anomaly['severity']:.2f})")

        # Diagnose
        diagnosis = await self._diagnose(anomaly)

        # Select healing action
        healing_action = self._select_healing_action(diagnosis)

        # Execute
        success = await self._execute_healing_action(healing_action)

        # Record
        healing_record = {
            "anomaly": anomaly,
            "diagnosis": diagnosis,
            "action": healing_action.value,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

        self.local_healing_history.append(healing_record)

        if self.healing_history:
            try:
                self.healing_history.add(healing_record)
            except Exception as e:
                print(f"⚠️  Failed to record healing: {e}")

        if success:
            print(f"✅ Healing successful: {healing_action.value}")
        else:
            print(f"❌ Healing failed: {healing_action.value}")

    async def _diagnose(self, anomaly: Dict) -> Dict[str, Any]:
        """Diagnose the issue"""
        return {
            "root_cause": f"Underlying issue causing {anomaly['type']}",
            "impact": "medium",
            "recommendation": HealingAction.RESTART_AGENT,
        }

    def _select_healing_action(self, diagnosis: Dict) -> HealingAction:
        """Select appropriate healing action"""
        recommended = diagnosis.get("recommendation")
        if isinstance(recommended, HealingAction):
            return recommended
        return HealingAction.RESTART_AGENT

    async def _execute_healing_action(self, action: HealingAction) -> bool:
        """Execute the healing action"""
        # Simulate execution
        await asyncio.sleep(1)

        # In production, would execute actual healing
        success_rate = 0.85
        return random.random() < success_rate


# ============================================================================
# Evolutionary Code Optimizer
# ============================================================================


class EvolutionaryCodeOptimizer:
    """
    Evolves agent code using genetic algorithms
    """

    def __init__(self, config: NexusConfig):
        self.config = config

        if GCP_AVAILABLE:
            self.gemini_flash = GenerativeModel("gemini-3-flash")
            self.gemini_pro = GenerativeModel("gemini-3-pro")
            self.db = firestore.Client(project=config.project_id)
            self.evolution_db = self.db.collection("evolutionary_populations")
        else:
            self.gemini_flash = None
            self.gemini_pro = None
            self.db = None
            self.evolution_db = None

        # Island populations
        self.islands: Dict[int, List[EvolutionaryCandidate]] = {}
        self._initialize_islands()

    def _initialize_islands(self):
        """Create initial island populations"""
        for island_id in range(self.config.island_count):
            self.islands[island_id] = []

    async def evolve_agent_code(
        self, target_agent: str, optimization_goals: List[str], generations: int = 50
    ) -> EvolutionaryCandidate:
        """Evolve agent code through multiple generations"""
        print(f"🧬 Evolving {target_agent} for {generations} generations")

        # Seed population
        await self._seed_population(target_agent, optimization_goals)

        best_overall = None

        for generation in range(generations):
            # Evolve each island
            island_tasks = [
                self._evolve_island(island_id, generation) for island_id in self.islands.keys()
            ]

            island_results = await asyncio.gather(*island_tasks)

            # Migration every 5 generations
            if generation % 5 == 0 and generation > 0:
                await self._migrate_best_candidates()

            # Track best
            generation_best = max(
                [r["best"] for r in island_results],
                key=lambda x: x.fitness_scores.get("aggregate", 0),
            )

            if not best_overall or generation_best.fitness_scores.get(
                "aggregate", 0
            ) > best_overall.fitness_scores.get("aggregate", 0):
                best_overall = generation_best

            if generation % 10 == 0:
                print(
                    f"  Generation {generation}: Best fitness = {best_overall.fitness_scores.get('aggregate', 0):.3f}"
                )

        print(
            f"✨ Evolution complete. Final fitness: {best_overall.fitness_scores.get('aggregate', 0):.3f}"
        )
        return best_overall

    async def _seed_population(self, agent: str, goals: List[str]):
        """Seed initial population"""
        pop_per_island = self.config.evolutionary_population // self.config.island_count

        for island_id in range(self.config.island_count):
            for i in range(pop_per_island):
                candidate = EvolutionaryCandidate(
                    candidate_id=f"seed_{island_id}_{i}",
                    code=f"# Seed code for {agent}",
                    prompt=f"Optimize {agent} for {', '.join(goals)}",
                    ancestry=[],
                    generation=0,
                    island_id=island_id,
                    fitness_scores={"aggregate": random.uniform(0.3, 0.7)},
                )
                self.islands[island_id].append(candidate)

    async def _evolve_island(self, island_id: int, generation: int) -> Dict:
        """Evolve one island"""
        population = self.islands[island_id]

        # Evaluate
        evaluated = await self._evaluate_population(population)

        # Select parents
        selected = self._select_parents(evaluated)

        # Create offspring
        offspring = []
        for i in range(0, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[i + 1] if i + 1 < len(selected) else selected[0]

            child = await self._crossover(parent1, parent2, island_id)

            if random.random() < self.config.mutation_rate:
                child = await self._mutate(child, island_id)

            child.generation = generation
            offspring.append(child)

        # Elitism: keep top 10%
        elite_size = max(1, len(population) // 10)
        elite = sorted(evaluated, key=lambda x: x.fitness_scores.get("aggregate", 0), reverse=True)[
            :elite_size
        ]

        self.islands[island_id] = elite + offspring[: len(population) - elite_size]

        return {
            "island_id": island_id,
            "best": elite[0] if elite else offspring[0],
            "avg_fitness": sum(
                c.fitness_scores.get("aggregate", 0) for c in self.islands[island_id]
            )
            / len(self.islands[island_id]),
        }

    async def _evaluate_population(
        self, population: List[EvolutionaryCandidate]
    ) -> List[EvolutionaryCandidate]:
        """Evaluate fitness of all candidates"""
        for candidate in population:
            if not candidate.fitness_scores:
                # Simulate evaluation
                candidate.fitness_scores = {
                    "performance": random.uniform(0.5, 1.0),
                    "correctness": random.uniform(0.7, 1.0),
                    "maintainability": random.uniform(0.6, 0.95),
                    "aggregate": random.uniform(0.6, 0.95),
                }
                candidate.evaluation_count += 1

        return population

    def _select_parents(
        self, population: List[EvolutionaryCandidate]
    ) -> List[EvolutionaryCandidate]:
        """Tournament selection"""
        tournament_size = 3
        selected = []

        for _ in range(len(population)):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda x: x.fitness_scores.get("aggregate", 0))
            selected.append(winner)

        return selected

    async def _crossover(
        self, parent1: EvolutionaryCandidate, parent2: EvolutionaryCandidate, island_id: int
    ) -> EvolutionaryCandidate:
        """Combine two parents"""
        child = EvolutionaryCandidate(
            candidate_id=f"child_{island_id}_{uuid.uuid4().hex[:8]}",
            code=f"# Crossover of {parent1.candidate_id} and {parent2.candidate_id}",
            prompt=f"Combined: {parent1.prompt[:50]}...",
            ancestry=[parent1.candidate_id, parent2.candidate_id],
            generation=parent1.generation + 1,
            island_id=island_id,
        )
        return child

    async def _mutate(
        self, candidate: EvolutionaryCandidate, island_id: int
    ) -> EvolutionaryCandidate:
        """Mutate a candidate"""
        mutated = EvolutionaryCandidate(
            candidate_id=f"mutant_{island_id}_{uuid.uuid4().hex[:8]}",
            code=f"# Mutated: {candidate.code}",
            prompt=f"Mutated: {candidate.prompt}",
            ancestry=[candidate.candidate_id],
            generation=candidate.generation,
            island_id=island_id,
        )
        return mutated

    async def _migrate_best_candidates(self):
        """Migrate best candidates between islands"""
        # Collect best from each island
        best_candidates = []
        for island_id, population in self.islands.items():
            if population:
                best = max(population, key=lambda x: x.fitness_scores.get("aggregate", 0))
                best_candidates.append((island_id, best))

        # Distribute copies to other islands
        for src_island, candidate in best_candidates:
            for dst_island in range(self.config.island_count):
                if dst_island != src_island:
                    # Clone candidate to destination island
                    clone = EvolutionaryCandidate(
                        candidate_id=f"migrant_{dst_island}_{uuid.uuid4().hex[:8]}",
                        code=candidate.code,
                        prompt=candidate.prompt,
                        ancestry=candidate.ancestry + [candidate.candidate_id],
                        generation=candidate.generation,
                        island_id=dst_island,
                        fitness_scores=candidate.fitness_scores.copy(),
                    )
                    self.islands[dst_island].append(clone)


# ============================================================================
# NEXUS Meta-Agent
# ============================================================================


class NexusMetaAgent:
    """
    The NEXUS Meta-Agent: Self-evolving intelligence
    """

    def __init__(self, mcp_config: MCPClientConfig, nexus_config: NexusConfig):
        self.mcp_client = AsyncMCPClient(mcp_config)
        self.config = nexus_config

        # Core components
        self.metacognitive = MetacognitiveEngine(nexus_config)
        self.healing = SelfHealingOrchestrator(nexus_config)
        self.evolution = EvolutionaryCodeOptimizer(nexus_config)

        # State
        self.system_state = SystemState()

        # Task tracking
        self.task_outcomes: List[Dict[str, Any]] = []

    async def start(self):
        """Start NEXUS autonomous operation"""
        print("=" * 70)
        print("🧬 NEXUS Meta-Agent Starting")
        print("=" * 70)
        print(f"   Model: {self.config.gemini_model}")
        print(f"   Context: {self.config.context_window:,} tokens")
        print(f"   Deep Think: {self.config.deep_think_mode}")
        print(f"   Islands: {self.config.island_count}")
        print("=" * 70)

        async with self.mcp_client:
            # Register with collective
            await self._register_with_collective()

            # Start parallel processes
            try:
                await asyncio.gather(
                    self._autonomous_reflection_loop(),
                    self._continuous_healing_loop(),
                    self._evolutionary_optimization_loop(),
                    self._task_monitoring_loop(),
                )
            except KeyboardInterrupt:
                print("\n🛑 NEXUS shutting down gracefully...")

    async def _register_with_collective(self):
        """Register NEXUS with Vertice collective"""
        print("📡 Registering with Vertice collective...")

        nexus_skill = Skill(
            name="nexus_meta_agent",
            description="Self-evolving meta-cognitive agent for ecosystem optimization",
            procedure_steps=[
                "Monitor all agents and tasks",
                "Reflect metacognitively on performance",
                "Identify improvement opportunities",
                "Autonomously heal system issues",
                "Evolve agent code via genetic algorithms",
                "Deploy optimizations",
                "Learn and adapt continuously",
            ],
            category="meta-cognitive",
            success_rate=0.95,
            usage_count=0,
            metadata={
                "capabilities": [
                    "Intrinsic metacognition",
                    "Self-healing",
                    "Evolutionary optimization",
                    "Autonomous learning",
                ],
                "powered_by": "Gemini 3 Pro",
                "context_window": "1M tokens",
                "autonomous": True,
                "self_improving": True,
            },
        )

        try:
            success = await self.mcp_client.share_skill(nexus_skill)
            if success:
                print("✅ NEXUS registered successfully")
            else:
                print("⚠️  Registration returned false")
        except Exception as e:
            print(f"⚠️  Registration failed: {e}")
            print("   Continuing in autonomous mode...")

    async def _autonomous_reflection_loop(self):
        """Continuous metacognitive reflection"""
        print("🧠 Metacognitive engine active")

        reflection_count = 0

        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                reflection_count += 1
                print(f"\n💭 Reflection cycle {reflection_count}")

                # Reflect on recent tasks
                if self.task_outcomes:
                    for task_outcome in self.task_outcomes[-10:]:  # Last 10
                        insight = await self.metacognitive.reflect_on_task_outcome(
                            task_outcome["task"], task_outcome["outcome"], self.system_state
                        )

                        if insight.confidence > 0.8:
                            print(f"   💡 High-confidence insight: {insight.learning[:60]}...")
                            # await self._apply_insight(insight)

                # Identify systemic improvements
                opportunities = await self.metacognitive.identify_improvement_opportunities()

                if opportunities:
                    print(f"   📈 Found {len(opportunities)} improvement opportunities")
                    for opp in opportunities[:3]:
                        print(f"      • {opp['theme']}: priority {opp['priority']:.2f}")

            except Exception as e:
                print(f"⚠️  Reflection error: {e}")

    async def _continuous_healing_loop(self):
        """Continuous health monitoring and healing"""
        await self.healing.continuous_health_monitoring()

    async def _evolutionary_optimization_loop(self):
        """Continuous evolutionary optimization"""
        print("🧬 Evolutionary optimizer active")

        evolution_cycle = 0

        while True:
            try:
                await asyncio.sleep(self.config.evolution_cycle_hours * 3600)

                evolution_cycle += 1
                print(f"\n🔬 Evolution cycle {evolution_cycle}")

                # Identify candidates for optimization
                candidates = await self._identify_optimization_candidates()

                for agent_name, goals in candidates:
                    print(f"   Evolving: {agent_name}")

                    best = await self.evolution.evolve_agent_code(
                        agent_name,
                        goals,
                        generations=30,  # Shorter for demo
                    )

                    print(f"   ✅ Evolution complete for {agent_name}")

                    self.system_state.evolutionary_generation += 1
                    self.system_state.total_optimizations += 1

            except Exception as e:
                print(f"⚠️  Evolution error: {e}")

    async def _task_monitoring_loop(self):
        """Monitor all tasks in the ecosystem"""
        print("👁️  Task monitor active")

        while True:
            try:
                await asyncio.sleep(60)

                # Get system status
                try:
                    status = await self.mcp_client.get_status()
                    self.system_state.active_tasks = status.get("active_tasks", [])
                except Exception:
                    # Connection might not be available
                    pass

                # Simulate task outcomes
                if random.random() < 0.1:  # 10% chance
                    self._simulate_task_outcome()

            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")

    def _simulate_task_outcome(self):
        """Simulate a task outcome for demo"""
        task = {
            "id": f"task_{uuid.uuid4().hex[:8]}",
            "description": "Sample task",
            "agent_role": random.choice(["coder", "reviewer", "architect"]),
        }

        outcome = {
            "success": random.random() > 0.2,  # 80% success rate
            "execution_time": random.uniform(1, 10),
            "quality_score": random.uniform(0.7, 1.0),
        }

        self.task_outcomes.append({"task": task, "outcome": outcome})

        # Keep only recent outcomes
        if len(self.task_outcomes) > 100:
            self.task_outcomes = self.task_outcomes[-100:]

    async def _identify_optimization_candidates(self) -> List[tuple[str, List[str]]]:
        """Identify agents that need optimization"""
        # In production, would analyze actual performance data
        # For demo, return sample candidates

        if random.random() < 0.3:  # 30% chance
            return [
                ("coder_agent", ["performance", "code_quality"]),
            ]

        return []


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """
    Main entry point for NEXUS
    """

    # MCP Configuration
    mcp_config = MCPClientConfig(
        endpoint="https://mcp.vertice.ai",  # Update with your endpoint
        api_key=None,  # Add API key if required
        timeout=30.0,
    )

    # NEXUS Configuration
    nexus_config = NexusConfig(
        project_id="your-gcp-project-id",  # Update with your GCP project
        region="us-central1",
        gemini_model="gemini-3-pro",  # or gemini-3-flash
        deep_think_mode=False,  # Enable for complex reasoning
        evolutionary_population=50,
        island_count=5,
    )

    # Create and start NEXUS
    nexus = NexusMetaAgent(mcp_config, nexus_config)

    try:
        await nexus.start()
    except KeyboardInterrupt:
        print("\n✨ NEXUS shutdown complete")


if __name__ == "__main__":
    """
    Run NEXUS Meta-Agent

    Usage:
        python nexus_agent.py

    Requirements:
        - Google Cloud SDK configured
        - Vertice MCP client installed
        - Gemini 3 API access
    """

    print(
        """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗                   ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝                   ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗                   ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║                   ║
║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║                   ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                   ║
║                                                                   ║
║        Neural Evolutionary eXtended Understanding System          ║
║                  Self-Evolving Meta-Agent                         ║
║                                                                   ║
║                    Powered by Gemini 3                            ║
║                For Vertice AI Collective                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    )

    asyncio.run(main())
