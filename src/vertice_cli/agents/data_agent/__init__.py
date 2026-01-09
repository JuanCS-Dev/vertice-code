"""
Data Agent Module - Database optimization and schema analysis.

Production-ready DataAgent that works with existing infrastructure.

Submodules:
    - types: Domain models (IssueSeverity, SchemaIssue, etc.)
    - parsers: LLM response parsing
    - agent: DataAgent class
"""

from .types import (
    IssueSeverity,
    OptimizationType,
    DatabaseType,
    SchemaIssue,
    QueryOptimization,
    MigrationPlan,
)
from .parsers import parse_query_analysis, parse_migration_analysis
from .agent import DataAgent, create_data_agent

__all__ = [
    # Types
    "IssueSeverity",
    "OptimizationType",
    "DatabaseType",
    "SchemaIssue",
    "QueryOptimization",
    "MigrationPlan",
    # Parsers
    "parse_query_analysis",
    "parse_migration_analysis",
    # Agent
    "DataAgent",
    "create_data_agent",
]
