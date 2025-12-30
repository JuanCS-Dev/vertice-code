---
name: code-review
description: Comprehensive code review with security, performance, and quality analysis
version: 1.0.0
author: Vertice Agency
tools:
  - filesystem
  - grep
  - shell
---

# Code Review Skill

## Overview
Perform thorough code reviews covering security vulnerabilities, performance issues, code quality, and adherence to best practices.

## Instructions

### Review Process
1. **Security Scan**: Check OWASP Top 10 vulnerabilities
2. **Performance**: Identify bottlenecks and inefficiencies
3. **Quality**: Assess readability, maintainability, testability
4. **Standards**: Verify coding standards compliance
5. **Logic**: Validate business logic correctness

### Security Checklist
- [ ] Input validation and sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Authentication/authorization checks
- [ ] Secrets not hardcoded
- [ ] Secure dependencies (no known CVEs)

### Performance Checklist
- [ ] No N+1 queries
- [ ] Appropriate data structures
- [ ] Caching opportunities
- [ ] Lazy loading where appropriate
- [ ] No memory leaks

### Output Format
```markdown
## Code Review: [file/PR name]

### Summary
[1-2 sentence overview]

### Critical Issues
- [Security/Breaking issues that MUST be fixed]

### Suggestions
- [Improvements that SHOULD be considered]

### Positive Notes
- [What's done well]

### Verdict: [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]
```

## Scripts

### security_scan.py
Runs automated security checks.

### complexity_analysis.py
Calculates cyclomatic complexity.

## References
- `references/owasp_top_10.md`
- `references/performance_patterns.md`
