"""
ThoughtSignatures - Gemini 3-Style Reasoning Continuity.

Implements Thought Signatures pattern from Gemini 3 (Dec 2025):
- Encrypted representations of model's internal thought process
- Maintains reasoning context across API calls
- Prevents "reasoning drift" in long sessions
- Must be returned exactly as received for best results

Key Features:
- Hash-based signature generation
- Chain validation for continuity
- Automatic signature rotation
- Recovery from broken chains

References:
- Gemini 3 Developer Guide (Dec 2025)
- "Thought signatures maintain reasoning context across API calls"

Phase 10: Sprint 4 - Context Optimization

Soli Deo Gloria
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Signature settings
SIGNATURE_VERSION = "v1"
MAX_CHAIN_LENGTH = 20
SIGNATURE_TTL_SECONDS = 3600  # 1 hour


class SignatureStatus(str, Enum):
    """Status of a thought signature."""

    VALID = "valid"
    EXPIRED = "expired"
    BROKEN_CHAIN = "broken_chain"
    INVALID = "invalid"
    MISSING = "missing"


class ThinkingLevel(str, Enum):
    """Thinking levels (like Gemini 3)."""

    MINIMAL = "minimal"  # Fast, simple tasks
    LOW = "low"  # Quick responses
    MEDIUM = "medium"  # Balanced
    HIGH = "high"  # Complex reasoning


@dataclass
class ThoughtSignature:
    """
    A thought signature representing reasoning state.

    Inspired by Gemini 3's encrypted thought signatures that
    maintain reasoning context across API calls.
    """

    signature_id: str
    version: str
    timestamp: float
    thinking_level: ThinkingLevel
    thought_hash: str  # Hash of reasoning content
    key_insights: List[str]  # Top insights extracted
    next_action: str  # Planned next action
    chain_hash: str  # Hash linking to previous signature
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.signature_id,
            "v": self.version,
            "ts": self.timestamp,
            "level": self.thinking_level.value,
            "th": self.thought_hash,
            "insights": self.key_insights,
            "next": self.next_action,
            "chain": self.chain_hash,
            "meta": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtSignature":
        """Deserialize from dictionary."""
        return cls(
            signature_id=data["id"],
            version=data.get("v", SIGNATURE_VERSION),
            timestamp=data["ts"],
            thinking_level=ThinkingLevel(data.get("level", "medium")),
            thought_hash=data["th"],
            key_insights=data.get("insights", []),
            next_action=data.get("next", ""),
            chain_hash=data.get("chain", ""),
            metadata=data.get("meta", {}),
        )

    def encode(self) -> str:
        """Encode signature to string for transmission."""
        data = self.to_dict()
        json_str = json.dumps(data, separators=(",", ":"))
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    @classmethod
    def decode(cls, encoded: str) -> "ThoughtSignature":
        """Decode signature from string."""
        json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
        data = json.loads(json_str)
        return cls.from_dict(data)

    def is_expired(self, ttl: int = SIGNATURE_TTL_SECONDS) -> bool:
        """Check if signature is expired."""
        return time.time() - self.timestamp > ttl

    @property
    def age_seconds(self) -> float:
        """Age of signature in seconds."""
        return time.time() - self.timestamp


@dataclass
class SignatureValidation:
    """Result of signature validation."""

    status: SignatureStatus
    signature: Optional[ThoughtSignature]
    chain_position: int
    is_continuous: bool
    error: Optional[str] = None


@dataclass
class ReasoningContext:
    """
    Context extracted from thought signatures.

    Used to restore reasoning state after context compression.
    """

    key_insights: List[str]
    decisions_made: List[str]
    current_goal: str
    next_actions: List[str]
    thinking_level: ThinkingLevel
    chain_length: int


class ThoughtSignatureManager:
    """
    Manages thought signatures for reasoning continuity.

    Implements Gemini 3 pattern of maintaining reasoning state
    across API calls through encrypted signatures.

    Usage:
        manager = ThoughtSignatureManager()

        # Generate signature after reasoning
        sig = manager.create_signature(
            reasoning="Analysis shows...",
            insights=["Finding 1", "Finding 2"],
            next_action="Implement solution",
            level=ThinkingLevel.HIGH,
        )

        # Encode for transmission
        encoded = sig.encode()

        # Later: decode and validate
        restored = ThoughtSignature.decode(encoded)
        validation = manager.validate(restored)

        if validation.status == SignatureStatus.VALID:
            context = manager.get_reasoning_context()
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        max_chain_length: int = MAX_CHAIN_LENGTH,
        signature_ttl: int = SIGNATURE_TTL_SECONDS,
    ):
        """
        Initialize thought signature manager.

        Args:
            secret_key: Key for HMAC signing (generated if None)
            max_chain_length: Maximum signatures to keep in chain
            signature_ttl: Time-to-live for signatures in seconds
        """
        self._secret_key = secret_key or secrets.token_hex(32)
        self._max_chain_length = max_chain_length
        self._signature_ttl = signature_ttl
        self._chain: List[ThoughtSignature] = []
        self._current_level = ThinkingLevel.MEDIUM

    def create_signature(
        self,
        reasoning: str,
        insights: List[str],
        next_action: str,
        level: Optional[ThinkingLevel] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ThoughtSignature:
        """
        Create a new thought signature.

        Args:
            reasoning: The reasoning/thought process content
            insights: Key insights extracted from reasoning
            next_action: Planned next action
            level: Thinking level used
            metadata: Additional metadata

        Returns:
            New ThoughtSignature
        """
        level = level or self._current_level
        self._current_level = level

        # Generate thought hash
        thought_hash = self._hash_content(reasoning)

        # Generate chain hash (links to previous)
        if self._chain:
            prev_sig = self._chain[-1]
            chain_hash = self._hash_content(f"{prev_sig.signature_id}:{prev_sig.thought_hash}")
        else:
            chain_hash = self._hash_content("genesis")

        # Generate unique ID
        signature_id = self._generate_id()

        signature = ThoughtSignature(
            signature_id=signature_id,
            version=SIGNATURE_VERSION,
            timestamp=time.time(),
            thinking_level=level,
            thought_hash=thought_hash,
            key_insights=insights[:5],  # Keep top 5
            next_action=next_action,
            chain_hash=chain_hash,
            metadata=metadata or {},
        )

        # Add to chain
        self._chain.append(signature)

        # Prune old signatures
        if len(self._chain) > self._max_chain_length:
            self._chain = self._chain[-self._max_chain_length :]

        return signature

    def validate(
        self,
        signature: ThoughtSignature,
    ) -> SignatureValidation:
        """
        Validate a thought signature.

        Args:
            signature: Signature to validate

        Returns:
            SignatureValidation with status and details
        """
        # Check expiration
        if signature.is_expired(self._signature_ttl):
            return SignatureValidation(
                status=SignatureStatus.EXPIRED,
                signature=signature,
                chain_position=-1,
                is_continuous=False,
                error=f"Signature expired ({signature.age_seconds:.0f}s old)",
            )

        # Find in chain
        chain_position = -1
        for i, sig in enumerate(self._chain):
            if sig.signature_id == signature.signature_id:
                chain_position = i
                break

        if chain_position == -1:
            # Not in chain - could be from different session
            return SignatureValidation(
                status=SignatureStatus.BROKEN_CHAIN,
                signature=signature,
                chain_position=-1,
                is_continuous=False,
                error="Signature not found in current chain",
            )

        # Verify chain continuity
        is_continuous = self._verify_chain_continuity(chain_position)

        return SignatureValidation(
            status=SignatureStatus.VALID,
            signature=signature,
            chain_position=chain_position,
            is_continuous=is_continuous,
        )

    def validate_and_restore(
        self,
        encoded: str,
    ) -> Tuple[SignatureValidation, Optional[ReasoningContext]]:
        """
        Validate encoded signature and restore context if valid.

        Args:
            encoded: Encoded signature string

        Returns:
            Tuple of (validation result, reasoning context if valid)
        """
        try:
            signature = ThoughtSignature.decode(encoded)
            validation = self.validate(signature)

            if validation.status == SignatureStatus.VALID:
                context = self.get_reasoning_context()
                return validation, context

            return validation, None

        except Exception as e:
            return (
                SignatureValidation(
                    status=SignatureStatus.INVALID,
                    signature=None,
                    chain_position=-1,
                    is_continuous=False,
                    error=str(e),
                ),
                None,
            )

    def get_reasoning_context(self) -> ReasoningContext:
        """
        Get current reasoning context from signature chain.

        Returns:
            ReasoningContext with aggregated insights
        """
        if not self._chain:
            return ReasoningContext(
                key_insights=[],
                decisions_made=[],
                current_goal="",
                next_actions=[],
                thinking_level=self._current_level,
                chain_length=0,
            )

        # Aggregate insights from chain
        all_insights = []
        all_next_actions = []
        decisions = []

        for sig in self._chain:
            all_insights.extend(sig.key_insights)
            if sig.next_action:
                all_next_actions.append(sig.next_action)
            if sig.metadata.get("decision"):
                decisions.append(sig.metadata["decision"])

        # Deduplicate and limit
        unique_insights = list(dict.fromkeys(all_insights))[:10]
        unique_actions = list(dict.fromkeys(all_next_actions))[:5]

        # Get current goal from latest signature
        latest = self._chain[-1]
        current_goal = latest.metadata.get("goal", latest.next_action)

        return ReasoningContext(
            key_insights=unique_insights,
            decisions_made=decisions[-5:],
            current_goal=current_goal,
            next_actions=unique_actions,
            thinking_level=self._current_level,
            chain_length=len(self._chain),
        )

    def get_latest_signature(self) -> Optional[ThoughtSignature]:
        """Get the most recent signature in the chain."""
        return self._chain[-1] if self._chain else None

    def get_encoded_chain(self) -> List[str]:
        """Get all signatures encoded for transmission."""
        return [sig.encode() for sig in self._chain]

    def restore_chain(self, encoded_chain: List[str]) -> int:
        """
        Restore signature chain from encoded signatures.

        Args:
            encoded_chain: List of encoded signatures

        Returns:
            Number of signatures restored
        """
        restored = 0
        for encoded in encoded_chain:
            try:
                sig = ThoughtSignature.decode(encoded)
                if not sig.is_expired(self._signature_ttl):
                    self._chain.append(sig)
                    restored += 1
            except (ValueError, KeyError, TypeError):
                continue

        # Prune if needed
        if len(self._chain) > self._max_chain_length:
            self._chain = self._chain[-self._max_chain_length :]

        return restored

    def clear_chain(self) -> int:
        """Clear the signature chain. Returns count of cleared signatures."""
        count = len(self._chain)
        self._chain.clear()
        return count

    def set_thinking_level(self, level: ThinkingLevel) -> None:
        """Set the current thinking level."""
        self._current_level = level

    def get_thinking_level(self) -> ThinkingLevel:
        """Get the current thinking level."""
        return self._current_level

    def _hash_content(self, content: str) -> str:
        """Generate HMAC hash of content."""
        h = hmac.new(self._secret_key.encode(), content.encode(), hashlib.sha256)
        return h.hexdigest()[:16]

    def _generate_id(self) -> str:
        """Generate unique signature ID."""
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(4)
        return f"ts_{timestamp}_{random_part}"

    def _verify_chain_continuity(self, position: int) -> bool:
        """Verify chain is continuous up to position."""
        if position == 0:
            return True

        for i in range(1, position + 1):
            current = self._chain[i]
            previous = self._chain[i - 1]

            expected_chain_hash = self._hash_content(
                f"{previous.signature_id}:{previous.thought_hash}"
            )

            if current.chain_hash != expected_chain_hash:
                return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get signature manager statistics."""
        return {
            "chain_length": len(self._chain),
            "max_chain_length": self._max_chain_length,
            "current_level": self._current_level.value,
            "signature_ttl": self._signature_ttl,
            "oldest_age": (self._chain[0].age_seconds if self._chain else 0),
            "newest_age": (self._chain[-1].age_seconds if self._chain else 0),
        }


# Singleton instance
_manager: Optional[ThoughtSignatureManager] = None


def get_thought_manager() -> ThoughtSignatureManager:
    """Get or create singleton thought signature manager."""
    global _manager
    if _manager is None:
        _manager = ThoughtSignatureManager()
    return _manager


def create_thought_signature(
    reasoning: str,
    insights: List[str],
    next_action: str,
    level: ThinkingLevel = ThinkingLevel.MEDIUM,
) -> str:
    """
    Convenience function to create and encode a thought signature.

    Args:
        reasoning: The reasoning content
        insights: Key insights
        next_action: Next planned action
        level: Thinking level

    Returns:
        Encoded signature string
    """
    manager = get_thought_manager()
    sig = manager.create_signature(
        reasoning=reasoning,
        insights=insights,
        next_action=next_action,
        level=level,
    )
    return sig.encode()


__all__ = [
    "SignatureStatus",
    "ThinkingLevel",
    "ThoughtSignature",
    "SignatureValidation",
    "ReasoningContext",
    "ThoughtSignatureManager",
    "get_thought_manager",
    "create_thought_signature",
]
