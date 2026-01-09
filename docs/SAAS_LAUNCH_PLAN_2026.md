# 🚀 VERTICE-CODE: SAAS LAUNCH PLAN 2026
**Status:** READY FOR DEPLOY
**Target:** Google Cloud Platform (Sovereign Stack)
**Domain:** vertice-maximus.com (Migration Pending)

---

## 1. THE VISION: DIVINE SOVEREIGNTY
**"Unleash the Architect"**

We are not building a tool. We are building a temple for creation.
- **Sovereign Code:** No external dependencies, no "wrappers". Direct intelligence.
- **Divine Inspiration:** The bridge between human intent and machine precision.
- **Zero Latency:** Edge-ready, generative UI, immediate manifestation.

---

## 2. INFRASTRUCTURE ARCHITECTURE (GOOGLE STACK PURE)

We have successfully migrated from a hybrid mess to a unified, sovereign stack on GCP project `vertice-ai`.

### 🟢 Frontend (The Face)
- **Technology:** Next.js 15 (App Router) + Tailwind v4 (Cyberpunk Theme).
- **Hosting:** Firebase Hosting (Web Frameworks).
- **Auth:** Firebase Authentication (No more Clerk).
- **Streaming:** Vercel AI SDK Core (Data Stream Protocol).
- **Artifacts:** Sandpack + Monaco Editor (Browser-based execution).

### 🔵 Backend (The Brain)
- **Technology:** FastAPI (Python 3.11).
- **Hosting:** Google Cloud Run (Serverless, Auto-scale to zero).
- **Intelligence:** Vertex AI (Gemini 2.5 Pro / Claude 4.5 Opus*).
- **Deep Sync:** GitHub App Webhooks integration.

*\*Quota unlock pending for Claude 4.5 Opus.*

---

## 3. DEPLOYMENT PROTOCOL (ZERO DOWNTIME)

### A. Pre-Flight Check
1.  **GCloud Auth:** Ensure you are logged in as `juancs.d3v@gmail.com`.
    ```bash
    gcloud auth login
    gcloud config set project vertice-ai
    ```
2.  **Clean State:**
    ```bash
    rm -rf vertice-chat-webapp/frontend/.next
    rm -rf vertice-chat-webapp/frontend/node_modules
    ```

### B. Execution (The "One-Click" Script)
We have prepared a hardened script that handles everything.

```bash
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

**What it does:**
1.  Verifies Project ID (`vertice-ai`).
2.  Enables necessary APIs (Cloud Run, Artifact Registry, etc.).
3.  Builds & Deploys Backend container to Cloud Run.
4.  Updates Frontend `.env.production` with the new Backend URL.
5.  Builds & Deploys Frontend to Firebase Hosting.

### C. DNS Migration (The Switch)
*After successful deploy to `vertice-ai.web.app`*:

1.  Go to [Firebase Console > Hosting](https://console.firebase.google.com/project/vertice-ai/hosting).
2.  Click **"Add Custom Domain"**.
3.  Enter `vertice-maximus.com`.
4.  Copy the `TXT` records to your Cloudflare DNS.
5.  Wait for verification, then update `A` records.

---

## 4. MARKETING & GROWTH STRATEGY (2026)

### The Narrative
Stop selling "AI". Sell **Power**.
- **Don't say:** "We use Gemini 3."
- **Say:** "Your code, amplified by the most advanced reasoning engine in existence."

### The "Sect" Growth
1.  **Artifacts Demos:** Share videos of the TUI creating complex React components in seconds.
2.  **Manifesto:** Publish `CODE_CONSTITUTION.md` as a public philosophy.
3.  **High-Technical Content:** Blog posts about "Why we ditched Clerk for Firebase" or "Achieving 60fps in a TUI".

---

## 5. IMMEDIATE NEXT STEPS

1.  **Run `./deploy-gcp.sh`**.
2.  **Verify** the live app at the Firebase URL.
3.  **Record** the demo video for the Landing Page placeholder.
4.  **Execute** DNS migration on Cloudflare.

*Soli Deo Gloria.*
