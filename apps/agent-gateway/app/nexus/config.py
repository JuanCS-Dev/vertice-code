"""
NEXUS Configuration - Gemini 3 Pro Native

All configuration for the NEXUS Meta-Agent system.
Uses gemini-3-pro-preview exclusively as per M12 requirements.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class NexusConfig:
    """Configuration for NEXUS Meta-Agent (Gemini 3 Pro native)."""

    # GCP Project Configuration
    project_id: str = field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai"))
    location: str = field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_LOCATION", "global"))

    # Gemini 3 Pro Model Configuration
    model: str = "gemini-3-pro-preview"
    flash_model: str = "gemini-3-flash-preview"

    # Thinking Level (Gemini 3 specific)
    # LOW: Fast responses, minimal reasoning
    # HIGH: Deep reasoning, complex tasks (default for metacognition)
    default_thinking_level: Literal["LOW", "HIGH"] = "HIGH"

    # Context Window (1M tokens for Gemini 3 Pro)
    context_window: int = 1_048_576
    max_output_tokens: int = 65_536

    # Temperature (Gemini 3 recommends 1.0)
    temperature: float = 1.0

    # Evolutionary Algorithm Settings
    evolutionary_population: int = 50
    island_count: int = 5
    mutation_rate: float = 0.15
    crossover_rate: float = 0.8
    elite_ratio: float = 0.1
    migration_interval: int = 5
    max_generations: int = 50

    # Metacognitive Settings
    reflection_interval_seconds: int = 3600  # 1 hour
    insight_confidence_threshold: float = 0.8
    max_local_insights: int = 1000

    # Self-Healing Settings
    health_check_interval_seconds: int = 60
    anomaly_severity_threshold: float = 0.7
    error_rate_threshold: float = 0.03
    response_time_threshold_ms: float = 400.0

    # Memory Hierarchy (L1-L4)
    l1_working_memory_tokens: int = 131_072  # 128K
    l2_episodic_memory_tokens: int = 524_288  # 512K
    l3_semantic_memory_tokens: int = 262_144  # 256K
    l4_procedural_memory_tokens: int = 131_072  # 128K

    # Firestore Collections
    firestore_insights_collection: str = "nexus_metacognitive_insights"
    firestore_memory_collection: str = "nexus_hierarchical_memory"
    firestore_evolution_collection: str = "nexus_evolutionary_populations"
    firestore_healing_collection: str = "nexus_healing_actions"
    firestore_state_collection: str = "nexus_system_states"

    @classmethod
    def from_env(cls) -> "NexusConfig":
        """Create configuration from environment variables."""
        return cls(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
            model=os.getenv("NEXUS_GEMINI_MODEL", "gemini-3-pro-preview"),
            flash_model=os.getenv("NEXUS_GEMINI_FLASH_MODEL", "gemini-3-flash-preview"),
            default_thinking_level=os.getenv("NEXUS_THINKING_LEVEL", "HIGH"),  # type: ignore
            evolutionary_population=int(os.getenv("NEXUS_EVOLUTION_POPULATION", "50")),
            island_count=int(os.getenv("NEXUS_ISLAND_COUNT", "5")),
            mutation_rate=float(os.getenv("NEXUS_MUTATION_RATE", "0.15")),
            reflection_interval_seconds=int(os.getenv("NEXUS_REFLECTION_INTERVAL", "3600")),
            health_check_interval_seconds=int(os.getenv("NEXUS_HEALTH_CHECK_INTERVAL", "60")),
        )
