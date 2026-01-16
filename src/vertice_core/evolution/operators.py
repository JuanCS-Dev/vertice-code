"""
Specific Mutation Operators

Concrete implementations of GVU Generate phase operators.

References:
- arXiv:2310.11958 (STaR: Self-Taught Reasoner)
- arXiv:2303.11366 (Reflexion)
- arXiv:2401.01335 (SPIN: Self-Play Fine-Tuning)
- arXiv:2505.22954 (Darwin Gödel Machine)
- arXiv:2512.02731 (GVU Operator Framework)
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional

from .types import AgentVariant, MutationType, MutationProposal, GVUPhase


class BaseMutator(ABC):
    """
    Abstract base class for GVU Generate phase operators.

    Each mutator implements the Generate phase of the GVU framework,
    proposing modifications that will be verified empirically.
    """

    mutation_type: MutationType = MutationType.PROMPT
    gvu_phase: GVUPhase = GVUPhase.GENERATE

    @abstractmethod
    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """
        Generate a mutation proposal.

        Returns:
            MutationProposal if mutation is possible, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """
        Apply a mutation proposal to create a new variant.

        Returns:
            New variant with mutation applied
        """
        raise NotImplementedError


class PromptMutator(BaseMutator):
    """Mutator for system prompts using STaR/Reflexion patterns."""

    mutation_type = MutationType.PROMPT

    REASONING_PATTERNS = [
        "Think step by step before answering.",
        "Consider edge cases carefully.",
        "Verify your answer before responding.",
        "Break down complex problems into smaller parts.",
    ]

    REFLECTION_PATTERNS = [
        "After generating a solution, reflect on potential issues.",
        "Learn from previous mistakes in similar tasks.",
        "Consider alternative approaches before committing.",
        "Evaluate the robustness of your solution.",
    ]

    SELFPLAY_PATTERNS = [
        "Generate multiple candidate solutions and select the best.",
        "Act as your own critic and identify weaknesses.",
        "Compare your approach with alternative strategies.",
        "Iterate and refine based on self-evaluation.",
    ]

    METACOGNITIVE_PATTERNS = [
        "Assess your confidence before responding.",
        "Identify what you don't know about this problem.",
        "Consider when to ask for clarification.",
        "Monitor your reasoning process for errors.",
    ]

    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """Propose a prompt enhancement using STaR/Reflexion/SPIN patterns."""
        if not variant.prompts:
            return MutationProposal(
                mutation_type=self.mutation_type,
                target_key="system",
                original_value="",
                proposed_value="You are a helpful coding assistant.",
                reasoning="Initialize system prompt",
                confidence=1.0,
                gvu_phase=GVUPhase.GENERATE,
            )

        target_key = random.choice(list(variant.prompts.keys()))
        original = variant.prompts[target_key]

        all_patterns = []
        if not any(p.lower() in original.lower() for p in ["step by step", "break down"]):
            all_patterns.extend(self.REASONING_PATTERNS)
        if not any(p.lower() in original.lower() for p in ["reflect", "learn from"]):
            all_patterns.extend(self.REFLECTION_PATTERNS)
        if not any(p.lower() in original.lower() for p in ["generate multiple", "act as"]):
            all_patterns.extend(self.SELFPLAY_PATTERNS)
        if not any(p.lower() in original.lower() for p in ["confidence", "don't know"]):
            all_patterns.extend(self.METACOGNITIVE_PATTERNS)

        if not all_patterns:
            return None

        enhancement = random.choice(all_patterns)
        proposed = f"{original}\n\n{enhancement}"

        confidence = 0.6
        if enhancement in self.REASONING_PATTERNS:
            confidence = 0.7
        elif enhancement in self.REFLECTION_PATTERNS:
            confidence = 0.65
        elif enhancement in self.METACOGNITIVE_PATTERNS:
            confidence = 0.55

        return MutationProposal(
            mutation_type=self.mutation_type,
            target_key=target_key,
            original_value=original,
            proposed_value=proposed,
            reasoning=f"[STaR/Reflexion] Add: {enhancement}",
            confidence=confidence,
            gvu_phase=GVUPhase.GENERATE,
            uncertainty_type="epistemic",
        )

    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """Apply prompt mutation."""
        new_variant = variant.clone()
        new_variant.prompts[proposal.target_key] = proposal.proposed_value
        new_variant.metadata["last_mutation"] = proposal.reasoning
        new_variant.metadata["mutation_source"] = "prompt_mutator"
        new_variant.generation_quality = proposal.confidence
        return new_variant


