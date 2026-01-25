"""
DataAgent Production v1.0 - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- data_agent/types.py: IssueSeverity, DatabaseType, SchemaIssue, etc.
- data_agent/parsers.py: LLM response parsing
- data_agent/agent.py: DataAgent class

All symbols are re-exported here for backward compatibility.
Import from 'data_agent' subpackage for new code.

Philosophy: "Ship code that works today, not dreams for tomorrow."
"""

# Re-export all public symbols for backward compatibility
from .data_agent import (
    # Types
    IssueSeverity,
    OptimizationType,
    DatabaseType,
    SchemaIssue,
    QueryOptimization,
    MigrationPlan,
    # Agent
    DataAgent,
    create_data_agent,
)

__all__ = [
    "IssueSeverity",
    "OptimizationType",
    "DatabaseType",
    "SchemaIssue",
    "QueryOptimization",
    "MigrationPlan",
    "DataAgent",
    "create_data_agent",
]
