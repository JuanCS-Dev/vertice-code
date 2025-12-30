---
name: git-ops
description: Git operations including commits, branches, PRs, and conflict resolution
version: 1.0.0
author: Vertice Agency
tools:
  - git
  - shell
---

# Git Operations Skill

## Overview
Handle all Git-related operations following conventional commits and GitFlow/GitHub Flow patterns.

## Instructions

### Commit Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Branch Naming
- `feature/<ticket>-<description>`
- `fix/<ticket>-<description>`
- `hotfix/<description>`
- `release/<version>`

### PR Creation
1. Create descriptive title
2. Fill PR template
3. Link related issues
4. Add appropriate labels
5. Request reviewers

### Conflict Resolution
1. Fetch latest changes
2. Identify conflict sources
3. Resolve preserving both intents
4. Test after resolution
5. Commit with clear message

## Scripts

### smart_commit.sh
Generates commit message from diff analysis.

### pr_template.md
Standard PR template.

## Examples

### Create feature branch and commit
```bash
git checkout -b feature/AUTH-123-user-login
# ... make changes ...
git add .
git commit -m "feat(auth): implement user login with JWT"
```
