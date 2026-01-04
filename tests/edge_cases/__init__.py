"""
Edge Case Tests.

Comprehensive edge case testing for:
- Streaming (empty chunks, malformed JSON, connection drops)
- Rate Limiting (429/529 handling, retry logic)
- Context Window (boundaries, overflow, compaction)
- File Operations (binary files, permissions, symlinks)
- Agent Failures (timeouts, cascades, resource exhaustion)
"""
