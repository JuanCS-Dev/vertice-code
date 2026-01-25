"""
Distributed Skills Registry - Skills Sharing Across Prometheus Instances

This registry extends PrometheusSkillsRegistry to enable peer-to-peer
skills sharing and collective learning across distributed instances.

Created with love for collaborative AI evolution.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from prometheus.skills.registry import PrometheusSkillsRegistry, LearnedSkill
from prometheus.distributed.skills_discovery import SkillsDiscoveryService

logger = logging.getLogger(__name__)


@dataclass
class SkillConflict:
    """Represents a conflict between local and peer skill versions."""

    skill_name: str
    local_skill: LearnedSkill
    peer_skill: LearnedSkill
    peer_id: str
    conflict_reason: str
    resolution_strategy: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "local_skill": self.local_skill.to_dict(),
            "peer_skill": self.peer_skill.to_dict(),
            "peer_id": self.peer_id,
            "conflict_reason": self.conflict_reason,
            "resolution_strategy": self.resolution_strategy,
        }


class SkillsConsensusManager:
    """
    Manages consensus and conflict resolution for distributed skills.

    Implements strategies for resolving conflicts when multiple instances
    have different versions of the same skill.
    """

    def __init__(self):
        self.conflict_history: List[SkillConflict] = []
        self.consensus_rules = {
            "success_rate_priority": 0.7,  # Weight for success rate
            "recency_priority": 0.2,  # Weight for how recent the skill is
            "usage_priority": 0.1,  # Weight for usage count
        }

    def resolve_skill_conflict(
        self, skill_name: str, local_skill: LearnedSkill, peer_skill: LearnedSkill, peer_id: str
    ) -> LearnedSkill:
        """
        Resolve conflict between local and peer skill versions.

        Uses weighted scoring based on success rate, recency, and usage.
        """
        conflict = SkillConflict(
            skill_name=skill_name,
            local_skill=local_skill,
            peer_skill=peer_skill,
            peer_id=peer_id,
            conflict_reason=self._determine_conflict_reason(local_skill, peer_skill),
        )

        # Calculate scores for both versions
        local_score = self._calculate_skill_score(local_skill)
        peer_score = self._calculate_skill_score(peer_skill)

        # Choose winner based on score
        if peer_score > local_score:
            conflict.resolution_strategy = "peer_higher_score"
            winner = peer_skill
        elif peer_score == local_score:
            # Tie-breaker: prefer more recent
            if peer_skill.learned_at > local_skill.learned_at:
                conflict.resolution_strategy = "peer_more_recent"
                winner = peer_skill
            else:
                conflict.resolution_strategy = "local_more_recent"
                winner = local_skill
        else:
            conflict.resolution_strategy = "local_higher_score"
            winner = local_skill

        # Record conflict for analysis
        self.conflict_history.append(conflict)

        logger.info(
            f"Resolved skill conflict for '{skill_name}': "
            f"{conflict.resolution_strategy} "
            f"(local: {local_score:.2f}, peer: {peer_score:.2f})"
        )

        return winner

    def _calculate_skill_score(self, skill: LearnedSkill) -> float:
        """Calculate a consensus score for a skill."""
        # Success rate is most important
        success_score = skill.success_rate * self.consensus_rules["success_rate_priority"]

        # Recency bonus (newer skills get slight preference)
        now = datetime.now()
        days_old = (now - skill.learned_at).days
        recency_score = min(1.0, 30 / max(days_old, 1)) * self.consensus_rules["recency_priority"]

        # Usage bonus (more used skills get preference)
        usage_score = min(1.0, skill.usage_count / 10) * self.consensus_rules["usage_priority"]

        return success_score + recency_score + usage_score

    def _determine_conflict_reason(self, local: LearnedSkill, peer: LearnedSkill) -> str:
        """Determine the reason for a skill conflict."""
        if local.procedure_steps != peer.procedure_steps:
            return "different_procedures"
        elif abs(local.success_rate - peer.success_rate) > 0.1:
            return "different_success_rates"
        elif local.category != peer.category:
            return "different_categories"
        else:
            return "minor_differences"

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get statistics about resolved conflicts."""
        if not self.conflict_history:
            return {"total_conflicts": 0}

        resolution_counts = {}
        for conflict in self.conflict_history:
            resolution_counts[conflict.resolution_strategy] = (
                resolution_counts.get(conflict.resolution_strategy, 0) + 1
            )

        return {
            "total_conflicts": len(self.conflict_history),
            "resolution_breakdown": resolution_counts,
            "most_common_reason": max(
                (c.conflict_reason for c in self.conflict_history),
                key=lambda x: sum(1 for c in self.conflict_history if c.conflict_reason == x),
            ),
        }


