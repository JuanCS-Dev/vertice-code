# 📦 Legacy Agents - Deprecated Code

**Status:** ARCHIVED
**Date:** 23/Nov/2025
**Reason:** Replaced by Enterprise versions

---

## ⚠️ DO NOT USE THESE FILES

These agents have been replaced by superior Enterprise/NextGen versions.

---

## 📁 Archived Files

### 1. **executor.py** (SimpleExecutorAgent)
**Replaced by:** `executor.py` (NextGenExecutorAgent)

**Why deprecated:**
- ❌ Simple, basic implementation
- ❌ No MCP Code Execution Pattern
- ❌ No advanced security features
- ❌ No streaming support

**New version features:**
- ✅ 98.7% token reduction (MCP Pattern)
- ✅ Multi-layer sandboxing (Docker + E2B)
- ✅ OWASP-compliant security
- ✅ ReAct pattern with auto-correction
- ✅ Streaming @ 30 FPS

---

### 2. **refactorer_backup_v6.py** (RefactorerAgent v6)
**Replaced by:** `refactorer.py` (RefactorerAgent v8.0)

**Why deprecated:**
- ❌ Basic refactoring capabilities
- ❌ No AST-aware patching
- ❌ No transactional memory
- ❌ No rollback support

**New version features:**
- ✅ LibCST for format preservation
- ✅ Transactional memory with rollback
- ✅ Semantic validation
- ✅ RL-guided transformations
- ✅ Multi-file atomic refactoring
- ✅ Blast radius integration

---

### 3. **planner_v5.py** (PlannerAgent v5.0 - smaller version)
**Replaced by:** `planner.py` (PlannerAgent v5.0 - full version)

**Why deprecated:**
- ❌ Smaller, less feature-rich (577 LOC vs 1211 LOC)
- ❌ Used nowhere in the codebase

**Active version:**
- ✅ Full-featured (1211 LOC)
- ✅ Used in all imports
- ✅ Tested and validated

---

### 4. **planner_backup_v1.py** (PlannerAgent v1.0)
**Replaced by:** `planner.py` (PlannerAgent v5.0)

**Why deprecated:**
- ❌ Very old version (v1.0)
- ❌ Missing modern features
- ❌ Not compatible with current system

---

## 🎯 Migration Guide

If you have code importing these files:

### Before:
```python
from qwen_dev_cli.agents.executor import SimpleExecutorAgent  # OLD
from qwen_dev_cli.agents.refactorer_v8 import RefactorerAgent  # OLD
```

### After:
```python
from qwen_dev_cli.agents.executor import NextGenExecutorAgent  # NEW
from qwen_dev_cli.agents.refactorer import RefactorerAgent  # NEW (v8.0)
```

---

## 📊 Why Enterprise Versions?

| Feature | Legacy | Enterprise |
|---------|--------|------------|
| **Token Efficiency** | Standard | 98.7% reduction (MCP) |
| **Security** | Basic | OWASP-compliant, multi-layer |
| **Error Recovery** | None | ReAct pattern with retry |
| **Code Preservation** | No | LibCST format preservation |
| **Transactional** | No | Multi-level rollback |
| **Streaming** | No | 30 FPS real-time |
| **Tests** | Basic | 100+ comprehensive tests |
| **Grade** | B | A+ Elite |

---

## 🗑️ Deletion Schedule

These files will be permanently deleted after **30 days** (23/Dec/2025) if no issues arise.

If you need to reference these files for any reason, they will be available until then.

---

## 📞 Questions?

If you encounter any issues with the new versions, please:
1. Check the migration guide above
2. Review the new agent documentation
3. Report issues in GitHub

**DO NOT revert to these legacy files** - they are unmaintained and unsupported.
