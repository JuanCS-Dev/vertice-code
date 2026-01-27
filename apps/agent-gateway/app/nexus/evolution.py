"""
NEXUS Evolutionary Code Optimizer

Implements Island-Based Evolutionary Framework using Gemini 3 Pro
for LLM-guided code evolution and optimization.

Inspired by:
- DeepMind AlphaEvolve
- CodeEvolve research (2024-2025)

Evolution Mechanisms:
- LLM-guided mutation
- Inspiration-based crossover
- Multi-objective fitness evaluation
- Island migration for diversity
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple

from nexus.config import NexusConfig
from nexus.types import EvolutionaryCandidate

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


CROSSOVER_PROMPT_TEMPLATE = """You are creating a new solution by combining insights from two parent solutions.

PARENT 1:
Prompt: {parent1_prompt}
Code:
```
{parent1_code}
```
Fitness: {parent1_fitness}

PARENT 2:
Prompt: {parent2_prompt}
Code:
```
{parent2_code}
```
Fitness: {parent2_fitness}

OPTIMIZATION GOALS: {goals}

Create a child solution that combines the best aspects of both parents.
Consider:
- What works well in each parent?
- How can their strengths be combined?
- What new insights emerge from their combination?

Generate the improved solution code only, no explanations:
```python
"""

MUTATION_PROMPT_TEMPLATE = """Mutate this solution to explore new possibilities.

CURRENT SOLUTION:
```
{code}
```
Performance: {fitness}

OPTIMIZATION GOALS: {goals}

Make a targeted modification that:
1. Preserves core functionality
2. Explores a new approach or optimization
3. Potentially improves performance

Mutation types to consider:
- Algorithm change
- Data structure optimization
- Control flow modification
- New technique integration

Generate the mutated code only:
```python
"""


class EvolutionaryCodeOptimizer:
    """
    Evolutionary Code Optimizer using Gemini 3 Pro.

    Implements island-based genetic algorithm with LLM-guided
    mutation and crossover operations.
    """

    def __init__(self, config: NexusConfig):
        self.config = config
        self.islands: Dict[int, List[EvolutionaryCandidate]] = {}
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None

        # Initialize islands
        for i in range(config.island_count):
            self.islands[i] = []

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
                self._evolution_collection = self._db.collection(
                    config.firestore_evolution_collection
                )
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}")

    async def evolve(
        self,
        target: str,
        goals: List[str],
        seed_code: Optional[str] = None,
        generations: Optional[int] = None,
    ) -> EvolutionaryCandidate:
        """
        Evolve code through multiple generations.

        Args:
            target: Name/description of what to optimize
            goals: List of optimization goals
            seed_code: Optional initial code to evolve from
            generations: Number of generations (default from config)

        Returns:
            Best evolved candidate
        """
        generations = generations or self.config.max_generations
        logger.info(f"🧬 Starting evolution: {target} for {generations} generations")

        # Seed population
        await self._seed_population(target, goals, seed_code)

        best_overall: Optional[EvolutionaryCandidate] = None

        for gen in range(generations):
            # Evolve each island in parallel
            tasks = [
                self._evolve_island(island_id, gen, goals) for island_id in self.islands.keys()
            ]
            results = await asyncio.gather(*tasks)

            # Find best of this generation
            gen_best = max(
                [r["best"] for r in results],
                key=lambda c: c.aggregate_fitness,
            )

            if not best_overall or gen_best.aggregate_fitness > best_overall.aggregate_fitness:
                best_overall = gen_best

            # Migration every N generations
            if gen > 0 and gen % self.config.migration_interval == 0:
                await self._migrate()

            if gen % 10 == 0:
                logger.info(f"  Gen {gen}: Best fitness = {best_overall.aggregate_fitness:.3f}")

        logger.info(f"✨ Evolution complete. Final fitness: {best_overall.aggregate_fitness:.3f}")

        # Persist best candidate
        if self._db and best_overall:
            try:
                await self._evolution_collection.document(best_overall.candidate_id).set(
                    best_overall.to_dict()
                )
            except Exception as e:
                logger.warning(f"Failed to persist candidate: {e}")

        return best_overall

    async def _seed_population(
        self,
        target: str,
        goals: List[str],
        seed_code: Optional[str],
    ) -> None:
        """Seed initial population across islands."""
        pop_per_island = self.config.evolutionary_population // self.config.island_count

        for island_id in range(self.config.island_count):
            self.islands[island_id] = []

            for i in range(pop_per_island):
                code = seed_code or f"# Seed code for {target}\npass"
                candidate = EvolutionaryCandidate(
                    candidate_id=f"seed_{island_id}_{i}_{uuid.uuid4().hex[:6]}",
                    code=code,
                    prompt=f"Optimize {target} for: {', '.join(goals)}",
                    island_id=island_id,
                    generation=0,
                    fitness_scores={"aggregate": random.uniform(0.3, 0.6)},
                )
                self.islands[island_id].append(candidate)

    async def _evolve_island(
        self,
        island_id: int,
        generation: int,
        goals: List[str],
    ) -> Dict[str, Any]:
        """Evolve one island for one generation."""
        population = self.islands[island_id]

        # Evaluate fitness
        evaluated = await self._evaluate_population(population)

        # Select parents
        selected = self._select_parents(evaluated)

        # Create offspring
        offspring = []
        for i in range(0, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[i + 1] if i + 1 < len(selected) else selected[0]

            # Crossover
            if random.random() < self.config.crossover_rate:
                child = await self._crossover(parent1, parent2, island_id, goals)
            else:
                child = EvolutionaryCandidate(
                    candidate_id=f"clone_{island_id}_{uuid.uuid4().hex[:6]}",
                    code=parent1.code,
                    prompt=parent1.prompt,
                    ancestry=[parent1.candidate_id],
                    island_id=island_id,
                    generation=generation,
                )

            # Mutation
            if random.random() < self.config.mutation_rate:
                child = await self._mutate(child, island_id, goals)

            child.generation = generation
            offspring.append(child)

        # Elitism: keep top performers
        elite_count = max(1, int(len(population) * self.config.elite_ratio))
        elite = sorted(
            evaluated,
            key=lambda c: c.aggregate_fitness,
            reverse=True,
        )[:elite_count]

        # New population
        self.islands[island_id] = elite + offspring[: len(population) - elite_count]

        return {
            "island_id": island_id,
            "best": elite[0] if elite else offspring[0],
            "avg_fitness": sum(c.aggregate_fitness for c in self.islands[island_id])
            / len(self.islands[island_id]),
        }

    async def _evaluate_population(
        self,
        population: List[EvolutionaryCandidate],
    ) -> List[EvolutionaryCandidate]:
        """Evaluate fitness of population."""
        for candidate in population:
            if not candidate.fitness_scores:
                # Simulate multi-objective evaluation
                # In production, actually run and measure the code
                candidate.fitness_scores = {
                    "correctness": random.uniform(0.7, 1.0),
                    "performance": random.uniform(0.5, 1.0),
                    "maintainability": random.uniform(0.6, 0.95),
                    "efficiency": random.uniform(0.5, 0.95),
                }

                # Weighted aggregate
                weights = {
                    "correctness": 0.35,
                    "performance": 0.25,
                    "maintainability": 0.20,
                    "efficiency": 0.20,
                }
                aggregate = sum(candidate.fitness_scores[k] * weights[k] for k in weights)
                candidate.fitness_scores["aggregate"] = aggregate
                candidate.evaluation_count += 1

        return population

    def _select_parents(
        self,
        population: List[EvolutionaryCandidate],
    ) -> List[EvolutionaryCandidate]:
        """Tournament selection."""
        tournament_size = 3
        selected = []

        for _ in range(len(population)):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = max(tournament, key=lambda c: c.aggregate_fitness)
            selected.append(winner)

        return selected

    async def _crossover(
        self,
        parent1: EvolutionaryCandidate,
        parent2: EvolutionaryCandidate,
        island_id: int,
        goals: List[str],
    ) -> EvolutionaryCandidate:
        """LLM-guided crossover using Gemini 3 Pro."""
        if self._client:
            try:
                prompt = CROSSOVER_PROMPT_TEMPLATE.format(
                    parent1_prompt=parent1.prompt,
                    parent1_code=parent1.code[:2000],
                    parent1_fitness=parent1.fitness_scores,
                    parent2_prompt=parent2.prompt,
                    parent2_code=parent2.code[:2000],
                    parent2_fitness=parent2.fitness_scores,
                    goals=", ".join(goals),
                )

                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=self.config.flash_model,  # Use Flash for speed
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.config.temperature,
                        max_output_tokens=4096,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=types.ThinkingLevel.LOW,
                        ),
                    ),
                )

                child_code = self._extract_code(response.text)

                return EvolutionaryCandidate(
                    candidate_id=f"cross_{island_id}_{uuid.uuid4().hex[:6]}",
                    code=child_code,
                    prompt=f"Crossover of {parent1.candidate_id} and {parent2.candidate_id}",
                    ancestry=[parent1.candidate_id, parent2.candidate_id],
                    island_id=island_id,
                    generation=parent1.generation + 1,
                )

            except Exception as e:
                logger.warning(f"Gemini crossover failed: {e}")

        # Fallback: simple code merge
        return EvolutionaryCandidate(
            candidate_id=f"cross_{island_id}_{uuid.uuid4().hex[:6]}",
            code=f"# Crossover\n{parent1.code[:500]}\n# ---\n{parent2.code[:500]}",
            prompt=f"Crossover of {parent1.candidate_id} and {parent2.candidate_id}",
            ancestry=[parent1.candidate_id, parent2.candidate_id],
            island_id=island_id,
            generation=parent1.generation + 1,
        )

    async def _mutate(
        self,
        candidate: EvolutionaryCandidate,
        island_id: int,
        goals: List[str],
    ) -> EvolutionaryCandidate:
        """LLM-guided mutation using Gemini 3 Pro."""
        if self._client:
            try:
                prompt = MUTATION_PROMPT_TEMPLATE.format(
                    code=candidate.code[:3000],
                    fitness=candidate.fitness_scores,
                    goals=", ".join(goals),
                )

                response = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=self.config.flash_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=1.2,  # Slightly higher for diversity
                        max_output_tokens=4096,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=types.ThinkingLevel.LOW,
                        ),
                    ),
                )

                mutated_code = self._extract_code(response.text)

                return EvolutionaryCandidate(
                    candidate_id=f"mut_{island_id}_{uuid.uuid4().hex[:6]}",
                    code=mutated_code,
                    prompt=f"Mutation of {candidate.candidate_id}",
                    ancestry=[candidate.candidate_id],
                    island_id=island_id,
                    generation=candidate.generation,
                )

            except Exception as e:
                logger.warning(f"Gemini mutation failed: {e}")

        # Fallback: return unchanged
        return candidate

    def _extract_code(self, response: str) -> str:
        """Extract code from Gemini response."""
        # Look for code block
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code_part = parts[1].split("```")[0]
                return code_part.strip()

        if "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                return parts[1].strip()

        return response.strip()

    async def _migrate(self) -> None:
        """Migrate best candidates between islands."""
        best_per_island: List[Tuple[int, EvolutionaryCandidate]] = []

        for island_id, population in self.islands.items():
            if population:
                best = max(population, key=lambda c: c.aggregate_fitness)
                best_per_island.append((island_id, best))

        # Distribute copies to neighboring islands
        for src_island, candidate in best_per_island:
            for dst_island in range(self.config.island_count):
                if dst_island != src_island:
                    clone = EvolutionaryCandidate(
                        candidate_id=f"migrant_{dst_island}_{uuid.uuid4().hex[:6]}",
                        code=candidate.code,
                        prompt=candidate.prompt,
                        ancestry=candidate.ancestry + [candidate.candidate_id],
                        island_id=dst_island,
                        generation=candidate.generation,
                        fitness_scores=candidate.fitness_scores.copy(),
                    )
                    self.islands[dst_island].append(clone)

        logger.debug(f"Migration complete: {len(best_per_island)} candidates shared")

    def get_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        total_candidates = sum(len(pop) for pop in self.islands.values())

        all_candidates = [c for pop in self.islands.values() for c in pop]
        if all_candidates:
            best = max(all_candidates, key=lambda c: c.aggregate_fitness)
            avg_fitness = sum(c.aggregate_fitness for c in all_candidates) / len(all_candidates)
        else:
            best = None
            avg_fitness = 0.0

        return {
            "total_candidates": total_candidates,
            "island_count": self.config.island_count,
            "avg_fitness": round(avg_fitness, 3),
            "best_fitness": round(best.aggregate_fitness, 3) if best else 0.0,
            "best_candidate_id": best.candidate_id if best else None,
            "gemini_available": self._client is not None,
            "model": self.config.flash_model,
        }
