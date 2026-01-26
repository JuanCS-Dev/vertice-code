# Critical Failure Report: M5 Cutover Deployment (2026-01-26)

## 1. Incident Overview
**Status:** ❌ **FAILED**
**Phase:** M5 (Cutover to Canonical Frontend)
**Trigger:** `tools/deploy_m5_robust.py` (Cloud Build submission)
**Build ID:** `7eb8ad69-a068-4a4d-a81c-817a1ab1e46d`

## 2. Root Cause Analysis
The deployment failed during **Step 2 (Build Frontend)** inside Cloud Build.

**Error Message:**
```text
npm error `npm ci` can only install packages when your package.json and package-lock.json or npm-shrinkwrap.json are in sync.
npm error Invalid: lock file's next@15.5.9 does not satisfy next@16.0.0
...
npm error The command '/bin/sh -c npm ci' returned a non-zero code: 1
```

**Explanation:**
1.  **Dependency Conflict:** The `package.json` in `apps/web-console` declares `next: "16.0.0"`.
2.  **Stale Lockfile:** The `package-lock.json` in `apps/web-console` is locked to `next@15.5.9`.
3.  **Strict Mode Failure:** The `Dockerfile` uses `npm ci` (Clean Install), which *intentionally fails* if the lockfile does not match `package.json` exactly. This is a safety feature for CI/CD, and it worked as intended by blocking a broken dependency state.

## 3. Context & Impact
- **Backend:** Successfully built (`ea059754f70d`) and pushed.
- **Frontend:** Failed to build.
- **Impact:** The M5 deployment was aborted. No bad code was deployed to Cloud Run (atomic failure at build time). Production is safe but the update is stalled.

## 4. Remediation Plan (Recommended)
The following actions are required to fix the repository state before retrying:

1.  **Local Fix:**
    - Run `cd apps/web-console`
    - Run `npm install` (to update `package-lock.json` to match `next: 16.0.0`)
    - Commit the updated `package-lock.json`.

2.  **Retry Deployment:**
    - Run `python3 tools/deploy_m5_robust.py` again.

## 5. Artifacts
- **Logs:** Captured in `build_submit.log` (stdout) and this report.
- **Script:** `tools/deploy_m5_robust.py` (Working correctly, logic is sound).

**Auditor:** Vertice-MAXIMUS
**Date:** 2026-01-26
