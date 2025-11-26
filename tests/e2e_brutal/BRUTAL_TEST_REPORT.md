# BRUTAL E2E TEST REPORT - qwen-dev-cli

**Generated:** 2025-11-24 17:59:22
**Total Issues Found:** 88
**Test Exit Code:** 0

---

## Executive Summary

This report documents all issues found during brutal E2E testing of the qwen-dev-cli shell.
Tests were designed from three user perspectives:

1. **Senior Developer** - Expects precision, reliability, professional error handling
2. **Vibe Coder** - Beginner who expects magic, gives vague instructions
3. **Script Kid** - Malicious actor attempting to break security

---

## Issue Distribution

### By Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| CRITICAL | 1 | 1% |
| HIGH | 14 | 15% |
| MEDIUM | 64 | 72% |
| LOW | 9 | 10% |

### By Category

| Category | Count |
|----------|-------|
| INTEGRATION | 13 |
| LOGIC | 6 |
| PERFORMANCE | 1 |
| SECURITY | 4 |
| UNKNOWN | 49 |
| UX | 15 |

### By User Persona

| Persona | Count |
|---------|-------|
| INTEGRATION | 18 |
| SCRIPT_KID | 20 |
| SENIOR | 17 |
| STRESS_TEST | 14 |
| VIBE_CODER | 19 |


---

## Critical Issues (Must Fix)

### ISSUE-055: Python code shouldn't escape sandbox.
- **Category:** UNKNOWN
- **Persona:** SCRIPT_KID
- **File:** test_script_kid.py


---

## High Priority Issues

### ISSUE-003: Git operations outside repo should have clear error.
- **Category:** UNKNOWN
- **Persona:** SENIOR
- **File:** test_senior_developer.py

### ISSUE-011: LLM timeout should be handled gracefully.
- **Category:** LOGIC
- **Persona:** SENIOR
- **File:** test_senior_developer.py

### ISSUE-025: AI should use visible context.
- **Category:** UX
- **Persona:** VIBE_CODER
- **File:** test_vibe_coder.py

### ISSUE-027: AI should detect what file user is talking about.
- **Category:** UX
- **Persona:** VIBE_CODER
- **File:** test_vibe_coder.py

### ISSUE-030: System should support easy undo.
- **Category:** UX
- **Persona:** VIBE_CODER
- **File:** test_vibe_coder.py

### ISSUE-044: Infinite loop in generated code should be caught.
- **Category:** SECURITY
- **Persona:** SCRIPT_KID
- **File:** test_script_kid.py

### ISSUE-045: Memory exhaustion should be prevented.
- **Category:** SECURITY
- **Persona:** SCRIPT_KID
- **File:** test_script_kid.py

### ISSUE-054: Indirect prompt injection via files.
- **Category:** SECURITY
- **Persona:** SCRIPT_KID
- **File:** test_script_kid.py

### ISSUE-066: Partial failures should leave clean state.
- **Category:** LOGIC
- **Persona:** STRESS_TEST
- **File:** test_stress_edge_cases.py

### ISSUE-068: Disk full should be handled gracefully.
- **Category:** LOGIC
- **Persona:** STRESS_TEST
- **File:** test_stress_edge_cases.py

### ISSUE-071: Planner output should be executable by Executor.
- **Category:** INTEGRATION
- **Persona:** INTEGRATION
- **File:** test_agent_integration.py

### ISSUE-077: System should create working Flask app.
- **Category:** UNKNOWN
- **Persona:** INTEGRATION
- **File:** test_agent_integration.py

### ISSUE-078: System should create working CLI tool.
- **Category:** INTEGRATION
- **Persona:** INTEGRATION
- **File:** test_agent_integration.py

### ISSUE-086: Session context should persist across commands.
- **Category:** INTEGRATION
- **Persona:** INTEGRATION
- **File:** test_agent_integration.py


---

## Medium Priority Issues

