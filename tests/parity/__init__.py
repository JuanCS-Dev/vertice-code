"""
Parity Test Suite - Vertice vs Claude Code/Gemini CLI

This test suite validates that Vertice achieves functional parity
with Claude Code and Gemini CLI in key areas:

1. Task Decomposition - Multi-step requests properly broken down
2. Intent Recognition - Semantic understanding of user requests
3. Agent Orchestration - Correct agent selection and coordination
4. Tool Execution - Proper tool chaining and parallel execution
5. Error Recovery - Graceful handling and escalation
6. Provider Routing - Multi-provider failover
7. Plan Gating - User approval before execution
"""

__version__ = "1.0.0"
