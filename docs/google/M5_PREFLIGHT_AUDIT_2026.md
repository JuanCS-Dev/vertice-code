# Pre-Flight Audit & Failure Analysis Report (M5 Cutover)
**Date:** 2026-01-26
**Auditor:** Vertice-MAXIMUS
**Context:** Phase M5 Deployment (Cloud Run Frontend)

## 1. Executive Summary
The M5 deployment attempts have failed due to **structural immaturity** in the `apps/web-console` artifact. While the code follows the Constitution (clean, typed), the *project structure* lacks standard Next.js artifacts required for a production container build. We are attempting to deploy a "skeleton" that is missing its bones.

## 2. Failure Analysis (Root Cause)

### Failure A: Dependency Drift (`npm ci` exit code 1)
*   **Symptom:** Cloud Build failed at `RUN npm ci`.
*   **Root Cause:** `package.json` requested `next: 16.0.0` but `package-lock.json` pinned `15.5.9`.
*   **Diagnosis:** The migration to Next.js 16 was partial. The lockfile was not updated.
*   **Status:** ✅ **FIXED** (Local `npm install` + Commit).

### Failure B: Dynamic Rendering Violation
*   **Symptom:** `Next.js build worker exited with code: 1`.
*   **Root Cause:** The `/dashboard` route uses cookies (headers), forcing it to be dynamic, but it was being rendered statically by default.
*   **Diagnosis:** Next.js 15/16 App Router is strict about static vs dynamic.
*   **Status:** ✅ **FIXED** (Added `export const dynamic = 'force-dynamic'` to `dashboard/page.tsx`).

### Failure C: Missing Static Assets (`COPY failed`)
*   **Symptom:** `COPY --from=builder /app/public ./public` failed.
*   **Root Cause:** The `apps/web-console` directory **did not contain a `public` folder**.
*   **Context:** The Dockerfile assumes a standard Next.js layout where `public/` contains assets (favicon, robots.txt).
*   **Diagnosis:** The `apps/web-console` was likely scaffolded programmatically without the standard asset directory.
*   **Status:** ⚠️ **PARTIALLY FIXED** (Created `public/.gitkeep` but deployment aborted).

## 3. Codebase Validation (Pre-Deploy Audit)

I have audited `apps/web-console` against the **Launch Roadmap** and **Code Constitution**:

| Requirement | Status | Findings |
|---|---|---|
| **Structure** | ⚠️ **Incomplete** | Missing `public/` assets (favicon, manifest). Missing `robots.txt`. |
| **Config** | ✅ **Valid** | `next.config.js` has `output: 'standalone'` (Correct for Cloud Run). |
| **Security** | ✅ **Valid** | `middleware.ts` implements CSRF protection. Headers are set. |
| **Deps** | ✅ **Synced** | Lockfile now matches `package.json`. |
| **Env** | ⚠️ **Risky** | Local build succeeded, but Cloud Build environment variables must be verified. |

## 4. Remediation Plan (The "Correct" Way)

We must complete the "skeleton" before trying to animate it.

1.  **Restore Standard Artifacts:** Create a proper `public` folder with a placeholder `favicon.ico` to satisfy the Dockerfile and browser expectations.
2.  **Local Build Verification:** Execute `npm run build` locally in `apps/web-console` to prove the build logic *before* sending it to Google Cloud.
3.  **Deploy:** Execute `tools/deploy_m5_robust.py` only after local verification passes.

## 5. Required Actions
I request permission to execute the following **Atomic Fix**:
1.  Create `apps/web-console/public/favicon.ico` (Placeholder).
2.  Run `npm run build` locally to verify.
3.  Commit the fix.
4.  Retrigger the deployment.
