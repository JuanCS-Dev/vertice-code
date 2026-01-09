"""
Data Agent Parsers - Parse LLM analysis for database operations.

Extract structured data from LLM responses.
"""

from __future__ import annotations

import re
from typing import Any, Dict


def parse_query_analysis(analysis: str, original_query: str) -> Dict[str, Any]:
    """Parse LLM analysis to extract query optimization suggestions.

    Extracts:
    - Rewritten query (if present)
    - Suggested indexes
    - Confidence indicators

    Args:
        analysis: LLM analysis text.
        original_query: Original SQL query.

    Returns:
        Dict with 'rewritten_query', 'indexes', 'confidence' keys.
    """
    result = {
        "rewritten_query": original_query,
        "indexes": [],
        "confidence": 0.5,
    }

    if not analysis:
        return result

    analysis_lower = analysis.lower()

    # Extract rewritten query (look for SQL patterns)
    sql_patterns = [
        r"(?:optimized|rewritten|improved).*?:?\s*```(?:sql)?\s*(.+?)```",
        r"SELECT\s+.+?\s+FROM\s+.+?(?:WHERE|GROUP|ORDER|;|$)",
    ]

    for pattern in sql_patterns:
        match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
        if match:
            result["rewritten_query"] = (
                match.group(1).strip() if match.lastindex else match.group(0).strip()
            )
            break

    # Extract index suggestions
    index_patterns = [
        r"(?:CREATE\s+)?INDEX\s+(?:ON\s+)?(\w+)\s*\(([^)]+)\)",
        r"(\w+)\s*\(([^)]+)\)\s*(?:index|INDEX)",
    ]

    for pattern in index_patterns:
        matches = re.findall(pattern, analysis)
        for match in matches:
            if len(match) >= 2:
                result["indexes"].append(f"{match[0]}({match[1]})")

    # Estimate confidence from language
    high_conf_words = ["definitely", "certain", "clearly", "must", "highly recommend"]
    low_conf_words = ["possibly", "might", "could", "maybe", "uncertain"]

    for word in high_conf_words:
        if word in analysis_lower:
            result["confidence"] = min(0.9, result["confidence"] + 0.1)

    for word in low_conf_words:
        if word in analysis_lower:
            result["confidence"] = max(0.3, result["confidence"] - 0.1)

    return result


def parse_migration_analysis(analysis: str) -> Dict[str, Any]:
    """Parse LLM analysis to extract migration risk assessment.

    Extracts:
    - Risk level from LLM opinion
    - Downtime estimates
    - Online migration feasibility

    Args:
        analysis: LLM analysis text.

    Returns:
        Dict with 'risk_modifier', 'downtime_modifier', 'online_safe' keys.
    """
    result = {
        "risk_modifier": 0,  # -2 to +2 adjustment
        "downtime_modifier": 0.0,
        "online_safe": None,  # None = no opinion
    }

    if not analysis:
        return result

    analysis_lower = analysis.lower()

    # Check for risk indicators
    if any(w in analysis_lower for w in ["critical", "dangerous", "data loss", "high risk"]):
        result["risk_modifier"] = 2
    elif any(w in analysis_lower for w in ["risky", "caution", "careful"]):
        result["risk_modifier"] = 1
    elif any(w in analysis_lower for w in ["safe", "low risk", "straightforward"]):
        result["risk_modifier"] = -1

    # Check for downtime mentions
    time_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:seconds?|minutes?|hours?)", analysis_lower)
    if time_match:
        value = float(time_match.group(1))
        if "minute" in analysis_lower:
            value *= 60
        elif "hour" in analysis_lower:
            value *= 3600
        result["downtime_modifier"] = value

    # Check online migration feasibility
    if "online" in analysis_lower and "cannot" in analysis_lower:
        result["online_safe"] = False
    elif "online" in analysis_lower and "safe" in analysis_lower:
        result["online_safe"] = True

    return result


__all__ = ["parse_query_analysis", "parse_migration_analysis"]