class ToolMutator(BaseMutator):
    """Mutator for agent tools with synergy-aware selection."""

    mutation_type = MutationType.TOOL

    TOOL_CATALOG = {
        "code_search": {"category": "exploration", "synergies": ["file_reader", "grep"]},
        "file_reader": {"category": "exploration", "synergies": ["code_search"]},
        "file_writer": {"category": "modification", "synergies": ["file_reader"]},
        "test_runner": {"category": "validation", "synergies": ["linter", "type_checker"]},
        "linter": {"category": "validation", "synergies": ["test_runner", "code_formatter"]},
        "type_checker": {"category": "validation", "synergies": ["linter"]},
        "code_formatter": {"category": "modification", "synergies": ["linter"]},
        "documentation_lookup": {"category": "exploration", "synergies": ["web_search"]},
        "dependency_analyzer": {"category": "analysis", "synergies": ["security_scanner"]},
        "git_operations": {"category": "vcs", "synergies": ["file_reader", "file_writer"]},
        "web_search": {"category": "exploration", "synergies": ["documentation_lookup"]},
        "grep": {"category": "exploration", "synergies": ["code_search", "file_reader"]},
        "security_scanner": {"category": "validation", "synergies": ["dependency_analyzer"]},
    }

    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """Propose adding or removing a tool with synergy awareness."""
        current_tools = set(variant.tools)
        available = [t for t in self.TOOL_CATALOG if t not in current_tools]

        synergy_scores = {}
        for tool in available:
            tool_info = self.TOOL_CATALOG[tool]
            synergies = tool_info.get("synergies", [])
            score = sum(1 for s in synergies if s in current_tools)
            synergy_scores[tool] = score

        if available and random.random() < 0.75:
            if synergy_scores:
                max_synergy = max(synergy_scores.values())
                best_tools = [t for t, s in synergy_scores.items() if s == max_synergy]
                tool = random.choice(best_tools)
            else:  # pragma: no cover - defensive: dict always populated by loop above
                tool = random.choice(available)

            confidence = 0.5 + 0.1 * synergy_scores.get(tool, 0)
            return MutationProposal(
                mutation_type=self.mutation_type,
                target_key="add",
                original_value=list(variant.tools),
                proposed_value=tool,
                reasoning=f"Add tool: {tool} (synergy={synergy_scores.get(tool, 0)})",
                confidence=min(0.8, confidence),
                gvu_phase=GVUPhase.GENERATE,
                metadata={"synergy_score": synergy_scores.get(tool, 0)},
            )

        elif variant.tools:
            removal_scores = {}
            for tool in variant.tools:
                tool_info = self.TOOL_CATALOG.get(tool, {})
                synergies = tool_info.get("synergies", [])
                active_synergies = sum(1 for s in synergies if s in current_tools)
                removal_scores[tool] = active_synergies

            if removal_scores:
                min_synergy = min(removal_scores.values())
                removable = [t for t, s in removal_scores.items() if s == min_synergy]
                tool = random.choice(removable)
            else:  # pragma: no cover - defensive: dict always populated by loop above
                tool = random.choice(variant.tools)

            return MutationProposal(
                mutation_type=self.mutation_type,
                target_key="remove",
                original_value=list(variant.tools),
                proposed_value=tool,
                reasoning=f"Remove tool: {tool} (low synergy)",
                confidence=0.4,
                gvu_phase=GVUPhase.GENERATE,
            )

        return None

    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """Apply tool mutation."""
        new_variant = variant.clone()
        if proposal.target_key == "add":
            new_variant.tools.append(proposal.proposed_value)
        elif proposal.target_key == "remove":
            if proposal.proposed_value in new_variant.tools:
                new_variant.tools.remove(proposal.proposed_value)
        new_variant.metadata["last_mutation"] = proposal.reasoning
        new_variant.metadata["mutation_source"] = "tool_mutator"
        new_variant.generation_quality = proposal.confidence
        return new_variant


