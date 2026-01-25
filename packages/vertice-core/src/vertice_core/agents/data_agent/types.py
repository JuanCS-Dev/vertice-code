"""
Data Agent Types - Domain models for database operations.

Enums and dataclasses for schema analysis, query optimization, and migrations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OptimizationType(str, Enum):
    """Types of optimizations."""

    INDEX = "index"
    QUERY_REWRITE = "query_rewrite"
    SCHEMA_CHANGE = "schema_change"
    CACHING = "caching"


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRES = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"


@dataclass
class SchemaIssue:
    """Schema issue detection result."""

    table: str
    severity: IssueSeverity
    issue_type: str
    description: str
    recommendation: str
    auto_fix_available: bool = False
    estimated_impact: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema issue to dictionary for serialization."""
        return {
            "table": self.table,
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "description": self.description,
            "recommendation": self.recommendation,
            "auto_fix_available": self.auto_fix_available,
            "estimated_impact": self.estimated_impact,
        }


@dataclass
class QueryOptimization:
    """Query optimization result."""

    query_hash: str
    original_query: str
    optimization_type: OptimizationType
    cost_before: float
    cost_after: float
    improvement_percent: float
    rewritten_query: Optional[str] = None
    required_indexes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert query optimization to dictionary for serialization."""
        return {
            "query_hash": self.query_hash,
            "optimization_type": self.optimization_type.value,
            "cost_before": self.cost_before,
            "cost_after": self.cost_after,
            "improvement_percent": self.improvement_percent,
            "rewritten_query": self.rewritten_query,
            "required_indexes": self.required_indexes,
            "confidence_score": self.confidence_score,
        }


@dataclass
class MigrationPlan:
    """Database migration plan."""

    version_id: str
    description: str
    up_commands: List[str]
    down_commands: List[str]
    risk_level: IssueSeverity
    estimated_downtime_seconds: float = 0.0
    can_run_online: bool = True
    requires_backup: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert migration plan to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "estimated_downtime_seconds": self.estimated_downtime_seconds,
            "can_run_online": self.can_run_online,
            "requires_backup": self.requires_backup,
        }


__all__ = [
    "IssueSeverity",
    "OptimizationType",
    "DatabaseType",
    "SchemaIssue",
    "QueryOptimization",
    "MigrationPlan",
]