- **ISSUE-001**: Creating file in non-existent directory should fail gracefully. (UNKNOWN)
- **ISSUE-002**: File writes should be atomic to prevent corruption. (UNKNOWN)
- **ISSUE-004**: Concurrent access to same file should be handled. (UNKNOWN)
- **ISSUE-005**: Path traversal should be blocked. (UNKNOWN)
- **ISSUE-006**: Empty files should be handled correctly. (UNKNOWN)
- **ISSUE-007**: Large files should not cause OOM. (UNKNOWN)
- **ISSUE-008**: Agent should validate tasks before execution. (LOGIC)
- **ISSUE-009**: Agent responses should have consistent structure. (UNKNOWN)
- **ISSUE-010**: Agents should strictly enforce capabilities. (UNKNOWN)
- **ISSUE-012**: Network errors should have retry logic. (UNKNOWN)
- **ISSUE-013**: Shell should handle SIGINT gracefully. (UNKNOWN)
- **ISSUE-014**: Error messages should be consistent language. (UNKNOWN)
- **ISSUE-015**: CLI help should be comprehensive. (UNKNOWN)
- **ISSUE-016**: Version should follow semver. (UNKNOWN)
- **ISSUE-017**: CLI should use proper exit codes. (UNKNOWN)
- **ISSUE-018**: Vague file creation request handling. (UNKNOWN)
- **ISSUE-019**: System should tolerate common typos. (UNKNOWN)
- **ISSUE-021**: Import errors should be user-friendly. (UNKNOWN)
- **ISSUE-022**: Syntax errors should be explained simply. (UNKNOWN)
- **ISSUE-023**: Permission errors should explain resolution. (UNKNOWN)
- **ISSUE-024**: Network errors should check common causes. (UX)
- **ISSUE-026**: AI should understand (UX)
- **ISSUE-031**: System should handle multiline paste. (UX)
- **ISSUE-033**: System should extract code from markdown. (UX)
- **ISSUE-034**: Long operations should show progress. (UX)
- **ISSUE-037**: Semicolon command chaining should be blocked. (UNKNOWN)
- **ISSUE-038**: Backtick command substitution should be blocked. (UNKNOWN)
- **ISSUE-039**: $() command substitution should be blocked. (UNKNOWN)
- **ISSUE-040**: Newline injection should be blocked. (UNKNOWN)
- **ISSUE-041**: ../../../ path traversal should be blocked. (UNKNOWN)
- **ISSUE-042**: Null byte injection should be blocked. (UNKNOWN)
- **ISSUE-043**: Symlink attacks should be prevented. (UNKNOWN)
- **ISSUE-046**: Fork bomb should be detected and blocked. (UNKNOWN)
- **ISSUE-047**: Disk filling attacks should be limited. (SECURITY)
- **ISSUE-048**: sudo commands should be blocked. (UNKNOWN)
- **ISSUE-049**: setuid manipulation should be blocked. (UNKNOWN)
- **ISSUE-050**: Dangerous env variables should be blocked. (UNKNOWN)
- **ISSUE-051**: Data exfiltration via curl should be blocked. (UNKNOWN)
- **ISSUE-052**: DNS exfiltration should be considered. (UNKNOWN)
- **ISSUE-053**: User can't override system prompt. (UNKNOWN)
- **ISSUE-056**: File descriptors shouldn't leak info. (UNKNOWN)
- **ISSUE-057**: Concurrent file reads should be safe. (UNKNOWN)
- **ISSUE-058**: Concurrent writes to same file should be serialized. (UNKNOWN)
- **ISSUE-059**: Multiple agent executions should not interfere. (INTEGRATION)
- **ISSUE-060**: Writing very large file content should work. (UNKNOWN)
- **ISSUE-061**: Very long command should be handled. (UNKNOWN)
- **ISSUE-062**: Directory with many files should work. (UNKNOWN)
- **ISSUE-063**: Unicode filenames should work. (UNKNOWN)
- **ISSUE-064**: Unicode content should be preserved. (UNKNOWN)
- **ISSUE-065**: Special characters in path should be escaped. (UNKNOWN)
- **ISSUE-067**: Network timeouts should retry gracefully. (LOGIC)
- **ISSUE-069**: API rate limits should be handled. (LOGIC)
- **ISSUE-072**: Explorer findings should propagate to other agents. (INTEGRATION)
- **ISSUE-073**: Reviewer feedback should trigger corrections. (INTEGRATION)
- **ISSUE-074**: Architect phase should exist and work. (UNKNOWN)
- **ISSUE-075**: DevSquad should enforce phase ordering. (INTEGRATION)
- **ISSUE-076**: Failed phases should allow rollback. (INTEGRATION)
- **ISSUE-079**: System should create working data processor. (INTEGRATION)
- **ISSUE-080**: Governance should block dangerous operations. (INTEGRATION)
- **ISSUE-082**: All governance decisions should be logged. (INTEGRATION)
- **ISSUE-083**: Read → Modify → Write should be atomic. (UNKNOWN)
- **ISSUE-084**: Search → Edit chain should preserve context. (UNKNOWN)
- **ISSUE-085**: Git workflow should be chainable. (INTEGRATION)
- **ISSUE-087**: Session should recover from crash. (INTEGRATION)

