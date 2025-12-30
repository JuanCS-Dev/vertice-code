---
name: code-generation
description: Generate high-quality, production-ready code following best practices
version: 1.0.0
author: Vertice Agency
tools:
  - filesystem
  - shell
  - git
---

# Code Generation Skill

## Overview
This skill enables agents to generate production-ready code following industry best practices, design patterns, and the project's coding standards.

## Instructions

### Before Generating Code
1. Analyze the project structure using `scripts/analyze_project.py`
2. Load relevant context from `references/`
3. Check existing patterns in the codebase

### Code Quality Standards
- Follow language-specific style guides
- Include type hints (Python) or TypeScript types
- Write self-documenting code with clear names
- Keep functions under 50 lines
- Single responsibility principle

### Generated Code Must Include
- Proper error handling
- Input validation at boundaries
- Logging for debugging
- Unit test stubs when appropriate

### Anti-Patterns to Avoid
- God classes/functions
- Deep nesting (max 3 levels)
- Magic numbers/strings
- Commented-out code
- Print debugging

## Scripts

### analyze_project.py
Analyzes project structure and returns coding conventions.

### generate_tests.py
Generates test stubs for new code.

## References
- `references/style_guides/` - Language-specific guides
- `references/patterns/` - Common design patterns
- `references/examples/` - Code examples

## Examples

### Generate a Python function
```
Generate a function that validates email addresses using regex.
Include type hints, docstring, and error handling.
```

### Generate a TypeScript class
```
Create a UserService class with CRUD operations.
Use dependency injection and proper typing.
```
