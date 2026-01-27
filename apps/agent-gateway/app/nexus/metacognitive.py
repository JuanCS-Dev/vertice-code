"""
NEXUS Metacognitive Engine

Implements intrinsic metacognitive learning using Gemini 3 Pro with
thinking_level=HIGH for deep causal reasoning and self-reflection.

Core capabilities:
- Task outcome reflection
- Pattern identification
- Improvement opportunity detection
- Self-modification recommendations
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import (
    InsightCategory,
    MetacognitiveInsight,
    SystemState,
)

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not available, metacognitive engine in simulation mode")

try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


METACOGNITIVE_SYSTEM_PROMPT = """You are the Metacognitive Engine of NEXUS, a self-aware meta-agent powered by Gemini 3 Pro.

Your role is to think about thinking—to monitor the system's cognitive processes, identify patterns in how problems are solved, and discover opportunities for fundamental improvement.

You operate at a higher level of abstraction than task execution. Your focus is:
1. WHY solutions work or fail (causal reasoning)
2. HOW the system approaches different problem types (strategy analysis)
3. WHAT patterns emerge across multiple tasks (meta-learning)
4. WHERE the system could fundamentally improve (architectural evolution)

You have access to:
- Complete history of tasks, solutions, and outcomes
- Performance metrics across all agents
- Code evolution history
- System architecture and agent interactions

Your outputs are metacognitive insights that drive:
- Self-modification of agent behaviors
- Evolution of problem-solving strategies
- Architectural improvements to the ecosystem
- New skill discovery and learning

Think deeply. Reason causally. Abstract patterns. Drive evolution.

ALWAYS structure your response as:
OBSERVATION: [What happened - factual description]
CAUSAL_ANALYSIS: [Why it happened - root cause analysis]
LEARNING: [What should be learned from this]
ACTION: [Specific actionable improvement]
CONFIDENCE: [0.0-1.0 - your confidence in this analysis]
CATEGORY: [performance|error_pattern|optimization|capability_gap|architectural|behavioral]
"""


class MetacognitiveEngine:
    """
    Metacognitive Engine using Gemini 3 Pro with thinking_level=HIGH.

    Implements intrinsic metacognitive learning for autonomous self-improvement.
    """

    def __init__(self, config: NexusConfig):
        self.config = config
        self._local_insights: List[MetacognitiveInsight] = []
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None

        if GENAI_AVAILABLE:
            try:
                os.environ.setdefault("GOOGLE_CLOUD_PROJECT", config.project_id)
                os.environ.setdefault("GOOGLE_CLOUD_LOCATION", config.location)
                os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
                self._client = genai.Client()
                logger.info(f"Initialized Gemini 3 Pro client: {config.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=config.project_id)
                self._insights_collection = self._db.collection(
                    config.firestore_insights_collection
                )
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}")
                self._db = None

    async def reflect_on_task_outcome(
        self,
        task: Dict[str, Any],
        outcome: Dict[str, Any],
        system_state: SystemState,
    ) -> MetacognitiveInsight:
        """
        Perform deep metacognitive reflection on a completed task.

        Uses Gemini 3 Pro with thinking_level=HIGH for causal analysis.
        """
        reflection_prompt = self._build_reflection_prompt(task, outcome, system_state)

        if self._client:
            try:
                response = await self._generate_with_thinking(reflection_prompt)
                insight = self._parse_reflection_response(response)
            except Exception as e:
                logger.warning(f"Gemini 3 reflection failed: {e}")
                insight = self._simulate_reflection(task, outcome)
        else:
            insight = self._simulate_reflection(task, outcome)

        await self._store_insight(insight)
        return insight

    async def _generate_with_thinking(self, prompt: str) -> str:
        """Generate response using Gemini 3 Pro with thinking_level=HIGH."""
        if not self._client:
            raise RuntimeError("Gemini client not initialized")

        thinking_level = (
            types.ThinkingLevel.HIGH
            if self.config.default_thinking_level == "HIGH"
            else types.ThinkingLevel.LOW
        )

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=METACOGNITIVE_SYSTEM_PROMPT,
                temperature=self.config.temperature,
                max_output_tokens=8192,
                thinking_config=types.ThinkingConfig(
                    thinking_level=thinking_level,
                ),
            ),
        )

        return response.text

    def _build_reflection_prompt(
        self,
        task: Dict[str, Any],
        outcome: Dict[str, Any],
        state: SystemState,
    ) -> str:
        return f"""Analyze this task outcome with deep metacognitive reasoning:

TASK:
{task}

OUTCOME:
{outcome}

CURRENT SYSTEM STATE:
- Agent Health: {state.agent_health}
- Recent Failures: {len(state.recent_failures)} in queue
- Skills Tracked: {len(state.skill_performance)}
- Evolutionary Generation: {state.evolutionary_generation}
- Total Insights Generated: {state.total_insights}
- Total Healings Performed: {state.total_healings}

REFLECTION QUESTIONS:
1. What patterns do you observe in how this task was approached?
2. Why did this outcome occur? (deep causal analysis required)
3. What does this reveal about the system's current capabilities and limitations?
4. How could the approach be fundamentally improved?
5. What new strategies or skills should the system learn?
6. Should any agents or workflows be evolved?

