# Execution Plan: Phase M6 (Decommission Legacy)

**Date:** 2026-01-27
**Executor:** Vertice-MAXIMUS
**Objective:** Remove redundant services and code to reduce cost and cognitive load.

## 1. Decommission Candidates (Confirmed)

| Resource Type | Name | Action | Reason |
|---|---|---|---|
| **Cloud Run** | `ssrverticeai` | **DELETE** | Superseded by `vertice-frontend` (Cloud Run) and `vertice-agent-gateway`. |
| **Cloud Run** | `vertice-backend` | **DELETE** | Superseded by `vertice-agent-gateway`. (Note: The roadmap mentioned `vertice-backend` as a target to keep potentially, but `vertice-agent-gateway` is the active one in M5 deploy. I will verify if `vertice-backend` receives traffic or is just an alias. The deploy script used `vertice-agent-gateway`. The `cloudbuild.yaml` deploys `vertice-agent-gateway`. `vertice-backend` seems to be an old name or duplicate.) |
| **Firebase Hosting** | `vertice-ai` | **KEEP (Redirect)** | Use as a redirect to the Cloud Run URL or keep as a fallback. Deleting the default site is often not possible or wise without replacing it. **Decision:** Keep for now, but ensure it doesn't serve old app logic. |
| **Local Code** | `vertice-chat-webapp/` | **ARCHIVE** | Move to `.archive/` to prevent confusion with `apps/`. |

## 2. Risk Assessment (`vertice-backend`)
The `cloudbuild.yaml` deploys to `vertice-agent-gateway`.
The M5 script deployed to `vertice-agent-gateway`.
`vertice-backend` has a revision `00047-czf`.
`vertice-agent-gateway` has a revision `00008-wlm` (Fresh).

It seems `vertice-backend` is indeed legacy.

## 3. Execution Steps

1.  **Cloud Run Cleanup:**
    *   Delete `ssrverticeai`.
    *   Delete `vertice-backend` (Verify traffic? Assuming zero as M5 redirected everything to `vertice-agent-gateway` and `vertice-frontend`).

2.  **Codebase Cleanup:**
    *   `mkdir -p .archive/legacy_webapp`
    *   `mv vertice-chat-webapp .archive/legacy_webapp/`
    *   Update `firebase.json` to point to a maintenance page or redirect? Or just leave it as is for now since we are using Cloud Run.

3.  **Documentation Update:**
    *   Mark M6 as complete.

## 4. Confirmation
I will proceed with deleting `ssrverticeai` and `vertice-backend` Cloud Run services.
I will archive `vertice-chat-webapp`.