class WorkflowMutator(BaseMutator):
    """Mutator for execution workflows (ReAct, CoT, ToT, etc.)."""

    mutation_type = MutationType.WORKFLOW

    WORKFLOW_PATTERNS = {
        "react": {"planning": True, "reflection": False, "support": 0.8},
        "cot": {"planning": True, "chain_of_thought": True, "support": 0.85},
        "tot": {"planning": True, "reflection": True, "tree_search": True, "support": 0.7},
        "reflexion": {"planning": True, "reflection": True, "memory": True, "support": 0.75},
        "self_consistency": {"multiple_paths": True, "voting": True, "support": 0.8},
        "iterative": {"max_iterations": 3, "early_stop": True, "support": 0.65},
    }

    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """Propose a workflow change based on empirical evidence."""
        current = variant.workflow.get("pattern", "default")
        available = [p for p in self.WORKFLOW_PATTERNS if p != current]
        if not available:
            return None

        weights = [self.WORKFLOW_PATTERNS[p]["support"] for p in available]
        total = sum(weights)
        weights = [w / total for w in weights]

        new_pattern = random.choices(available, weights=weights, k=1)[0]
        pattern_info = self.WORKFLOW_PATTERNS[new_pattern]

        return MutationProposal(
            mutation_type=self.mutation_type,
            target_key="pattern",
            original_value=current,
            proposed_value=new_pattern,
            reasoning=f"[Workflow] Switch to {new_pattern}",
            confidence=pattern_info["support"],
            gvu_phase=GVUPhase.GENERATE,
            metadata={"config": pattern_info},
        )

    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """Apply workflow mutation."""
        new_variant = variant.clone()
        config = proposal.metadata.get("config", {})
        new_variant.workflow["pattern"] = proposal.proposed_value
        for key, value in config.items():
            if key != "support":
                new_variant.workflow[key] = value
        new_variant.metadata["last_mutation"] = proposal.reasoning
        new_variant.metadata["mutation_source"] = "workflow_mutator"
        new_variant.generation_quality = proposal.confidence
        return new_variant


class ParameterMutator(BaseMutator):
    """Mutator for hyperparameters using Gaussian perturbation."""

    mutation_type = MutationType.PARAMETER

    PARAMETER_RANGES = {
        "temperature": {"min": 0.0, "max": 2.0, "default": 0.7, "type": "float"},
        "top_p": {"min": 0.0, "max": 1.0, "default": 0.9, "type": "float"},
        "max_tokens": {"min": 100, "max": 8000, "default": 2000, "type": "int"},
        "frequency_penalty": {"min": 0.0, "max": 2.0, "default": 0.0, "type": "float"},
        "presence_penalty": {"min": 0.0, "max": 2.0, "default": 0.0, "type": "float"},
        "retry_count": {"min": 1, "max": 5, "default": 3, "type": "int"},
        "timeout_seconds": {"min": 30, "max": 300, "default": 60, "type": "int"},
    }

    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """Propose a parameter change using Gaussian perturbation."""
        param_name = random.choice(list(self.PARAMETER_RANGES.keys()))
        param_info = self.PARAMETER_RANGES[param_name]

        current_value = variant.parameters.get(param_name, param_info["default"])
        range_size = param_info["max"] - param_info["min"]
        perturbation = random.gauss(0, range_size * 0.1)

        new_value = current_value + perturbation
        new_value = max(param_info["min"], min(param_info["max"], new_value))
        if param_info["type"] == "int":
            new_value = int(round(new_value))

        if new_value == current_value:
            return None

        return MutationProposal(
            mutation_type=self.mutation_type,
            target_key=param_name,
            original_value=current_value,
            proposed_value=new_value,
            reasoning=f"Tune {param_name}: {current_value} → {new_value}",
            confidence=0.5,
            gvu_phase=GVUPhase.GENERATE,
        )

    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """Apply parameter mutation."""
        new_variant = variant.clone()
        new_variant.parameters[proposal.target_key] = proposal.proposed_value
        new_variant.metadata["last_mutation"] = proposal.reasoning
        new_variant.metadata["mutation_source"] = "parameter_mutator"
        new_variant.generation_quality = proposal.confidence
        return new_variant