Provide your structured metacognitive insight."""

    def _parse_reflection_response(self, response: str) -> MetacognitiveInsight:
        """Parse Gemini 3 response into structured insight."""
        lines = response.strip().split("\n")
        parsed: Dict[str, str] = {}

        current_key = None
        current_value = []

        for line in lines:
            if ":" in line:
                key_part = line.split(":", 1)[0].strip().upper().replace(" ", "_")
                if key_part in {
                    "OBSERVATION",
                    "CAUSAL_ANALYSIS",
                    "LEARNING",
                    "ACTION",
                    "CONFIDENCE",
                    "CATEGORY",
                }:
                    if current_key:
                        parsed[current_key] = " ".join(current_value).strip()
                    current_key = key_part.lower()
                    current_value = [line.split(":", 1)[1].strip()]
                    continue

            if current_key:
                current_value.append(line.strip())

        if current_key:
            parsed[current_key] = " ".join(current_value).strip()

        # Parse confidence
        confidence = 0.5
        try:
            conf_str = parsed.get("confidence", "0.5")
            confidence = float(conf_str.replace(",", ".").strip())
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            pass

        # Parse category
        category = InsightCategory.PERFORMANCE
        cat_str = parsed.get("category", "").lower()
        for cat in InsightCategory:
            if cat.value in cat_str:
                category = cat
                break

        return MetacognitiveInsight(
            context="task_outcome_reflection",
            observation=parsed.get("observation", "No observation extracted"),
            causal_analysis=parsed.get("causal_analysis", "No analysis extracted"),
            learning=parsed.get("learning", "No learning extracted"),
            action=parsed.get("action", "No action extracted"),
            confidence=confidence,
            category=category,
        )

    def _simulate_reflection(
        self,
        task: Dict[str, Any],
        outcome: Dict[str, Any],
    ) -> MetacognitiveInsight:
        """Simulate reflection when Gemini 3 is unavailable."""
        success = outcome.get("success", False)

        if success:
            return MetacognitiveInsight(
                context="simulated_reflection",
                observation=f"Task {task.get('id', 'unknown')} completed successfully",
                causal_analysis="Task execution followed expected patterns",
                learning="Current approach is effective for this task type",
                action="Continue monitoring for optimization opportunities",
                confidence=0.7,
                category=InsightCategory.PERFORMANCE,
            )
        else:
            return MetacognitiveInsight(
                context="simulated_reflection",
                observation=f"Task {task.get('id', 'unknown')} failed",
                causal_analysis="Failure indicates capability gap or system issue",
                learning="System needs improvement in this area",
                action="Queue for evolutionary optimization",
                confidence=0.6,
                category=InsightCategory.CAPABILITY_GAP,
            )

    async def _store_insight(self, insight: MetacognitiveInsight) -> None:
        """Store insight in local cache and Firestore."""
        self._local_insights.append(insight)

        # Keep local cache bounded
        if len(self._local_insights) > self.config.max_local_insights:
            self._local_insights = self._local_insights[-self.config.max_local_insights :]

        if self._db:
            try:
                await self._insights_collection.document(insight.insight_id).set(insight.to_dict())
            except Exception as e:
                logger.warning(f"Failed to store insight: {e}")

    async def identify_improvement_opportunities(
        self,
        time_window_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Analyze recent insights to find systemic improvement opportunities."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

        recent = [
            i
            for i in self._local_insights
            if i.timestamp > cutoff and i.confidence >= self.config.insight_confidence_threshold
        ]

        if not recent:
            return []

        # Cluster by category
        clusters: Dict[InsightCategory, List[MetacognitiveInsight]] = {}
        for insight in recent:
            if insight.category not in clusters:
                clusters[insight.category] = []
            clusters[insight.category].append(insight)

        opportunities = []
        for category, insights in clusters.items():
            if len(insights) >= 2:  # Pattern requires multiple insights
                avg_confidence = sum(i.confidence for i in insights) / len(insights)
                priority = len(insights) * avg_confidence

                opportunities.append(
                    {
                        "category": category.value,
                        "insight_count": len(insights),
                        "avg_confidence": round(avg_confidence, 3),
                        "priority": round(priority, 3),
                        "actions": [i.action for i in insights[:5]],
                        "learnings": [i.learning for i in insights[:5]],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

        return sorted(opportunities, key=lambda x: x["priority"], reverse=True)

    async def get_recent_insights(
        self,
        limit: int = 20,
        min_confidence: float = 0.0,
    ) -> List[MetacognitiveInsight]:
        """Get recent insights, optionally filtered by confidence."""
        filtered = [i for i in self._local_insights if i.confidence >= min_confidence]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get metacognitive engine statistics."""
        by_category = {}
        for cat in InsightCategory:
            count = sum(1 for i in self._local_insights if i.category == cat)
            by_category[cat.value] = count

        return {
            "total_insights": len(self._local_insights),
            "by_category": by_category,
            "avg_confidence": (
                sum(i.confidence for i in self._local_insights) / len(self._local_insights)
                if self._local_insights
                else 0.0
            ),
            "gemini_available": self._client is not None,
            "model": self.config.model,
            "thinking_level": self.config.default_thinking_level,
        }