class DistributedSkillsRegistry(PrometheusSkillsRegistry):
    """
    Distributed extension of PrometheusSkillsRegistry.

    Enables peer-to-peer skills sharing and collective learning across
    multiple Prometheus instances.
    """

    def __init__(
        self,
        memory_system=None,
        discovery_service: Optional[SkillsDiscoveryService] = None,
        instance_id: str = None,
    ):
        super().__init__(memory_system)

        # Distributed components
        self.discovery_service = discovery_service
        self.consensus_manager = SkillsConsensusManager()

        # Distributed state
        self.instance_id = instance_id or f"instance_{hash(self):x}"
        self.peer_skills_cache: Dict[str, List[LearnedSkill]] = {}
        self.last_sync_time: Optional[datetime] = None
        self.sync_interval = timedelta(minutes=5)

        # Configuration
        self.auto_sync_enabled = True
        self.max_peer_skills = 1000  # Limit skills from peers
        self.quality_threshold = 0.7  # Minimum quality for peer skills

        logger.info(f"Initialized Distributed Skills Registry for instance {self.instance_id}")

    def set_discovery_service(self, discovery_service: SkillsDiscoveryService):
        """Set the discovery service for peer communication."""
        self.discovery_service = discovery_service
        logger.info("Discovery service configured for distributed registry")

    async def sync_with_peers(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize skills with all known peers.

        Returns statistics about the sync operation.
        """
        if not self.discovery_service:
            return {"error": "No discovery service configured"}

        # Check if sync is needed
        if (
            not force
            and self.last_sync_time
            and (datetime.now() - self.last_sync_time) < self.sync_interval
        ):
            return {"skipped": "Sync interval not reached"}

        logger.info("Starting skills synchronization with peers...")

        peers = await self.discovery_service.discover_peers()
        if not peers:
            return {"peers_found": 0, "skills_synced": 0}

        sync_stats = {
            "peers_found": len(peers),
            "peers_contacted": 0,
            "skills_received": 0,
            "skills_added": 0,
            "conflicts_resolved": 0,
            "errors": 0,
        }

        # Sync with each peer concurrently
        tasks = [self._sync_with_peer(peer_id) for peer_id in peers[:10]]  # Limit concurrent peers
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                sync_stats["errors"] += 1
                continue

            sync_stats["peers_contacted"] += 1
            sync_stats["skills_received"] += result.get("skills_received", 0)
            sync_stats["skills_added"] += result.get("skills_added", 0)
            sync_stats["conflicts_resolved"] += result.get("conflicts_resolved", 0)

        self.last_sync_time = datetime.now()

        logger.info(
            f"Skills sync completed: {sync_stats['skills_added']} skills added, "
            f"{sync_stats['conflicts_resolved']} conflicts resolved from {sync_stats['peers_contacted']} peers"
        )

        return sync_stats

    async def share_top_skills(self, top_k: int = 10, min_quality: float = 0.8) -> int:
        """
        Share the top skills with peers.

        Only shares skills above quality threshold to maintain ecosystem health.

        Returns number of skills shared.
        """
        if not self.discovery_service:
            return 0

        # Get top skills above quality threshold
        all_skills = await self.list_skills(sort_by="success_rate")
        top_skills = [
            skill
            for skill in all_skills[: top_k * 2]  # Get more to filter
            if skill.success_rate >= min_quality
        ][:top_k]  # Take top k

        if not top_skills:
            logger.debug("No high-quality skills to share")
            return 0

        # Share each skill
        shared_count = 0
        for skill in top_skills:
            try:
                await self.discovery_service.broadcast_skill(skill)
                shared_count += 1
            except Exception as e:
                logger.warning(f"Failed to share skill '{skill.name}': {e}")

        logger.info(f"Shared {shared_count} high-quality skills with peers")
        return shared_count

    async def request_skill_from_peers(self, skill_name: str) -> Optional[LearnedSkill]:
        """
        Request a specific skill from peers.

        Useful when local instance lacks a needed skill.
        """
        if not self.discovery_service:
            return None

        peers = await self.discovery_service.discover_peers()

        # Try to get skill from peers
        for peer_id in peers[:5]:  # Limit peer requests
            try:
                skill = await self.discovery_service.request_skill(skill_name, peer_id)
                if skill and skill.success_rate >= self.quality_threshold:
                    # Validate and register locally
                    await self._register_peer_skill(skill, peer_id)
                    logger.info(f"Acquired skill '{skill_name}' from peer {peer_id}")
                    return skill
            except Exception as e:
                logger.debug(f"Failed to get skill '{skill_name}' from peer {peer_id}: {e}")

        return None

    async def _sync_with_peer(self, peer_id: str) -> Dict[str, int]:
        """Synchronize skills with a specific peer."""
        stats = {"skills_received": 0, "skills_added": 0, "conflicts_resolved": 0}

        try:
            # Get peer skills
            peer_skills = await self.discovery_service.get_peer_skills(peer_id)
            stats["skills_received"] = len(peer_skills)

            # Process each skill
            for peer_skill in peer_skills:
                if peer_skill.success_rate < self.quality_threshold:
                    continue  # Skip low-quality skills

                result = await self._register_peer_skill(peer_skill, peer_id)
                if result["added"]:
                    stats["skills_added"] += 1
                if result["conflict_resolved"]:
                    stats["conflicts_resolved"] += 1

        except Exception as e:
            logger.warning(f"Error syncing with peer {peer_id}: {e}")

        return stats

    async def _register_peer_skill(self, skill: LearnedSkill, peer_id: str) -> Dict[str, bool]:
        """
        Register a skill received from a peer.

        Handles conflicts and quality validation.
        """
        result = {"added": False, "conflict_resolved": False}

        # Check if we already have this skill
        existing_skill = await self.get_skill(skill.name)

        if existing_skill:
            # Resolve conflict
            winner_skill = self.consensus_manager.resolve_skill_conflict(
                skill.name, existing_skill, skill, peer_id
            )

            # Update if peer version won
            if winner_skill is skill:
                self.learned_skills[skill.name] = skill
                result["conflict_resolved"] = True
                result["added"] = True
        else:
            # New skill - register it
            self.learned_skills[skill.name] = skill
            result["added"] = True

            # Persist if we have memory system
            if self.memory_system:
                await self._persist_skill(skill)

        return result

    async def merge_peer_skills(
        self, peer_id: str, peer_skills: List[LearnedSkill]
    ) -> Dict[str, int]:
        """
        Merge skills from a peer into local registry.

        Returns statistics about the merge operation.
        """
        stats = {"processed": 0, "added": 0, "updated": 0, "rejected": 0, "conflicts": 0}

        for skill in peer_skills:
            stats["processed"] += 1

            # Quality filter
            if skill.success_rate < self.quality_threshold:
                stats["rejected"] += 1
                continue

            # Check existing
            existing = await self.get_skill(skill.name)
            if existing:
                # Resolve conflict
                winner = self.consensus_manager.resolve_skill_conflict(
                    skill.name, existing, skill, peer_id
                )
                if winner is skill:
                    self.learned_skills[skill.name] = skill
                    stats["updated"] += 1
                    stats["conflicts"] += 1
            else:
                # Add new skill
                self.learned_skills[skill.name] = skill
                stats["added"] += 1

                # Persist
                if self.memory_system:
                    await self._persist_skill(skill)

        logger.debug(f"Merged skills from peer {peer_id}: {stats}")
        return stats

    async def get_distributed_stats(self) -> Dict[str, Any]:
        """Get comprehensive distributed registry statistics."""
        base_stats = await self.get_stats()

        distributed_stats = {
            **base_stats,
            "instance_id": self.instance_id,
            "distributed_features": {
                "auto_sync_enabled": self.auto_sync_enabled,
                "quality_threshold": self.quality_threshold,
                "sync_interval_minutes": self.sync_interval.total_seconds() / 60,
                "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "cached_peer_skills": len(self.peer_skills_cache),
            },
        }

        # Add discovery service stats if available
        if self.discovery_service:
            discovery_stats = self.discovery_service.get_stats()
            distributed_stats["discovery"] = discovery_stats

        # Add consensus stats
        consensus_stats = self.consensus_manager.get_conflict_stats()
        distributed_stats["consensus"] = consensus_stats

        return distributed_stats

    def enable_auto_sync(self, enabled: bool = True):
        """Enable/disable automatic synchronization with peers."""
        self.auto_sync_enabled = enabled
        logger.info(f"Auto-sync {'enabled' if enabled else 'disabled'}")

    def set_quality_threshold(self, threshold: float):
        """Set minimum quality threshold for accepting peer skills."""
        self.quality_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Quality threshold set to {self.quality_threshold}")

    def set_sync_interval(self, minutes: int):
        """Set synchronization interval in minutes."""
        self.sync_interval = timedelta(minutes=max(1, minutes))
        logger.info(f"Sync interval set to {minutes} minutes")