---

## Low Priority Issues

- **ISSUE-020**: Incomplete commands should get helpful prompts. (UX)
- **ISSUE-028**: System should not get frustrated with repetition. (UX)
- **ISSUE-029**: System should detect user frustration. (UX)
- **ISSUE-032**: System should handle StackOverflow-style paste. (UX)
- **ISSUE-035**: Complex operations should explain steps. (UX)
- **ISSUE-036**: Success should be clearly communicated. (UX)
- **ISSUE-070**: Rapid tool calls should be throttled. (PERFORMANCE)
- **ISSUE-081**: Sofia counsel should be available. (UNKNOWN)
- **ISSUE-088**: Command history should persist. (UX)

---

## Complete Issue List

| ID | Title | Severity | Category | Persona |
|----|-------|----------|----------|---------|
| ISSUE-001 | Creating file in non-existent directory should fai... | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-002 | File writes should be atomic to prevent corruption... | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-003 | Git operations outside repo should have clear erro... | HIGH | UNKNOWN | SENIOR |
| ISSUE-004 | Concurrent access to same file should be handled. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-005 | Path traversal should be blocked. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-006 | Empty files should be handled correctly. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-007 | Large files should not cause OOM. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-008 | Agent should validate tasks before execution. | MEDIUM | LOGIC | SENIOR |
| ISSUE-009 | Agent responses should have consistent structure. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-010 | Agents should strictly enforce capabilities. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-011 | LLM timeout should be handled gracefully. | HIGH | LOGIC | SENIOR |
| ISSUE-012 | Network errors should have retry logic. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-013 | Shell should handle SIGINT gracefully. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-014 | Error messages should be consistent language. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-015 | CLI help should be comprehensive. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-016 | Version should follow semver. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-017 | CLI should use proper exit codes. | MEDIUM | UNKNOWN | SENIOR |
| ISSUE-018 | Vague file creation request handling. | MEDIUM | UNKNOWN | VIBE_CODER |
| ISSUE-019 | System should tolerate common typos. | MEDIUM | UNKNOWN | VIBE_CODER |
| ISSUE-020 | Incomplete commands should get helpful prompts. | LOW | UX | VIBE_CODER |
| ISSUE-021 | Import errors should be user-friendly. | MEDIUM | UNKNOWN | VIBE_CODER |
| ISSUE-022 | Syntax errors should be explained simply. | MEDIUM | UNKNOWN | VIBE_CODER |
| ISSUE-023 | Permission errors should explain resolution. | MEDIUM | UNKNOWN | VIBE_CODER |
| ISSUE-024 | Network errors should check common causes. | MEDIUM | UX | VIBE_CODER |
| ISSUE-025 | AI should use visible context. | HIGH | UX | VIBE_CODER |
| ISSUE-026 | AI should understand | MEDIUM | UX | VIBE_CODER |
| ISSUE-027 | AI should detect what file user is talking about. | HIGH | UX | VIBE_CODER |
| ISSUE-028 | System should not get frustrated with repetition. | LOW | UX | VIBE_CODER |
| ISSUE-029 | System should detect user frustration. | LOW | UX | VIBE_CODER |
| ISSUE-030 | System should support easy undo. | HIGH | UX | VIBE_CODER |
| ISSUE-031 | System should handle multiline paste. | MEDIUM | UX | VIBE_CODER |
| ISSUE-032 | System should handle StackOverflow-style paste. | LOW | UX | VIBE_CODER |
| ISSUE-033 | System should extract code from markdown. | MEDIUM | UX | VIBE_CODER |
| ISSUE-034 | Long operations should show progress. | MEDIUM | UX | VIBE_CODER |
| ISSUE-035 | Complex operations should explain steps. | LOW | UX | VIBE_CODER |
| ISSUE-036 | Success should be clearly communicated. | LOW | UX | VIBE_CODER |
| ISSUE-037 | Semicolon command chaining should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-038 | Backtick command substitution should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-039 | $() command substitution should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-040 | Newline injection should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-041 | ../../../ path traversal should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-042 | Null byte injection should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-043 | Symlink attacks should be prevented. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-044 | Infinite loop in generated code should be caught. | HIGH | SECURITY | SCRIPT_KID |
| ISSUE-045 | Memory exhaustion should be prevented. | HIGH | SECURITY | SCRIPT_KID |
| ISSUE-046 | Fork bomb should be detected and blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-047 | Disk filling attacks should be limited. | MEDIUM | SECURITY | SCRIPT_KID |
| ISSUE-048 | sudo commands should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-049 | setuid manipulation should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-050 | Dangerous env variables should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-051 | Data exfiltration via curl should be blocked. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-052 | DNS exfiltration should be considered. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-053 | User can't override system prompt. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-054 | Indirect prompt injection via files. | HIGH | SECURITY | SCRIPT_KID |
| ISSUE-055 | Python code shouldn't escape sandbox. | CRITICAL | UNKNOWN | SCRIPT_KID |
| ISSUE-056 | File descriptors shouldn't leak info. | MEDIUM | UNKNOWN | SCRIPT_KID |
| ISSUE-057 | Concurrent file reads should be safe. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-058 | Concurrent writes to same file should be serialize... | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-059 | Multiple agent executions should not interfere. | MEDIUM | INTEGRATION | STRESS_TEST |
| ISSUE-060 | Writing very large file content should work. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-061 | Very long command should be handled. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-062 | Directory with many files should work. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-063 | Unicode filenames should work. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-064 | Unicode content should be preserved. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-065 | Special characters in path should be escaped. | MEDIUM | UNKNOWN | STRESS_TEST |
| ISSUE-066 | Partial failures should leave clean state. | HIGH | LOGIC | STRESS_TEST |
| ISSUE-067 | Network timeouts should retry gracefully. | MEDIUM | LOGIC | STRESS_TEST |
| ISSUE-068 | Disk full should be handled gracefully. | HIGH | LOGIC | STRESS_TEST |
| ISSUE-069 | API rate limits should be handled. | MEDIUM | LOGIC | STRESS_TEST |
| ISSUE-070 | Rapid tool calls should be throttled. | LOW | PERFORMANCE | STRESS_TEST |
| ISSUE-071 | Planner output should be executable by Executor. | HIGH | INTEGRATION | INTEGRATION |
| ISSUE-072 | Explorer findings should propagate to other agents... | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-073 | Reviewer feedback should trigger corrections. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-074 | Architect phase should exist and work. | MEDIUM | UNKNOWN | INTEGRATION |
| ISSUE-075 | DevSquad should enforce phase ordering. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-076 | Failed phases should allow rollback. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-077 | System should create working Flask app. | HIGH | UNKNOWN | INTEGRATION |
| ISSUE-078 | System should create working CLI tool. | HIGH | INTEGRATION | INTEGRATION |
| ISSUE-079 | System should create working data processor. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-080 | Governance should block dangerous operations. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-081 | Sofia counsel should be available. | LOW | UNKNOWN | INTEGRATION |
| ISSUE-082 | All governance decisions should be logged. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-083 | Read → Modify → Write should be atomic. | MEDIUM | UNKNOWN | INTEGRATION |
| ISSUE-084 | Search → Edit chain should preserve context. | MEDIUM | UNKNOWN | INTEGRATION |
| ISSUE-085 | Git workflow should be chainable. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-086 | Session context should persist across commands. | HIGH | INTEGRATION | INTEGRATION |
| ISSUE-087 | Session should recover from crash. | MEDIUM | INTEGRATION | INTEGRATION |
| ISSUE-088 | Command history should persist. | LOW | UX | INTEGRATION |


---

## Recommendations

### Immediate Actions (CRITICAL)
1. Fix all CRITICAL security issues before any release
2. Address path traversal and command injection vulnerabilities
3. Implement proper input validation

### Short-term (HIGH)
1. Add atomic file operations to prevent corruption
2. Implement proper error messages for beginners
3. Add undo/rollback functionality

### Medium-term (MEDIUM)
1. Add typo correction and fuzzy matching
2. Implement progress indicators for long operations
3. Add session persistence and crash recovery

### Nice-to-have (LOW)
1. Add frustration detection
2. Implement learning/verbose mode
3. Add multilingual support

---

## Test Output

```
No stdout
```

### Errors (if any)

```
No stderr
```

---

*Report generated by BRUTAL E2E Test Suite v1.0*
