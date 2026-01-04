# Jules Integration Guide

## Overview

Jules is configured as a **Senior Python Developer** that maintains the Vertice-Code codebase autonomously.

## Quick Start

```bash
# Load workflow helpers
source .jules/workflows.sh

# See available commands
jules-help
```

## Task Templates

| Command | Purpose | Example |
|---------|---------|---------|
| `jules-fix` | Bug fixes | `jules-fix 'TypeError in streaming handler'` |
| `jules-test` | Add tests | `jules-test 'vertice_cli.core.resilience'` |
| `jules-refactor` | Code cleanup | `jules-refactor 'agent error handling'` |
| `jules-docs` | Documentation | `jules-docs 'vertice_tui.widgets'` |
| `jules-deps` | Update deps | `jules-deps 'textual'` |

## Maintenance Workflows

### Daily (Automated)
```bash
jules-daily
```
- Runs `black` and `ruff --fix`
- Ensures tests pass
- Creates PR with fixes

### Weekly (Scheduled)
```bash
jules-weekly
```
- Analyzes code smells
- Checks for dead code
- Reports missing type hints

### Security Audit
```bash
jules-security
```
- Checks for hardcoded secrets
- Scans for injection vulnerabilities
- Reports dependency CVEs

## Configuration Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent instructions (read by Jules) |
| `.jules/setup.sh` | Environment setup in VM |
| `.jules/workflows.sh` | CLI helper functions |

## Best Practices

1. **Specific prompts** - "Fix TypeError in X" > "Fix bugs"
2. **One task, one session** - Atomic changes
3. **Review before merge** - Always check PR diffs
4. **Run locally first** - Use `jules-pull <id> --apply` to test

## Monitoring

```bash
# Active sessions
jules-status

# Pull and apply changes locally
jules-pull <session_id>

# Check connected repos
jules-repos
```

## API Integration (Advanced)

For programmatic access, use the Jules API:

```bash
# Get API key from jules.google → Settings
export JULES_API_KEY="your-key"

# Create session via API
curl -X POST "https://jules.googleapis.com/v1alpha/sessions" \
  -H "X-Goog-Api-Key: $JULES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fix bug in X",
    "sourceContext": {
      "source": "sources/github/JuanCS-Dev/vertice-code"
    }
  }'
```

## Troubleshooting

**Jules creates empty PRs:**
- Check if task is too vague
- Verify AGENTS.md is readable
- Check VM setup script

**Tests fail in Jules VM:**
- Add missing deps to pyproject.toml
- Update `.jules/setup.sh`

**Rate limited:**
- Free tier: 15 tasks/day, 3 concurrent
- Upgrade to Pro ($19.99) or Ultra ($124.99)

---
*Last updated: 2026-01-04*
