#!/bin/bash
# Jules Workflows for Vertice-Code
# Usage: source .jules/workflows.sh

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# TASK TEMPLATES
# =============================================================================

# Quick bug fix
jules-fix() {
    local description="$1"
    if [ -z "$description" ]; then
        echo -e "${YELLOW}Usage: jules-fix 'description of the bug'${NC}"
        return 1
    fi
    echo -e "${BLUE}Creating Jules task: fix${NC}"
    jules new --repo JuanCS-Dev/vertice-code "fix: $description. Run black and ruff before PR. Add regression test if applicable."
}

# Add tests
jules-test() {
    local target="$1"
    if [ -z "$target" ]; then
        echo -e "${YELLOW}Usage: jules-test 'module or function to test'${NC}"
        return 1
    fi
    echo -e "${BLUE}Creating Jules task: test${NC}"
    jules new --repo JuanCS-Dev/vertice-code "test: Add comprehensive tests for $target. Follow pytest patterns in tests/unit/. Use mocks for external calls. Target 80%+ coverage."
}

# Refactor code
jules-refactor() {
    local area="$1"
    if [ -z "$area" ]; then
        echo -e "${YELLOW}Usage: jules-refactor 'area to refactor'${NC}"
        return 1
    fi
    echo -e "${BLUE}Creating Jules task: refactor${NC}"
    jules new --repo JuanCS-Dev/vertice-code "refactor: Improve $area. Keep behavior identical. Update all imports. Run full test suite before PR."
}

# Documentation
jules-docs() {
    local target="$1"
    if [ -z "$target" ]; then
        echo -e "${YELLOW}Usage: jules-docs 'module to document'${NC}"
        return 1
    fi
    echo -e "${BLUE}Creating Jules task: docs${NC}"
    jules new --repo JuanCS-Dev/vertice-code "docs: Add docstrings and type hints to $target. Follow Google docstring style. Update any related README sections."
}

# Dependency update
jules-deps() {
    local package="$1"
    if [ -z "$package" ]; then
        echo -e "${YELLOW}Usage: jules-deps 'package to update'${NC}"
        return 1
    fi
    echo -e "${BLUE}Creating Jules task: deps${NC}"
    jules new --repo JuanCS-Dev/vertice-code "deps: Update $package to latest version in pyproject.toml. Test compatibility. Document any breaking changes."
}

# =============================================================================
# MAINTENANCE WORKFLOWS
# =============================================================================

# Daily maintenance check
jules-daily() {
    echo -e "${GREEN}=== Jules Daily Maintenance ===${NC}"
    jules new --repo JuanCS-Dev/vertice-code "maintenance: Run ruff check and fix any auto-fixable issues. Run black formatting. Ensure tests pass. Create PR with fixes if any."
}

# Weekly code review
jules-weekly() {
    echo -e "${GREEN}=== Jules Weekly Review ===${NC}"
    jules new --repo JuanCS-Dev/vertice-code "review: Analyze codebase for code smells, unused imports, dead code. Check for missing type hints in public APIs. Report findings but don't auto-fix complex issues."
}

# Security audit
jules-security() {
    echo -e "${GREEN}=== Jules Security Audit ===${NC}"
    jules new --repo JuanCS-Dev/vertice-code "security: Audit for hardcoded secrets, SQL injection, command injection, SSRF vulnerabilities. Check dependency versions for known CVEs. Report findings."
}

# =============================================================================
# BATCH OPERATIONS
# =============================================================================

# Process TODO.md tasks
jules-batch-todo() {
    if [ ! -f "TODO.md" ]; then
        echo -e "${YELLOW}TODO.md not found${NC}"
        return 1
    fi
    echo -e "${GREEN}Processing TODO.md with Jules...${NC}"
    grep -E "^\s*-\s*\[.\]" TODO.md | sed 's/^[^]]*\] //' | while IFS= read -r task; do
        echo -e "${BLUE}Assigning: $task${NC}"
        jules new --repo JuanCS-Dev/vertice-code "$task"
        sleep 2  # Rate limiting
    done
}

# Parallel test coverage
jules-coverage() {
    echo -e "${GREEN}=== Jules Parallel Coverage ===${NC}"
    jules new --parallel 3 --repo JuanCS-Dev/vertice-code "test: Improve test coverage. Find untested functions in vertice_cli/, vertice_tui/, vertice_core/. Add missing unit tests. Target 80%+ coverage."
}

# =============================================================================
# MONITORING
# =============================================================================

# List active sessions
jules-status() {
    echo -e "${GREEN}=== Active Jules Sessions ===${NC}"
    jules remote list --session
}

# List repos
jules-repos() {
    echo -e "${GREEN}=== Connected Repos ===${NC}"
    jules remote list --repo
}

# Pull latest result
jules-pull() {
    local session_id="$1"
    if [ -z "$session_id" ]; then
        echo -e "${YELLOW}Usage: jules-pull <session_id>${NC}"
        echo "Get session IDs with: jules-status"
        return 1
    fi
    jules remote pull --session "$session_id" --apply
}

# =============================================================================
# HELP
# =============================================================================

jules-help() {
    echo -e "${GREEN}=== Jules Workflows for Vertice-Code ===${NC}"
    echo ""
    echo -e "${BLUE}Task Templates:${NC}"
    echo "  jules-fix 'description'     - Create bug fix task"
    echo "  jules-test 'target'         - Create test task"
    echo "  jules-refactor 'area'       - Create refactor task"
    echo "  jules-docs 'module'         - Create documentation task"
    echo "  jules-deps 'package'        - Create dependency update task"
    echo ""
    echo -e "${BLUE}Maintenance:${NC}"
    echo "  jules-daily                 - Run daily maintenance"
    echo "  jules-weekly                - Run weekly code review"
    echo "  jules-security              - Run security audit"
    echo ""
    echo -e "${BLUE}Batch Operations:${NC}"
    echo "  jules-batch-todo            - Process TODO.md tasks"
    echo "  jules-coverage              - Parallel coverage improvement"
    echo ""
    echo -e "${BLUE}Monitoring:${NC}"
    echo "  jules-status                - List active sessions"
    echo "  jules-repos                 - List connected repos"
    echo "  jules-pull <id>             - Pull and apply session result"
}

echo -e "${GREEN}Jules workflows loaded! Run 'jules-help' for commands.${NC}"
